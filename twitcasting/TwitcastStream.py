# TwitcastStream.py
# Minimal Definition of a Twitcasting Stream
from dataclasses import dataclass

@dataclass
class TwitcastStream_:
    '''Expanded Twitcasting Stream Variables'''
    update_interval_sec: int
    movie_id: int
    title: str
    telop: str
    category_id: str
    category_name: str
    viewers_current: int
    viewers_total: int
    hashtag: str
    pin_message: str
    
@dataclass
class StreamServer:
    '''Twitcasting Streamserver'''
    movie_id: int
    live: bool
    
    hls_host: str
    hls_proto: str
    hls_source: bool

    fmp4_host: str
    fmp4_proto: str
    fmp4_source: bool
    fmp4_mobilesource: bool
    
    # Rule of thumb:
    # Main -> best
    # Base -> worst
    # Mobilesource -> low
    llfmp4_stream_main: str
    llfmp4_stream_base: str = None
    llfmp4_stream_mobilesource: str = None
    
    
@dataclass
class EventsPubSubURL:
    '''EventsPubSubURL - WSS'''
    url: str
    
@dataclass
class HappyToken:
    '''Twitcasting Happytoken'''
    token: str

class PasswordCookie(str):
    '''Used to access password-protected stream'''
    
@dataclass
class StreamEvent_Comment:
    '''Comment Event'''
    author_grade: int
    author_id: str
    author_name: str
    author_profile_image: str
    author_screenName: str
    
    createdAt: int
    event_id: int
    message: str
    numComments: int
    eventType: str
    
@dataclass
class StreamEvent_Gift:
    '''Gift Event'''
    createdAt: int
    event_id: int
    
    item_detailImage: str
    item_effectCommand: str
    item_image: str
    item_name: str
    item_showsSenderInfo: bool
    
    message: str
    
    sender_grade: int
    sender_id: str
    sender_name: str 
    sender_profileImage: str 
    sender_screenName: str 
    
    eventType: str