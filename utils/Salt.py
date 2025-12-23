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
    re_constants = "let e=\[((\"[a-zA-Z0-9]+\",)+\"[a-zA-Z0-9]+\")\]"
    match = re.search(re_constants, js)
    return [x.strip('"') for x in match.groups()[0].split(',')]

def get_base_offset(js):
    # strings on the array are accessed through specifying its index,
    # and function wrapping the array substracts constant value from
    # index it receives, which is different every script version
    re_offset = "let [a-z]=[a-z]\(\);return\([a-z]=function\([a-z],[a-z]\){let [a-z]=[a-z]\[[a-z]-=(\d+)\];"
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
        r'null!=\([a-z]=[a-z]\[[a-z]\(\d+\)\]\)\?[a-z]:[a-z]\((\d+)\),[a-z]\),'
    ]
    for re_salt_offset in re_salt_offsets:
        results = re.findall(re_salt_offset, js)
        try:
            return int(results[0])
        except (IndexError, ValueError):
            continue
    raise Exception('none of the salt offset patterns matched')


def get_salt(js):
    salt_offset = get_salt_offset(js) - get_base_offset(js)
    strings = decode_array(js)
    salt = strings[salt_offset]
    return salt
