# Twitcasting Downloader API Functions
import hashlib
import json
import re
import time
from typing import Optional

import requests

from utils.CookiesHandler import CookiesHandler
from utils.Salt import get_salt
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

    def GetSalt(self) -> str:
        player_url = "https://twitcasting.tv/js/v1/PlayerPage2.js"
        player_page = self.session.get(player_url)
        if player_page.status_code != 200:
            print(f"Got status code {player_page.status_code} when requesting PlayerPage2")
        try:
            salt = get_salt(player_page.text)
            print(f'Current salt is {salt}')
            return salt
        except Exception as e:
            msg = "Failed to extract value used to generate authorization headers from PlayerPage. Check for updates and report this issue on GitHub along with the error message above if it happens on the most recent version"
            raise TwitcastingAPIError(msg) from e

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
            msg = f"Error parsing token for movie {movieID}: {e!r}. Raw token data: '{TokenRequest.text}'"
            raise TwitcastingAPIError(msg) from e

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

    def refetch(self):
        new_instance = TwitcastingAPI(self.userInput)
        print(f"fetched new TwitcastingAPI instance, {new_instance.CurrentStreamToken=}, {new_instance.CurrentStreamInfo=}")
        return new_instance

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
