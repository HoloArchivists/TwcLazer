import base64
import re


def decode_string(text):
    """
    Base64 decode with case swap for extra obfuscation
    """
    text = text + '=' * (len(text) % 4)
    return base64.b64decode(bytes(text, 'ascii').swapcase()).decode('ascii')

def get_encoded_array(js):
    # array of encoded strings with function names and constants, used
    # in various places of the script. One of them is the salt.
    # Surprizingly, "const e" doesn't change over the versions of the script
    re_constants = "(?:var|let) e=\[((\"[a-zA-Z0-9]+\",)+\"[a-zA-Z0-9]+\")\]"
    match = re.search(re_constants, js)
    return [x.strip('"') for x in match.groups()[0].split(',')]

def get_base_offset(js):
    # strings on the array are accessed through specifying its index,
    # and function wrapping the array substracts constant value from
    # index it receives, which is different every script version
    re_offset = "(?:var|let) [a-z]=[a-z]\(\);return\([a-z]=function\([a-z],[a-z]\){(?:var|let) [a-z]=[a-z]\[[a-z]-=(\d+)\];"
    offset = re.findall(re_offset, js)[0]
    return int(offset)

def get_shift_offsets(js):
    # picking up indexes from the
    # "... parseInt(n(429)) / 1 + parseInt(n(448)) / 2 * ( - parseInt(n(428)) / 3) ..."
    re_offsets_line = 'if\(\d+==(.+)break;[a-z].push\([a-z].shift\(\)\)}'
    offsets_line = re.search(re_offsets_line, js).groups()[0]
    re_offsets = 'parseInt\([a-z]\((\d+)\)\)'
    offsets = re.findall(re_offsets, offsets_line)
    return [int(offset) for offset in offsets]

def starts_with_number(text):
    # cutting corners with parseInt() implementation: the way it works
    # it will throw away any non-numeric characters at the end of the string,
    # and for this case only the fact that it returns a number matters, not the number itself
    return re.match('\d+', text) is not None

def decode_array(js):
    # the array of encoded strings is also additionally rotated (circularly shifted), so order of
    # strings in runtime differs from that in code. The rule to determine correct
    # number of rotation steps is to try every possible position and pick the one,
    # where all (decoded) strings in array that are located at offsets used in the
    # "... parseInt(n(429)) / 1 + parseInt(n(448)) / 2 * ( - parseInt(n(428)) / 3) ..."
    # expression are successfully parseInt'ed as a number
    candidates = []
    base_offset = get_base_offset(js)
    test_points_offsets = [offset - base_offset for offset in get_shift_offsets(js)]
    array = [decode_string(x) for x in get_encoded_array(js)]
    for _ in range(len(array)):
        strings_on_offsets = [array[i] for i in test_points_offsets]
        if all([starts_with_number(line) for line in strings_on_offsets]):
            candidates.append(array.copy())
        array.append(array.pop(0))
    if len(candidates) == 0:
        raise Exception('Salt extraction failed: none of possible array positions matched')
    elif len(candidates) == 1:
        return candidates[0]
    else:
        print(f'Salt extraction: found {len(candidates)} possible offsets, using first one')
        return candidates[0]

def get_salt_offset(js):
    # extracting array offset for salt value from the place in code that makes use of it.
    # Since array can be decoded and rotated to right position, all that is left is to
    # get the salt value out of it by its offset
    re_salt_offsets = [
        r'null!=\([a-z]=[a-z]\.salt\)\?[a-z]:[a-z]\((\d+)\),[a-z]\)',
        r'null!=\([a-z]=[a-z]\[[a-z]\(\d+\)\]\)\?[a-z]:[a-z]\((\d+)\),[a-z]\),',
        # same shapes with variable/function names of any length
        r'null!=\([\w$]+=[\w$]+\.salt\)\?[\w$]+:[\w$]+\((\d+)\)',
        r'null!=\([\w$]+=[\w$]+\[[\w$]+\(\d+\)\]\)\?[\w$]+:[\w$]+\((\d+)\)',
    ]
    for re_salt_offset in re_salt_offsets:
        results = re.findall(re_salt_offset, js)
        try:
            return int(results[0])
        except (IndexError, ValueError):
            continue
    raise Exception('none of the salt offset patterns matched')


def js_parse_int(text):
    # JS parseInt() for the cases that matter here: leading number or NaN
    m = re.match(r'\s*[+-]?\d+', text)
    return float(int(m.group(0))) if m else float('nan')


def _check_from_parts(expr, target):
    indexes = [int(x) for x in re.findall(r'parseInt\([\w$]+\((\d+)\)\)', expr)]
    if not indexes:
        return None
    py_expr = re.sub(r'parseInt\([\w$]+\((\d+)\)\)', r'P(\1)', expr)
    # only arithmetic on P(...) calls may reach eval()
    if not re.fullmatch(r'[P0-9()+\-*/. ]+', py_expr):
        return None
    return py_expr, float(target), indexes


def get_rotation_check(js):
    """
    The script rotates the string array until a checksum expression equals a constant:

        for(var t=e();;)try{if(parseInt(n(214))/1+-parseInt(n(190))/2+...===597197)break;
                            t.push(t.shift())}catch(e){t.push(t.shift())}

    Older versions wrote the constant first: if(597197==expr)break;
    Returns (python_expression, target, [indexes passed to n()]).
    """
    patterns = [
        (r'if\((.+?)===?(-?\d+)\)break;[a-zA-Z_$][\w$]*\.push\([a-zA-Z_$][\w$]*\.shift\(\)\)', False),
        (r'if\((-?\d+)===?(.+?)\)break;[a-zA-Z_$][\w$]*\.push\([a-zA-Z_$][\w$]*\.shift\(\)\)', True),
    ]
    for pattern, constant_first in patterns:
        for m in re.finditer(pattern, js):
            expr, target = (m.group(2), m.group(1)) if constant_first else (m.group(1), m.group(2))
            result = _check_from_parts(expr, target)
            if result:
                return result
    # looser: any  if(<expression with parseInt(x(NNN)) calls> ==(=) NUMBER) break  ,
    # whatever the rotate statement around it looks like
    loose = r'if\(([^;{}]*?parseInt\([\w$]+\(\d+\)\)[^;{}]*?)\)\s*\{?\s*break'
    for m in re.finditer(loose, js):
        body = m.group(1).strip()
        a = re.fullmatch(r'(.+?)\s*===?\s*(-?\d+)', body, re.S)
        b = re.fullmatch(r'(-?\d+)\s*===?\s*(.+)', body, re.S)
        for expr, target in ([(a.group(1), a.group(2))] if a else []) + ([(b.group(2), b.group(1))] if b else []):
            result = _check_from_parts(expr, target)
            if result:
                return result
    raise Exception('rotation check expression not found')


def decode_array_by_checksum(js, extra_indexes=()):
    """
    Finds the (index offset, rotation) pair for which the script's own checksum holds,
    without needing the code of the wrapper function that applies the offset.
    Returns a list of (base_offset, decoded_array_in_runtime_order) matches. Offset and
    rotation are interchangeable (both shift the lookup), so many matches are normal.
    """
    py_expr, target, indexes = get_rotation_check(js)
    array = [decode_string(x) for x in get_encoded_array(js)]
    size = len(array)
    needed = list(indexes) + list(extra_indexes)
    base_low = max(needed) - (size - 1)   # smallest offset keeping every index inside the array
    base_high = min(needed)               # largest offset keeping every index inside the array
    matches = []
    for base in range(base_low, base_high + 1):
        rotated = array.copy()
        for rotation in range(size):
            def P(idx, rotated=rotated, base=base):
                return js_parse_int(rotated[idx - base])
            try:
                value = eval(py_expr, {'__builtins__': {}}, {'P': P})
            except Exception:
                value = float('nan')
            if value == target:
                matches.append((base, rotated.copy()))
            rotated.append(rotated.pop(0))
    if not matches:
        raise Exception('checksum not satisfied for any offset/rotation')
    return matches


def dump_debug(js, reason):
    """Save the script TwcLazer received and print the parts needed to adapt the patterns."""
    print('----- SALT DEBUG (please paste everything from here to the end marker) -----')
    print(f'reason: {reason}')
    print(f'script length: {len(js)}; starts with: {js[:120]!r}')
    try:
        with open('PlayerPage2_failed.js', 'w', encoding='utf-8') as f:
            f.write(js)
        print('full script saved as PlayerPage2_failed.js (in the folder you ran TwcLazer from)')
    except Exception as e:
        print(f'could not save script: {e}')
    shown = 0
    for m in re.finditer(r'shift', js):
        print(f'... around "shift" at {m.start()}: {js[max(0, m.start() - 650): m.end() + 120]!r}')
        shown += 1
        if shown >= 2:
            break
    m = re.search(r'parseInt\([\w$]+\(\d+\)\)', js)
    if m:
        print(f'... around first parseInt(x(N)): {js[max(0, m.start() - 150): m.end() + 450]!r}')
    for m in list(re.finditer(r'salt', js, re.I))[:3]:
        print(f'... around "salt": {js[max(0, m.start() - 100): m.end() + 100]!r}')
    print('----- END SALT DEBUG -----')


def get_salt(js):
    try:
        salt_index = get_salt_offset(js)
    except Exception as e:
        dump_debug(js, f'salt offset: {e}')
        raise
    try:
        matches = decode_array_by_checksum(js, extra_indexes=[salt_index])
        salts = []
        for base, strings in matches:
            salt = strings[salt_index - base]
            if salt not in salts:
                salts.append(salt)
        if len(salts) > 1:
            print(f'Salt extraction: checksum matched {len(salts)} different salt candidates, using first one: {salts}')
        return salts[0]
    except Exception as e:
        print(f'Checksum-based salt extraction failed ({e}), trying pattern-based extraction')
    try:
        salt_offset = salt_index - get_base_offset(js)
        strings = decode_array(js)
        return strings[salt_offset]
    except Exception as e:
        dump_debug(js, f'{type(e).__name__}: {e}')
        raise
