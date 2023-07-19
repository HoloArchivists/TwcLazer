from http import cookiejar

import requests

class CookiesHandler:

    @staticmethod
    def load_cookies(path):
        cookie_jar = cookiejar.MozillaCookieJar(path)
        try:
            cookie_jar.load(ignore_expires=True)
            print(f"cookies successfully loaded from {path}")
        except FileNotFoundError:
            print(f"failed to load cookies from {path}: no such file")
            return None
        except (cookiejar.LoadError, OSError) as e:
            print(f"failed to load cookies from {path}: {e}")
            return None
        requests_cookie_jar = requests.cookies.RequestsCookieJar()
        for cookie in cookie_jar:
            if cookie.expires == 0:
                cookie.expires = None
            if cookie.path != '/':
                cookie.path_specified = True
            requests_cookie_jar.set_cookie(cookie)
        return requests_cookie_jar

    @staticmethod
    def get_cookies_header(cookie_jar, url):
        # generate custom header from cookies to use with Websockets
        # connect() method, which accepts headers but not CookieJar
        r = requests.Request('GET', url)
        cookie_string = requests.cookies.get_cookie_header(cookie_jar, r)
        return {'Cookie': cookie_string}

    @staticmethod
    def to_dict(cookie_jar):
        # unlike RequestsCookieJar, FileCookieJar doesn't provide
        # dictionary-like interface for getting cookies values,
        # so this method can be used instead
        return {cookie.name: cookie.value for cookie in cookie_jar}
