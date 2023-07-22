# Twitcasting Downloader API Functions
import json
import re
from typing import Optional
import requests

import twitcasting.TwitcastStream as TwitcastStream
from utils.CookiesHandler import CookiesHandler

class TwitcastingAPI:
    '''Class for the functional Twitcasting API'''

    # Get Token
    def GetToken(self, movieID, password=None) -> TwitcastStream.HappyToken:
        TokenURL = f"https://frontendapi.twitcasting.tv/movies/{movieID}/token"
        TokenData = {"password": password} if password is not None else {}
        TokenRequest = self.session.post(TokenURL, data=TokenData)

        if TokenRequest.status_code != 200:
            print(f"Got status code {TokenRequest.status_code} when requesting token for movie {movieID}")
        try:
            TokenRequestData = json.loads(TokenRequest.text)
            Token = TokenRequestData["token"]
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print(f"Error parsing token for movie {movieID}: {e!r}. Raw token data: '{TokenRequest.text}'")
            raise

        return TwitcastStream.HappyToken(Token)

    def GetPasswordCookie(self, username, password=None) -> Optional[TwitcastStream.PasswordCookie]:
        '''Check if ongoing stream is password-restricted, submit password if required'''
        user_url = f"https://twitcasting.tv/{username}/"
        page = self.session.get(user_url)
        if page.status_code != 200:
            print(f"Got status code {page.status_code} when requesting {user_url}")

        flags = re.DOTALL | re.IGNORECASE
        re_form = '<div class="tw-empty-state-action">(.*?)</div>'
        re_session_id = 'name="cs_session_id" value="(.*?)"'

        password_form = re.search(re_form, page.text, flags)
        if password_form is None:
            print("Stream is not password-restricted")
            return None
        session_id = re.search(re_session_id, password_form.group(1), flags)
        if session_id is None:
            print(f"Unable to extract session_id from secret word form at {user_url}")
            return None
        if password is None:
            print("Current stream appears to be password-restricted. Password can be provided with --secret argument")
            return None

        # In response to submitting correct password server sets cookie "wpass",
        # used then to get stream data and access websocket url
        data = {"password": password, "cs_session_id": session_id.group(1)}
        self.session.post(user_url, data=data)
        password_value = CookiesHandler.to_dict(self.session.cookies).get("wpass")
        password_cookie = TwitcastStream.PasswordCookie(password_value) if password_value else None

        if password_cookie is not None:
            print(f"Password accepted for livestream {user_url}")
        else:
            print(f"Password {password} was not accepted for livestream {user_url}")
        return password_cookie

    # Get Current Stream
    def GetStream(self, username) -> TwitcastStream.StreamServer:
        StreamServerURL = f"https://twitcasting.tv/streamserver.php?target={username}&mode=client"
        StreamServer_Request = self.session.get(StreamServerURL)
        
        if StreamServer_Request.status_code != 200:
            print("User is not live or invalid username.")
            exit()
        
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
            print("User is not live or invalid username.")
            exit()
        
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

        password = self.GetPasswordCookie(self.userInput["username"], self.userInput["secret"])
        self.CurrentStream = self.GetStream(self.userInput["username"])
        self.CurrentStreamToken = self.GetToken(self.CurrentStream.movie_id, password)
        self.CurrentStreamInfo = self.GetStreamInfo(self.CurrentStream.movie_id, self.CurrentStreamToken)
        self.CurrentStreamPubSubURL = self.GetPubSubURL(self.CurrentStream.movie_id, password)
