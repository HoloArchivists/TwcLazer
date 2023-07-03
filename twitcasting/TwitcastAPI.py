# Twitcasting Downloader API Functions
import requests
import json

import twitcasting.TwitcastStream as TwitcastStream
from utils.CookiesHandler import CookiesHandler

class TwitcastingAPI:
    '''Class for the functional Twitcasting API'''
    
    # Get Token
    def GetToken(self, movieID) -> TwitcastStream.HappyToken:
        HappyTokenURL = "https://twitcasting.tv/happytoken.php"
        HappyTokenData = {'movie_id': movieID}
        HappyTokenRequest = self.session.post(HappyTokenURL, data=HappyTokenData)
        
        HappyTokenRequestData = json.loads(HappyTokenRequest.text)
        
        return TwitcastStream.HappyToken(HappyTokenRequestData["token"])
        
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
    def GetPubSubURL(self, movieID) -> TwitcastStream.EventsPubSubURL:
        PubSubURL = "https://twitcasting.tv/eventpubsuburl.php"
        PubSubData = {'movie_id': movieID}
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
        return CookiesHandler.get_cookies_header(self.session.cookies, "https://twitcasting.tv")

    def __init__(self, UserInput) -> None:
        # Input TwitcastStream.py Userinput object
        self.userInput = UserInput
        self.session = requests.Session()
        self.session.cookies = self.userInput["cookies"] or requests.cookies.RequestsCookieJar()

        self.CurrentStream = self.GetStream(self.userInput["username"])
        self.CurrentStreamToken = self.GetToken(self.CurrentStream.movie_id)
        self.CurrentStreamInfo = self.GetStreamInfo(self.CurrentStream.movie_id, self.CurrentStreamToken)
        self.CurrentStreamPubSubURL = self.GetPubSubURL(self.CurrentStream.movie_id)
