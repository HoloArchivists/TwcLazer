# Twitcasting Websocket Handler
import websockets, asyncio
import twitcasting.TwitcastStream as TwitcastStream
import utils.ChatFormatter as ChatFormatter
import helpers.CLIhelper as CLIhelper
import json
import urllib

# Twitcasting Video Socket
# Get Video Data from the twitcasting websocket
# The connection has a tendency to randomly just 'drop' or lag, Causing evident lagspikes in the video.
# The fallback seems to be an m3u8 "metastream" to fill in the gaps, but some streams do not have this,
# and querying for the metastream throws a 404 or 502.
# So as of now, extremely evident lagspikes will be persistent in the recordings until
# Someone figures out otherwise. 
class TwitcastVideoSocket:
    
    def count(numbytes, format="KB"):
        # Return a formatted version of the filesize
        prefixes = {
            "KB" : 1000,
            "MB" : 1000000,
            "GB" : 1000000000
        }
        return f"{numbytes/prefixes[format]} {format}"
    
    # Gather Stream Frames
    async def listen(url, TwitcastApiOBJ, filename, NoRetry=False):
        recieved_bytes = 0
        while True:
            async with websockets.connect(url, extra_headers=TwitcastApiOBJ.cookies_header) as ws:
                try:
                    while True:
                        with open(f"{filename}.mp4", 'ab') as filewriter:
                            msg = await asyncio.wait_for(ws.recv(), timeout=25) # https://github.com/HoloArchivists/TwcLazer/issues/5
                            if len(msg) != 1108:
                                recieved_bytes += len(msg)
                                print(f"[WebSocket] Recieved {TwitcastVideoSocket.count(len(msg))} from host | Collected {TwitcastVideoSocket.count(recieved_bytes, format='MB')}    ", end='\r')
                                filewriter.write(msg)
                except Exception as e:
                    print(f"[WebSocket] {e!r}, checking if stream is still live" + " "*30)
                    if TwitcastApiOBJ.is_live():
                        if NoRetry == True:
                            print("[WebSocket] Connection Dropped, Closing Socket..." + " "*30)
                            break
                        else:
                            print("[WebSocket] Connection Dropped, Reconnecting" + " "*30)
                            
                    else:
                        print("[WebSocket] Stream Ended, Closing Socket..." + " "*30)
                        break
    
    async def runListener(TwitcastApiOBJ, filename, quality="low", NoWarn=False, NoRetry=False):
        
        if quality == "best" and NoWarn != True:
            print(CLIhelper.HIGH_QUAL_WARNING)
            
        qualities = {
            "best" : TwitcastApiOBJ.CurrentStream.llfmp4_stream_main,
            "low" : TwitcastApiOBJ.CurrentStream.llfmp4_stream_mobilesource,
            "worst" : TwitcastApiOBJ.CurrentStream.llfmp4_stream_base
        }
        
        url = qualities[quality]
        if url == None and quality == "low":
            print("Unable to locate MobileSource, Defaulting to Main.")
            url = qualities["best"]
        password = TwitcastApiOBJ.GetPasswordCookie(TwitcastApiOBJ.userInput["username"])
        if password is not None:
            url = update_url(url, [("word", password)])

        await TwitcastVideoSocket.listen(url, TwitcastApiOBJ, filename, NoRetry)

def update_url(url, params):
    url = urllib.parse.unquote(url)
    parsed_url = urllib.parse.urlparse(url)
    get_args = parsed_url.query
    parsed_get_args = urllib.parse.parse_qsl(get_args)
    parsed_get_args.extend(params)
    encoded_get_args = urllib.parse.urlencode(parsed_get_args, doseq=True)
    return urllib.parse.ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()

# Twitcast Event Socket
# Socket for recieving events from the chat and gifts things like that
class TwitcastEventSocket:
    def parseGift(giftJSON) -> TwitcastStream.StreamEvent_Gift:
        giftData = giftJSON[0]
        
        return TwitcastStream.StreamEvent_Gift(
            giftData["createdAt"],
            giftData["id"],
            giftData.get("item").get("detailImage"),
            giftData.get("item").get("effectCommand"),
            giftData.get("item").get("image"),
            giftData.get("item").get("name"),
            giftData.get("item").get("showsSenderInfo"),
            giftData["message"],
            giftData["sender"]["grade"],
            giftData["sender"]["id"],
            giftData["sender"]["name"],
            giftData["sender"]["profileImage"],
            giftData["sender"]["screenName"],
            giftData["type"]
        )
        
    def parseComment(CommentJSON) -> TwitcastStream.StreamEvent_Comment:
        commentData = CommentJSON[0]

        return TwitcastStream.StreamEvent_Comment(
            commentData.get("author").get("grade"),
            commentData.get("author").get("id"),
            commentData.get("author").get("name"),
            commentData.get("author").get("profileImage"),
            commentData.get("author").get("screenName"),
            commentData["createdAt"],
            commentData["id"],
            commentData.get("message"),
            commentData["numComments"],
            commentData["type"]
        )
        
    # Todo: Allow for full customization of the format
    # e.g raw json, only specific attributes, etc.
    async def eventhandler(websocket, TwitcastApiOBJ, filename, printChat, CommentFormatString, GiftFormatString):
        while TwitcastApiOBJ.is_live():
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=25)
                eventData = json.loads(message)
                if not eventData:
                    continue
                if eventData[0]["type"] == "comment":
                    eventMessage = TwitcastEventSocket.parseComment(eventData)
                    formatted_event_message = ChatFormatter.ChatFormatter().FormatComments(CommentFormatString, eventMessage)
                elif eventData[0]["type"] == "gift":
                    eventMessage = TwitcastEventSocket.parseGift(eventData)
                    formatted_event_message = ChatFormatter.ChatFormatter().FormatGifts(GiftFormatString, eventMessage)
                else:
                    formatted_event_message = str(eventData)
                if printChat:
                    print("[ChatEvent] " + formatted_event_message+ " "*30)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.WebSocketException as e:
                print(f"[EventSocket] error while receiving chat message: {e!r}")
                break
            except Exception as e:
                print(f"[EventSocket] error while processing chat message: {e!r}")
                print(f"[EventSocket] message: {eventData}")
                break
            else:
                with open(f"{filename}.txt", 'a+', encoding="utf8") as f:
                    f.write(formatted_event_message + "\n")

    async def RecieveMessages(websocket_url, TwAPI, filename, printChat, CommentFormatString, GiftFormatString):
        url = websocket_url
        async with websockets.connect(url, extra_headers=TwAPI.cookies_header) as ws:
            await TwitcastEventSocket.eventhandler(ws, TwAPI, filename, printChat, CommentFormatString, GiftFormatString)
