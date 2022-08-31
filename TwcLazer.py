# TWCLAZER.py
# EF1500
# TWITCAST DOWNLOADER WITH CHAT
# https://github.com/ef1500

import twitcasting.TwitcastAPI as TwitcastAPI
import twitcasting.TwitcastStream as TwitcastStream
import twitcasting.TwitcastWebsocket as TwitcastWebsocket
import helpers.CLIhelper as CLIhelper
import utils.ChatFormatter as ChatFormatter
import datetime
import argparse
import threading

import asyncio

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-h", "--help", action="store_true")
parser.add_argument("-u", "--username", type=str)
parser.add_argument("-q", "--quality", type=str, default="low")
parser.add_argument("-ff", "--fileformat", type=str, default="Twitcasting-%%Un-%%Dy_%%Dm_%%Dd")
parser.add_argument("-p", "--path", type=str, default=None)

parser.add_argument("-nW", "--noWarn", action="store_true", default=False)
parser.add_argument("-nR", "--noRetry", action="store_true", default=False)
parser.add_argument("-pC", "--printChat", action="store_true", default=False)
parser.add_argument("-wC", "--withChat", action="store_true", default=False)

parser.add_argument("-cF", "--chatFormat", type=str, default="%%As: %%Mg | %%Ca")
parser.add_argument("-gF", "--giftFormat", type=str, default="Gift: %%In | %%Mg | %%Ss")

args = parser.parse_args()

if args.help is True:
    print(f"{CLIhelper.BANNER}\n{CLIhelper.OPTIONS}\n{CLIhelper.CHAT_FORMATTING_INFO}\n{CLIhelper.FILENAME_FORMATTING_INFO}")
    exit()

# Put input in a dict so we can create an API Object
UserIn = {
    "username": args.username,
    "quality" : args.quality,
    "fileformat": args.fileformat,
    "withchat": args.withChat,
    "path": args.path,
    
    "noWarn": args.noWarn,
    "noRetry": args.noRetry,
    "printChat": args.printChat,
    
    "chatformat": args.chatFormat,
    "giftformat": args.giftFormat
}

TwAPI = TwitcastAPI.TwitcastingAPI(UserIn)

# Now that we have the API object Created, we're good to go for making the fileformat object
today = datetime.datetime.now()
FileFormat_Translations = {
    "%%Tt" : TwAPI.CurrentStreamInfo.title,
    "%%Tl" : TwAPI.CurrentStreamInfo.telop,
    "%%Ci" : TwAPI.CurrentStreamInfo.category_id,
    "%%Cn" : TwAPI.CurrentStreamInfo.category_name,
    "%%Dy" : today.year.__str__(),
    "%%Dm" : today.month.__str__(),
    "%%Dd" : today.day.__str__(),
    "%%Un" : UserIn["username"]
}
UserIn["fileformat"] = ChatFormatter.strTranslate(UserIn["fileformat"], FileFormat_Translations)

# Great, now we're locked and loaded!
def between_callback(func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(func(*args, **kwargs))
    loop.close()

tasks = list()
tasks.append(threading.Thread(target=between_callback, args=(TwitcastWebsocket.TwitcastVideoSocket.runListener, TwAPI, UserIn["fileformat"],)))

if UserIn["withchat"] == True:
    tasks.append(threading.Thread(target=between_callback, args=(TwitcastWebsocket.TwitcastEventSocket.RecieveMessages, TwAPI.CurrentStreamPubSubURL.url, TwAPI, f"{UserIn['fileformat']}", UserIn['printChat'],UserIn['chatformat'], UserIn['giftformat'])))

#    TwAPI = TwitcastAPI.TwitcastingAPI(UserIn)
#    print(f"Using URL: {TwAPI.CurrentStream.llfmp4_stream_main}")
#    asyncio.run(TwitcastWebsocket.TwitcastVideoSocket.listenForData(TwAPI.CurrentStream.llfmp4_stream_main, UserIn.filename))
for task in tasks:
    task.start()
