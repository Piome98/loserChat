from django.contrib import admin
from .models import ChatRoom, ChatParticipant, ChatMessage

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'participants_count', 'is_loser_room')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'chatroom', 'joined_at', 'last_read')
    search_fields = ('user__username', 'chatroom__name')
    list_filter = ('joined_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'chatroom', 'content_preview', 'created_at', 'room_type')
    search_fields = ('user__username', 'content', 'chatroom__name')
    list_filter = ('created_at', 'room_type')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '메시지 내용'
