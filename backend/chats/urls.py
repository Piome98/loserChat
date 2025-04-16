from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatRoomViewSet, get_messages, get_loser_messages, 
    send_message, send_loser_message, get_my_chat_rooms,
    leave_chat_room, delete_message, join_chat_room
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('rooms/<int:room_id>/messages/', get_messages),
    path('rooms/<int:room_id>/send-message/', send_message),
    path('loser-room/messages/', get_loser_messages),
    path('loser-room/send-message/', send_loser_message),
    path('my-rooms/', get_my_chat_rooms),
    path('rooms/<int:room_id>/leave/', leave_chat_room),
    path('rooms/<int:room_id>/join/', join_chat_room),
    path('messages/<int:message_id>/delete/', delete_message),
]
