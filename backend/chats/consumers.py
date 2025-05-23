import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage, ChatParticipant
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from accounts.models import User
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class BaseChatConsumer(AsyncWebsocketConsumer):
    """기본 채팅 컨슈머 - 공통 기능"""
    
    async def connect(self):
        # 토큰 검증
        self.user = await self.get_user_from_token()
        if not self.user:
            await self.close(code=4001)
            return
        
        # 그룹에 추가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 참여자 수 업데이트 및 알림
        participants_info = await self.update_participants_count()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '연결 성공',
            'user': self.user.username
        }))
    
    async def disconnect(self, close_code):
        # 그룹에서 제거
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            content = data.get('content', '').strip()
            if content:
                # 메시지 저장 및 브로드캐스트
                message = await self.save_message(content)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message
                    }
                )
    
    async def chat_message(self, event):
        message = event['message']
        
        # WebSocket으로 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    @database_sync_to_async
    def get_user_from_token(self):
        """토큰에서 사용자 정보 추출"""
        try:
            # 쿼리 파라미터에서 토큰 추출
            query_string = self.scope.get('query_string', b'').decode()
            
            token = None
            # 쿼리 문자열 파싱
            if query_string:
                params = {}
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
                token = params.get('token')
            
            if not token:
                return None
            
            # 토큰 검증
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.get(id=user_id)
            return user
        except Exception as e:
            return None
    
    @database_sync_to_async
    def update_participants_count(self):
        """참여자 수 업데이트 및 그룹에 알림"""
        return {'count': 0}  # 기본 구현은 하위 클래스에서 오버라이드

class ChatConsumer(BaseChatConsumer):
    """일반 채팅방 Consumer"""
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # 채팅방 존재 확인
        room_exists = await self.check_room_exists()
        if not room_exists:
            await self.close(code=4002)
            return
        
        await super().connect()
    
    @database_sync_to_async
    def check_room_exists(self):
        """채팅방 존재 확인"""
        try:
            self.room = ChatRoom.objects.get(id=self.room_id)
            return True
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """메시지 저장"""
        # 사용자가 채팅방에 참여하지 않았다면 자동 참여
        if not ChatParticipant.objects.filter(user=self.user, chatroom=self.room).exists():
            ChatParticipant.objects.create(user=self.user, chatroom=self.room)
        
        # 메시지 생성
        message = ChatMessage.objects.create(
            user=self.user,
            chatroom=self.room,
            content=content,
            room_type='stock'
        )
        
        # 직렬화된 메시지 반환
        return {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'nickname': getattr(self.user, 'nickname', None),
                'has_loser_badge': getattr(self.user, 'loser_badge_count', 0) > 0,
                'has_champion_badge': getattr(self.user, 'champion_badge_count', 0) > 0
            }
        }
    
    @database_sync_to_async
    def update_participants_count(self):
        """참여자 수 업데이트 및 그룹에 알림"""
        participants_count = self.room.participants.count()
        
        # 알림 전송
        return {
            'count': participants_count
        }

class LoserChatConsumer(BaseChatConsumer):
    """패잔병 토론방 Consumer"""
    
    async def connect(self):
        self.room_group_name = 'chat_loser'
        
        # 패잔병 토론방 가져오기 또는 생성
        self.room = await self.get_or_create_loser_room()
        
        await super().connect()
    
    @database_sync_to_async
    def get_or_create_loser_room(self):
        """패잔병 토론방 가져오기 또는 생성"""
        room, created = ChatRoom.objects.get_or_create(
            stock__isnull=True,
            defaults={'name': '패잔병 토론방'}
        )
        return room
    
    @database_sync_to_async
    def save_message(self, content):
        """메시지 저장"""
        # 사용자가 채팅방에 참여하지 않았다면 자동 참여
        if not ChatParticipant.objects.filter(user=self.user, chatroom=self.room).exists():
            ChatParticipant.objects.create(user=self.user, chatroom=self.room)
        
        # 메시지 생성
        message = ChatMessage.objects.create(
            user=self.user,
            chatroom=self.room,
            content=content,
            room_type='loser'
        )
        
        # 직렬화된 메시지 반환
        return {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'nickname': getattr(self.user, 'nickname', None),
                'has_loser_badge': getattr(self.user, 'loser_badge_count', 0) > 0,
                'has_champion_badge': getattr(self.user, 'champion_badge_count', 0) > 0
            }
        }
    
    @database_sync_to_async
    def update_participants_count(self):
        """참여자 수 업데이트 및 그룹에 알림"""
        participants_count = self.room.participants.count()
        
        # 알림 전송
        return {
            'count': participants_count
        }

# 메시지 최대 개수 제한 (300개)
@receiver(post_save, sender=ChatMessage)
def limit_messages(sender, instance, **kwargs):
    # 방이 있는 경우 (일반 토론방)
    if instance.chatroom:
        messages_count = ChatMessage.objects.filter(chatroom=instance.chatroom).count()
        if messages_count > 300:
            # 가장 오래된 메시지부터 삭제 (bulk delete 사용)
            oldest_messages = ChatMessage.objects.filter(chatroom=instance.chatroom).order_by('created_at')[:messages_count-300]
            ChatMessage.objects.filter(id__in=oldest_messages.values_list('id', flat=True)).delete()
    
    # 패잔병 토론방 메시지인 경우
    if instance.room_type == 'loser':
        loser_messages_count = ChatMessage.objects.filter(room_type='loser').count()
        if loser_messages_count > 300:
            # 가장 오래된 메시지부터 삭제 (bulk delete 사용)
            oldest_loser_messages = ChatMessage.objects.filter(room_type='loser').order_by('created_at')[:loser_messages_count-300]
            ChatMessage.objects.filter(id__in=oldest_loser_messages.values_list('id', flat=True)).delete()
