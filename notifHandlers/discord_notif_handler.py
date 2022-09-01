# Discord Notif Handler
# EF1500
import requests

class discord_notif_handler:
    
    def __init__(self, webhook_url):
        self.webhook =  webhook_url
        
    def webhook(self):
        return self.webhook
        

class discord_embed_handler(discord_notif_handler):
    
    def __init__(self, url, color, title, category, username, movie_id, notifText=None):
        
        super().__init__(url)

        self.started_at = title # Field
        self.category = category # Field
        self.username = username
        self.movie_id = movie_id
        self.notifText = notifText
        self.title = title
        self.color = color
        
        self.data = {
    "content" : self.notifText,
    "username" : "TwcLazer Alert System"}
        
        self.data["embeds"] = [{
        "type": "rich",
        "title": "Twitcasting Notification",
        "description": f"{self.username} Is Now Live!\nhttps://twitcasting.tv/{self.username}",
        "color": self.color, # 0x07ff03 for green
        "fields": [
            {
            "name": "Title",
            "value": f"{self.title}",
            "inline": True
            },
            {
            "name": "Category",
            "value": f"{self.category}",
            "inline": True
            }
        ],
        "image": {
            "url": f"https://twitcasting.tv/{self.username}/thumb/{self.movie_id}",
            "height": 0,
            "width": 0
        },
        "author": {
            "name": "TwcLazer",
            "url": "https://github.com/HoloArchivists/TwcLazer",
            "icon_url": "https://imgur.com/VEcXhFz.png"
        },
        "footer": {
            "text": "Powered by EF1500 | HoloArchivists",
            "icon_url": "https://imgur.com/zgwxdoy.png"
        }
        }
    ]
    
    def send_embed(self):
        try:
            requests.post(super().webhook(), json=self.data)
        except requests.exceptions.HTTPError:
            print("[Notif Handler] HttpError")
            