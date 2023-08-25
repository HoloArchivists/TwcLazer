# Twitcasting Downloader API Functions
import hashlib
import json
import re
import time
from typing import Optional

import javascript
import requests

from utils.CookiesHandler import CookiesHandler
import twitcasting.TwitcastStream as TwitcastStream


class TwitcastingAPIError(Exception):
    '''Raised when TwitcastAPI failed to fetch and process all required metadata, making download impossible'''


class TwitcastingAPI:
    '''Class for the functional Twitcasting API'''

    def GetAuthSessionID(self, user_page) -> Optional[str]:
        flags = re.DOTALL | re.IGNORECASE
        re_auth_session_id = 'web-authorize-session-id&quot;:&quot;(.*?)&quot;'
        auth_session_id = re.search(re_auth_session_id, user_page.text, flags)
        if auth_session_id is None:
            print(f"Unable to extract session-id from user page {user_page.url}")
            return None
        return auth_session_id.group(1)

    
    def GenerateJsRegex(self, js: str) -> str:
        js = re.escape(js)
        js = re.sub(r"\\\[.*?\]", r"(\[.*?\])", js) # list
        js = re.sub(r"[0-9]+", r"([0-9]+)", js) # number
        js = re.sub(r"[a-zA-Z_][a-zA-Z0-9_]*", r"([a-zA-Z_][a-zA-Z0-9_]*)", js) # field
        js = re.sub(r"'.*?'|\".*?\"|`.*?`", r"('.*?'|\".*?\"|`.*?`)", js) # string
        return js
    
    def GetSalt(self):
        code = requests.get(
            f"https://twitcasting.tv/js/v1/PlayerPage2.js?{int(time.time())}"
        ).text

        crypt_func = """function t(e,i){const s=n();return t=function(n,i){let r=s[n-=269];void 0===t.MXfUDE&&(t.PoYvHX=function(e){let t="",n="";for(let n,i,s=0,r=0;i=e.charAt(r++);~i&&(n=s%4?64*n+i:i,s++%4)?t+=String.fromCharCode(255&n>>(-2*s&6)):0)i="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=".indexOf(i);for(let e=0,i=t.length;e<i;e++)n+="%"+("00"+t.charCodeAt(e).toString(16)).slice(-2);return decodeURIComponent(n)},e=arguments,t.MXfUDE=!0);const a=n+s[0],o=e[a];return o?r=o:(r=t.PoYvHX(r),e[a]=r),r},t(e,i)}function n(){const e=["x3nW","yNL0zu9MzNnLDa","x3nPEMu","mJG5nJu4vM9jBvnr","zxHWB3j0CW","x19PBxbVCNrezwzHDwX0","mtC1mdC3ou95BfLmyG","mJGWmZC1mtboBwrRDem","y2HHCKnVzgvbDa","muvHvxH5EG","qLLurvnFuevsx0vmru1ftLq","wc1xzwiTu2vZC2LVBKLK","x19LC01VzhvSzq","Dg9vChbLCKnHC2u","nZu5nJu4oxPcEenQBG","r0vu","yM9KEq","mtfds2HIu0u","x2jPBG","x3vPBNq4","DxbKyxrL","mZy4nty4ogLZA2DisW","Dg9mB3DLCKnHC2u","nJe5mZi2nKvZDgHXsG","yNvMzMvY","nuzODgHXyq","AgvHzgvYCW","BgvUz3rO","wc1xzwiTqxv0Ag9YAxPLs2v5","sgfZAa","C3rYAw5N","x3v0zJG","rgLNzxn0ig1LDgHVzcbUB3qGC3vWCg9YDgvK","C2vZC2LVBKLK","mtHrturLBhm","zgvMAw5LuhjVCgvYDhK","y29Uy2f0","z2v0vgLTzq","zgLNzxn0","mtq0mdm2ohPYwfbguW","zgvMyxvSDa","yNL0zuXLBMD0Aa","Bgj2ngPQDNqXmZjKBNj0Da","Ahr0Chm6lY9JyxmUC3q","Agv4","C2v0","x3DVCMq","Cgf0Ag5HBwu","zMXVB3i","x2HLEa","y3jLyxrLsgfZAa","C2XPy2u","Dg9tDhjPBMC","x2LUDdmY"];return(n=function(){return e})()}(function(e,n){const i=t,s=e();for(;;)try{if(563747==parseInt(i(283))/1*(-parseInt(i(277))/2)+parseInt(i(280))/3+-parseInt(i(295))/4+-parseInt(i(299))/5*(parseInt(i(297))/6)+-parseInt(i(288))/7+parseInt(i(313))/8*(parseInt(i(308))/9)+-parseInt(i(281))/10*(-parseInt(i(291))/11))break;s.push(s.shift())}catch(e){s.push(s.shift())}})(n)"""
        salt_func = """function(e,n,i){const s=t;var r=this&&this[s(279)]||function(e){return e&&e[s(286)]?e:{default:e}};Object[s(309)](n,s(286),{value:!0});var a=r(i(823));n[s(314)]=function(e,n,i,r){const o=s;var l;void 0===n&&(n={}),void 0===r&&(r=new Date);var c,u,d=(0,a.default)(function(e){const n=t;var i;return(null!==(i=e.method)&&void 0!==i?i:n(289))[n(287)]()}(n),e,i.sessionId,"string"==typeof(c=n)[o(290)]?c[o(290)]:"",null!==(l=i.salt)&&void 0!==l?l:null!==(u=o(316))?u:"",r),h=new Headers(n[o(300)]);return h[o(319)](o(285),i[o(307)]),h[o(319)](o(302),d),n[o(300)]=h,fetch(e,n)}}"""
        salt_expr = 'null!==(u=o(316))?u:""'

        # generate regex
        crypt_func = self.GenerateJsRegex(crypt_func)
        salt_func = self.GenerateJsRegex(salt_func)
        salt_expr = self.GenerateJsRegex(salt_expr)

        # find regex
        crypt_func = re.search(crypt_func, code).group(0)
        salt_func = re.search(salt_func, code).group(0)
        salt_expr = re.search(salt_expr, salt_func).group(0)

        # find number
        salt = re.search(r"[0-9]+", salt_expr).group(0)

        decrypt_code = f"""
        {crypt_func}
        result["salt"] = t({salt}, 0);
        """

        result = {}
        javascript.eval_js(decrypt_code)
        return result["salt"]

    def GenerateAuthHeaders(self, path, sessionID, method="POST") -> dict:
        if sessionID is None:
            print(f"Unable to generate authorization headers for {path}: no session id provided")
            return {}

        seed = self.GetSalt()
        timestamp = int(time.time())
        text = f"{seed}{timestamp}{method}{path}{sessionID}"
        h = hashlib.sha256()
        h.update(text.encode())
        hashed_text = h.hexdigest()
        authorizekey = f"{timestamp}.{hashed_text}"

        return {"x-web-authorizekey": authorizekey, "x-web-sessionid": sessionID}

    # Get Token
    def GetToken(self, movieID, sessionID, password=None) -> TwitcastStream.HappyToken:
        TokenURL = f"https://frontendapi.twitcasting.tv/movies/{movieID}/token"
        headers = self.GenerateAuthHeaders(f"/movies/{movieID}/token", sessionID)
        TokenData = {"password": password} if password is not None else {}
        TokenRequest = self.session.post(TokenURL, data=TokenData, headers=headers)

        if TokenRequest.status_code != 200:
            print(f"Got status code {TokenRequest.status_code} when requesting token for movie {movieID}")
        try:
            TokenRequestData = json.loads(TokenRequest.text)
            Token = TokenRequestData["token"]
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print(f"Error parsing token for movie {movieID}: {e!r}. Raw token data: '{TokenRequest.text}'")
            raise

        return TwitcastStream.HappyToken(Token)

    def GetUserPage(self, username) -> requests.Response:
        user_url = f"https://twitcasting.tv/{username}/"
        page = self.session.get(user_url)
        if page.headers.get('Set-Cookie', '').find('tc_ss=deleted') > -1:
            print("Logged out by server, session stored in cookies file is no longer valid")
        if page.status_code != 200:
            print(f"Got status code {page.status_code} when requesting {user_url}")
        return page

    def SubmitPassword(self, user_page: requests.Response, password: Optional[str] = None) -> requests.Response:
        '''Check if user_page contains password input form, submit password if required.
        If password gets accepted, request gets redirected to real user page.
        Return response (or original user_page if no password required) for further processing'''
        user_url = user_page.url

        flags = re.DOTALL | re.IGNORECASE
        re_form = '<div class="tw-empty-state-action">(.*?)</div>'
        re_session_id = 'name="cs_session_id" value="(.*?)"'
        password_form = re.search(re_form, user_page.text, flags)
        if password_form is None:
            # didn't get asked for password, stream is either unrestricted
            # or password is already present in cookies loaded from file
            return user_page
        session_id = re.search(re_session_id, password_form.group(1), flags)
        if session_id is None:
            print(f"Unable to extract session_id from secret word form at {user_url}")
            return user_page
        if password is None:
            print("Current stream appears to be password-restricted. Password can be provided with --secret argument")
            return user_page

        # In response to submitting correct password server sets cookie "wpass",
        # used then to get stream data and access websocket url
        data = {"password": password, "cs_session_id": session_id.group(1)}
        page = self.session.post(user_url, data=data)

        password_form = re.search(re_form, page.text, flags)
        if password_form is None:
            print(f"Password accepted for livestream {user_url}")
        else:
            print(f"Password {password} was not accepted for livestream {user_url}")
        return page

    def GetPasswordCookie(self, username) -> Optional[TwitcastStream.PasswordCookie]:
        '''Password cookie normally received in SubmitPassword, but can be loaded from cookies file'''
        password_value = self.session.cookies.get("wpass", path=f"/{username}")
        password_cookie = TwitcastStream.PasswordCookie(password_value) if password_value else None
        return password_cookie

    # Get Current Stream
    def GetStream(self, username) -> TwitcastStream.StreamServer:
        StreamServerURL = f"https://twitcasting.tv/streamserver.php?target={username}&mode=client"
        StreamServer_Request = self.session.get(StreamServerURL)

        if StreamServer_Request.status_code != 200:
            msg = "Failed to get streamserver links: got status {} at {}"
            msg = msg.format(StreamServer_Request.status_code, StreamServerURL)
            raise TwitcastingAPIError(msg)

        StreamServerData = json.loads(StreamServer_Request.text)

        return TwitcastStream.StreamServer(
            StreamServerData["movie"]["id"],
            StreamServerData["movie"]["live"],
            StreamServerData["hls"]["host"],
            StreamServerData["hls"]["proto"],
            StreamServerData["hls"]["source"],
            StreamServerData["fmp4"]["host"],
            StreamServerData["fmp4"]["proto"],
            StreamServerData["fmp4"]["source"],
            StreamServerData["fmp4"]["mobilesource"],
            StreamServerData["llfmp4"]["streams"]["main"],
            StreamServerData.get("llfmp4").get("streams").get("base"),
            StreamServerData.get("llfmp4").get("streams").get("mobilesource")
        )
    
    # Get Stream Info
    def GetStreamInfo(self, movieID, token) -> TwitcastStream.TwitcastStream_:
        TwitcastStreamURL = f"https://frontendapi.twitcasting.tv/movies/{movieID}/status/viewer?token={token.token}"
        TwitcastStream_Request = self.session.get(TwitcastStreamURL)

        if TwitcastStream_Request.status_code != 200:
            msg = "Failed to get stream info: got status {} at {}".format(TwitcastStream_Request.status_code, TwitcastStreamURL)
            raise TwitcastingAPIError(msg)

        TwitcastStreamData = json.loads(TwitcastStream_Request.text)

        return TwitcastStream.TwitcastStream_(
            TwitcastStreamData["update_interval_sec"],
            TwitcastStreamData.get("movie").get("id"),
            TwitcastStreamData.get("movie").get("title"),
            TwitcastStreamData.get("movie").get("telop"),
            TwitcastStreamData.get("movie").get("id"),
            TwitcastStreamData.get("movie").get("name"),
            TwitcastStreamData.get("movie").get("current"),
            TwitcastStreamData.get("movie").get("total"),
            TwitcastStreamData.get("movie").get("hashtag"), 
            TwitcastStreamData.get("movie").get("pin_message"))
        
    # Get PubSub URL
    def GetPubSubURL(self, movieID, password=None) -> TwitcastStream.EventsPubSubURL:
        PubSubURL = "https://twitcasting.tv/eventpubsuburl.php"
        PubSubData = {'movie_id': movieID}
        if password is not None:
            PubSubData["password"] = password
        PubSubRequest = self.session.post(PubSubURL, data=PubSubData)
        
        PubSubRequestData = json.loads(PubSubRequest.text)
        
        return TwitcastStream.EventsPubSubURL(PubSubRequestData["url"])
    
    @staticmethod
    def user_is_live(username, cookies=None) -> bool:
        url = f"https://twitcasting.tv/userajax.php?c=islive&u={username}"
        is_user_live = requests.get(url, cookies=cookies)
        if is_user_live.status_code != 200:
            print(f"got status {is_user_live.status_code} when checking if user {username} is live, '{is_user_live.text}'")
        if is_user_live.text == "0":
            return False
        else:
            return True

    def is_live(self):
        return self.user_is_live(self.userInput["username"], self.session.cookies)

    @property
    def cookies_header(self):
        username = self.userInput["username"]
        user_url = f"https://twitcasting.tv/{username}"
        return CookiesHandler.get_cookies_header(self.session.cookies, user_url)

    def __init__(self, UserInput) -> None:
        # Input TwitcastStream.py Userinput object
        self.userInput = UserInput
        self.session = requests.Session()
        self.session.cookies = self.userInput["cookies"] or requests.cookies.RequestsCookieJar()

        user_page = self.GetUserPage(self.userInput["username"])
        user_page = self.SubmitPassword(user_page, self.userInput["secret"])
        password = self.GetPasswordCookie(self.userInput["username"])
        sessionID = self.GetAuthSessionID(user_page)

        self.CurrentStream = self.GetStream(self.userInput["username"])
        self.CurrentStreamToken = self.GetToken(self.CurrentStream.movie_id, sessionID, password)
        self.CurrentStreamInfo = self.GetStreamInfo(self.CurrentStream.movie_id, self.CurrentStreamToken)
        self.CurrentStreamPubSubURL = self.GetPubSubURL(self.CurrentStream.movie_id, password)
