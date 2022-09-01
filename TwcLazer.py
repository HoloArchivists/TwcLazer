# TWCLAZER.py
# EF1500
# TWITCAST DOWNLOADER WITH CHAT
# https://github.com/ef1500

import argparse
import asyncio
import datetime
import threading
import os
from unittest import defaultTestLoader

import helpers.CLIhelper as CLIhelper
import twitcasting.TwitcastAPI as TwitcastAPI
import twitcasting.TwitcastWebsocket as TwitcastWebsocket
import utils.ChatFormatter as ChatFormatter
import twitcasting.TwitcastingListener as TwitcastListener
import notifHandlers.discord_notif_handler as DiscordHandler

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-h", "--help", action="store_true")
parser.add_argument("-u", "--username", type=str)
parser.add_argument("-q", "--quality", type=str, default="low")
parser.add_argument("-ff", "--fileformat", type=str, default="Twitcasting-%%Un-%%Dy_%%Dm_%%Dd")
parser.add_argument("-p", "--path", type=str, default=None)
parser.add_argument("-m", "--monitor", action="store_true", default=False)
parser.add_argument("-dU", "--discordUrl", type=str, default=None)
parser.add_argument("-nT", "--notifText", type=str, default=None)

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
    "monitor" : args.monitor,
    "discordURL" : args.discordUrl,
    "notifText" : args.notifText,
    
    "noWarn": args.noWarn,
    "noRetry": args.noRetry,
    "printChat": args.printChat,
    
    "chatformat": args.chatFormat,
    "giftformat": args.giftFormat
}

if UserIn["path"] is not None and not os.path.exists(UserIn["path"]):
    print(f"{UserIn['path']} is not a valid directory.")
    exit()

if TwitcastAPI.TwitcastingAPI.is_live(UserIn["username"]) is False and UserIn["monitor"] is False:
    print(f"{UserIn['username']} is not live.")
    exit()

TwAPI = TwitcastAPI.TwitcastingAPI(UserIn)

if UserIn["monitor"] is True and UserIn["discordURL"] is None:
    print("Missing argument: -dU, --discordUrl.")
    exit()
else:
    pass

if UserIn["monitor"] is True:
    NotifHandler = DiscordHandler.discord_embed_handler(UserIn["discordURL"], 0x07ff03,
                                      TwAPI.CurrentStreamInfo.title, TwAPI.CurrentStreamInfo.category_name, UserIn["username"], TwAPI.CurrentStreamInfo.movie_id, UserIn["notifText"])
    
    TwitcastListener = TwitcastListener.TwitcastListener(UserIn["username"], NotifHandler.send_embed)
    
    asyncio.run(TwitcastListener.listen())
    exit()
else:
    pass

# Now that we have the API object Created, we're good to go for making the fileformat object
today = datetime.datetime.now()
FileFormat_Translations = {
    "%%Tt" : TwAPI.CurrentStreamInfo.title,
    "%%Tl" : TwAPI.CurrentStreamInfo.telop,
    "%%Ci" : TwAPI.CurrentStreamInfo.category_id,
    "%%Cn" : TwAPI.CurrentStreamInfo.category_name,
    "%%Dy" : str(today.year),
    "%%Dm" : str(today.month),
    "%%Dd" : str(today.day),
    "%%Un" : UserIn["username"]
}

UserIn["fileformat"] = ChatFormatter.strTranslate(UserIn["fileformat"], FileFormat_Translations)
    

if UserIn["monitor"] is False:
    
    if UserIn["path"] is not None:
        UserIn["fileformat"] = os.path.join(UserIn["path"], UserIn["fileformat"])

    # Great, now we're locked and loaded!
    def between_callback(func, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(func(*args, **kwargs))
        loop.close()

    tasks = list()
    if UserIn["quality"] is not None:
        tasks.append(threading.Thread(target=between_callback, args=(
            TwitcastWebsocket.TwitcastVideoSocket.runListener, TwAPI, UserIn["fileformat"], UserIn["quality"], UserIn["noWarn"], UserIn["noRetry"],)))
    else:
        tasks.append(threading.Thread(target=between_callback, args=(
            TwitcastWebsocket.TwitcastVideoSocket.runListener, TwAPI, UserIn["fileformat"], UserIn["noRetry"],)))    

    if UserIn["withchat"] is True:
        tasks.append(threading.Thread(target=between_callback, args=(
            TwitcastWebsocket.TwitcastEventSocket.RecieveMessages, TwAPI.CurrentStreamPubSubURL.url,
            TwAPI, f"{UserIn['fileformat']}", UserIn['printChat'],UserIn['chatformat'],
            UserIn['giftformat'])))

    for task in tasks:
        task.start()
