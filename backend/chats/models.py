from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.ForeignKey('stocks.Stock', on_delete=models.CASCADE, null=True, blank=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatParticipant')
    
    def __str__(self):
        return self.name
    
    @property
    def participants_count(self):
        return self.participants.count()
    
    @property
    def is_loser_room(self):
        return self.stock is None

class ChatParticipant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'chatroom')

class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    room_type = models.CharField(max_length=10, choices=[('stock', 'Stock'), ('loser', 'Loser')])
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chatroom', 'created_at']),
            models.Index(fields=['room_type', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"

# 메시지 최대 개수 제한 (300개)
@receiver(post_save, sender=ChatMessage)
def limit_messages(sender, instance, **kwargs):
    # 방이 있는 경우 (일반 토론방)
    if instance.chatroom:
        messages_count = ChatMessage.objects.filter(chatroom=instance.chatroom).count()
        if messages_count > 300:
            # 가장 오래된 메시지부터 삭제
            oldest_messages = ChatMessage.objects.filter(chatroom=instance.chatroom).order_by('created_at')[:messages_count-300]
            for msg in oldest_messages:
                msg.delete()
    
    # 패잔병 토론방 메시지인 경우
    if instance.room_type == 'loser':
        loser_messages_count = ChatMessage.objects.filter(room_type='loser').count()
        if loser_messages_count > 300:
            # 가장 오래된 메시지부터 삭제
            oldest_loser_messages = ChatMessage.objects.filter(room_type='loser').order_by('created_at')[:loser_messages_count-300]
            for msg in oldest_loser_messages:
                msg.delete()
