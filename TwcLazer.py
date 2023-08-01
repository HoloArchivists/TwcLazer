# TWCLAZER.py
# EF1500
# TWITCAST DOWNLOADER WITH CHAT
# https://github.com/ef1500

import argparse
import asyncio
import datetime
import threading
import os

import helpers.CLIhelper as CLIhelper
import twitcasting.TwitcastAPI as TwitcastAPI
import twitcasting.TwitcastWebsocket as TwitcastWebsocket
import utils.ChatFormatter as ChatFormatter
from utils.CookiesHandler import CookiesHandler

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-h", "--help", action="store_true")
parser.add_argument("-u", "--username", type=str)
parser.add_argument("-q", "--quality", type=str, default="low")
parser.add_argument("-ff", "--fileformat", type=str, default="Twitcasting-%Un-%Mi-%Dy_%Dm_%Dd")
parser.add_argument("-p", "--path", type=str, default=None)
parser.add_argument("-c", "--cookies", type=str, default=None)
parser.add_argument("-s", "--secret", type=str, default=None)

parser.add_argument("-nW", "--noWarn", action="store_true", default=False)
parser.add_argument("-nR", "--noRetry", action="store_true", default=False)
parser.add_argument("-pC", "--printChat", action="store_true", default=False)
parser.add_argument("-wC", "--withChat", action="store_true", default=False)

parser.add_argument("-cF", "--chatFormat", type=str, default="%As: %Mg | %Ca")
parser.add_argument("-gF", "--giftFormat", type=str, default="Gift: %In | %Mg | %Ss")

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
    "secret": args.secret,
    
    "noWarn": args.noWarn,
    "noRetry": args.noRetry,
    "printChat": args.printChat,
    
    "chatformat": args.chatFormat,
    "giftformat": args.giftFormat
}

if args.cookies is not None:
    UserIn["cookies"] = CookiesHandler.load_cookies(args.cookies)
else:
    UserIn["cookies"] = None

if UserIn["path"] is not None and not os.path.exists(UserIn["path"]):
    print(f"{UserIn['path']} is not a valid directory.")
    exit()

if TwitcastAPI.TwitcastingAPI.user_is_live(UserIn["username"], UserIn["cookies"]):
    print(f"{UserIn['username']} is live, downloading")
else:
    print(f"{UserIn['username']} is not live.")
    exit()

TwAPI = TwitcastAPI.TwitcastingAPI(UserIn)

# Now that we have the API object Created, we're good to go for making the fileformat object
today = datetime.datetime.now()
Fileformatter = ChatFormatter.FileFormatter()
FileFormat_Translations = {
    "Tt" : TwAPI.CurrentStreamInfo.title,
    "Tl" : TwAPI.CurrentStreamInfo.telop,
    "Dy" : str(today.year),
    "Dm" : str(today.month),
    "Dd" : str(today.day),
    "Un" : UserIn["username"],
    "Mi" : TwAPI.CurrentStream.movie_id
}

UserIn["fileformat"] = Fileformatter.FormatFilename(UserIn["fileformat"], FileFormat_Translations)

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
for task in tasks:
    task.join()

