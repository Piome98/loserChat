from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StockViewSet, 
    StockRoomViewSet, 
    loser_room, 
    send_message, 
    get_messages
)

# ViewSet 라우터 설정
router = DefaultRouter()
router.register(r'stocks', StockViewSet)
router.register(r'rooms', StockRoomViewSet)

urlpatterns = [
    # ViewSet URL
    path('', include(router.urls)),
    
    # 패잔병 토론방
    path('loser-room/', loser_room, name='loser_room'),
    
    # 메시지 관련
    path('rooms/<int:room_id>/messages/', get_messages, name='get_messages'),
    path('rooms/<int:room_id>/send-message/', send_message, name='send_message'),
    path('loser-room/messages/', get_messages, name='get_loser_messages'),
    path('loser-room/send-message/', send_message, name='send_loser_message'),
] 