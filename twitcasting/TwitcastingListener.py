# Twitcasting Listener
# wait for a twitcast to start on a certain user

import twitcasting.TwitcastAPI as TwitcastingAPI
import asyncio

class TwitcastListener:
    
    """
    Essentially, we want to listen for a Twitcasting Livestream to Start.
    This can be done rather easily with the help of the Twitcasting API we wrote earlier.
    There are some predefined functions there that will allow us to easily define the listener
    so we can quickly and easily lisen.
    
    This will be a semi-rework of my failed "Monitor framework" project.
    """
    
    def __init__(self, username, callbackFunction) -> None:
        self.username = username # Username to listen on
        self.callbackFunction = callbackFunction # Function that we want to run a live has started
        self.checktimeout = 1 # Delay between requests (Default 1)
            
        
        
    
    async def listen(self, *args, **kwargs):
        while TwitcastingAPI.TwitcastingAPI.is_live(self.username) is not True:
            await asyncio.sleep(1)
            
        # If we got here, that means the user is live!
        self.callbackFunction(*args, **kwargs) #Send the notification!
        
    
        
#def callback_function(text):
#    print(text)
#    
#if __name__ == '__main__':
#    text = "USER IS LIVE!!!!"
#    username = "todo_natsu39"
#    TwitcastListener = TwitcastListener(username, callback_function, 1, text)
#    asyncio.run(TwitcastListener.listen())