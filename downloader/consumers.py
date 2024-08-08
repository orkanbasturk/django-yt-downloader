import json
from channels.generic.websocket import WebsocketConsumer

class ProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'message': 'İndirmeye Hazırlanıyor'
        }))

    def disconnect(self, close_code):
        pass

    def send_progress(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
