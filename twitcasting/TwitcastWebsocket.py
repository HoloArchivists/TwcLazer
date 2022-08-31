# Twitcasting Websocket Handler
import websockets, asyncio
import twitcasting.TwitcastStream as TwitcastStream
import utils.ChatFormatter as ChatFormatter
import helpers.CLIhelper as CLIhelper
import json

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
            async with websockets.connect(url) as ws:
                try:
                    while True:
                        with open(f"{filename}.mp4".replace(":", "-"), 'ab') as filewriter:
                            msg = await asyncio.wait_for(ws.recv(), timeout=2)
                            if len(msg) != 1108:
                                recieved_bytes += len(msg)
                                print(f"[WebSocket] Recieved {TwitcastVideoSocket.count(len(msg))} from host | Collected {TwitcastVideoSocket.count(recieved_bytes, format='MB')}    ", end='\r')
                                filewriter.write(msg)
                
                except Exception:
                    if TwitcastApiOBJ.GetStream(TwitcastApiOBJ.userInput["username"]).live == True:
                        if NoRetry == True:
                            print(f"[WebSocket] Connection Dropped, Closing Socket..." + " "*30, end='\r')
                            await ws.close()
                            break
                        else:
                            print(f"[WebSocket] Connection Dropped, Reconnecting" + " "*30, end='\r')
                            await ws.close()
                            
                    else:
                        print(f"[WebSocket] Stream Ended, Closing Socket..." + " "*30, end='\r')
                        await ws.close()
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
            
        
        await TwitcastVideoSocket.listen(url, TwitcastApiOBJ, filename, NoRetry)
            
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
        while TwitcastApiOBJ.GetStream(TwitcastApiOBJ.userInput["username"]).live == True:
            message = await websocket.recv()
            with open(f"{filename}.txt".replace(":", "-"), 'a+', encoding="utf8") as f:
                eventData = json.loads(message)
                
                try:
                    if eventData[0]["type"] == "comment":
                        eventMessage = TwitcastEventSocket.parseComment(eventData)
                        formatted_event_message = ChatFormatter.ChatFormatter.FormatComments(CommentFormatString, eventMessage)
                        
                        f.write(formatted_event_message + "\n")

                        if printChat == True:
                            print("[ChatEvent] " + formatted_event_message+ " "*30, end='\n\r')                        
                        
                    if eventData[0]["type"] == "gift":
                        eventMessage = TwitcastEventSocket.parseGift(eventData)
                        formatted_event_message = ChatFormatter.ChatFormatter.FormatGifts(GiftFormatString, eventMessage)
                        
                        f.write(formatted_event_message + "\n")

                        if printChat == True:
                            print("[ChatEvent] " + formatted_event_message+ " "*30,end='\n\r')       
                        
                except IndexError:
                    pass

    async def RecieveMessages(websocket_url, TwAPI, filename, printChat, CommentFormatString, GiftFormatString):
        url = websocket_url
        async with websockets.connect(url) as ws:
            await TwitcastEventSocket.eventhandler(ws, TwAPI, filename, printChat, CommentFormatString, GiftFormatString)
            await asyncio.Future()  # run forever
