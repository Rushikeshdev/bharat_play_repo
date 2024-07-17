from channels.generic.websocket import AsyncWebsocketConsumer
import json

class WithdrawalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close(code=403)
        else:
            await self.channel_layer.group_add('withdrawal_updates', self.channel_name)
            await self.accept()
            print("WebSocket connection opened")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('withdrawal_updates', self.channel_name)

    async def withdrawal_update(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
        print(f"Message sent: {message}")
