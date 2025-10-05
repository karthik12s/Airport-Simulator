from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class AirportConsumer(WebsocketConsumer):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AirportConsumer, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        self.user = self.scope['user']
        self.org = "airport"
        async_to_sync(self.channel_layer.group_add)(
            self.org,self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.org,self.channel_name
        )

    
    def receive(self, text_data = None, bytes_data = None):
        return super().receive(text_data, bytes_data)
    
    def push_notifications(self,data = None):
        event = {
            'type':"notification_event",
            'message':data
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("airport",event)
        
    
    def notification_event(self,event):
        data = event['message']
        self.send(text_data=data)
