# Twitcasting Downloader API Functions
import requests
import json
import twitcasting.TwitcastStream as TwitcastStream

class TwitcastingAPI:
    '''Class for the functional Twitcasting API'''
    
    # Get Token
    @staticmethod
    def GetToken(movieID) -> TwitcastStream.HappyToken:
        HappyTokenURL = "https://twitcasting.tv/happytoken.php"
        HappyTokenData = {'movie_id': movieID}
        HappyTokenRequest = requests.post(HappyTokenURL, data=HappyTokenData)
        
        HappyTokenRequestData = json.loads(HappyTokenRequest.text)
        
        return TwitcastStream.HappyToken(HappyTokenRequestData["token"])
        
    # Get Current Stream
    @staticmethod
    def GetStream(username) -> TwitcastStream.StreamServer:
        StreamServerURL = f"https://twitcasting.tv/streamserver.php?target={username}&mode=client"
        StreamServer_Request = requests.get(StreamServerURL)
        
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
    @staticmethod
    def GetStreamInfo(movieID, token) -> TwitcastStream.TwitcastStream_:
        TwitcastStreamURL = f"https://frontendapi.twitcasting.tv/movies/{movieID}/status/viewer?token={token.token}"
        TwitcastStream_Request = requests.get(TwitcastStreamURL)
        
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
    @staticmethod
    def GetPubSubURL(movieID) -> TwitcastStream.EventsPubSubURL:
        PubSubURL = "https://twitcasting.tv/eventpubsuburl.php"
        PubSubData = {'movie_id': movieID}
        PubSubRequest = requests.post(PubSubURL, data=PubSubData)
        
        PubSubRequestData = json.loads(PubSubRequest.text)
        
        return TwitcastStream.EventsPubSubURL(PubSubRequestData["url"])
    
    @staticmethod
    def is_live(username) -> bool:
        is_user_live = requests.get(f"https://twitcasting.tv/userajax.php?c=islive&u={username}")
        if is_user_live.text == "0":
            return False
        else:
            return True
    
    def __init__(self, UserInput) -> None:
        # Input TwitcastStream.py Userinput object
        self.userInput = UserInput
        self.CurrentStream = TwitcastingAPI.GetStream(self.userInput["username"])
        self.CurrentStreamToken = TwitcastingAPI.GetToken(self.CurrentStream.movie_id)
        self.CurrentStreamInfo = TwitcastingAPI.GetStreamInfo(self.CurrentStream.movie_id, self.CurrentStreamToken)
        self.CurrentStreamPubSubURL = TwitcastingAPI.GetPubSubURL(self.CurrentStream.movie_id)