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
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chatroom', 'created_at']),
            models.Index(fields=['room_type', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"
