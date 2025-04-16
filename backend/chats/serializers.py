from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from accounts.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

# UserSerializer 직접 정의
class UserBasicSerializer(serializers.ModelSerializer):
    has_loser_badge = serializers.SerializerMethodField()
    has_champion_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'has_loser_badge', 'has_champion_badge']
    
    def get_has_loser_badge(self, obj):
        # User 모델에 loser_badge_count 필드가 있다고 가정
        return obj.loser_badge_count > 0
    
    def get_has_champion_badge(self, obj):
        # User 모델에 champion_badge_count 필드가 있다고 가정
        return obj.champion_badge_count > 0

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'content', 'created_at', 'room_type']
        read_only_fields = ['id', 'user', 'created_at']

class ChatRoomSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'created_at', 'participants_count', 'is_loser_room']
    
    def get_participants_count(self, obj):
        return obj.participants_count

class CreateChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['content']
