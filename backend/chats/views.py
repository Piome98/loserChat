from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatRoom, ChatMessage
from .serializers import ChatMessageSerializer, ChatRoomSerializer

# Create your views here.

class ChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, room_id):
    """특정 토론방의 메시지를 가져옵니다."""
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        messages = ChatMessage.objects.filter(chatroom=chatroom).order_by('-created_at')[:300]  # 최신 300개만 가져옴
        
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({
            'results': serializer.data,
            'participants_count': chatroom.participants_count
        })
    except ChatRoom.DoesNotExist:
        return Response({"error": "토론방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_loser_messages(request):
    """패잔병 토론방의 메시지를 가져옵니다."""
    try:
        loser_room = ChatRoom.objects.get(stock__isnull=True)  # 패잔병 토론방 (stock이 없는 방)
        messages = ChatMessage.objects.filter(room_type='loser').order_by('-created_at')[:300]  # 최신 300개만 가져옴
        
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({
            'results': serializer.data,
            'participants_count': loser_room.participants_count
        })
    except ChatRoom.DoesNotExist:
        # 패잔병 토론방이 없으면 생성
        loser_room = ChatRoom.objects.create(name="패잔병 토론방")
        return Response({
            'results': [],
            'participants_count': 0
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, room_id):
    """특정 토론방에 메시지를 전송합니다."""
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        
        # 기존 ChatParticipant이 없는 경우 자동으로 생성 (토론방 참여)
        if not chatroom.participants.filter(id=request.user.id).exists():
            chatroom.participants.add(request.user)
        
        content = request.data.get('content', '').strip()
        if not content:
            return Response({"error": "메시지 내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        message = ChatMessage.objects.create(
            user=request.user,
            chatroom=chatroom,
            content=content,
            room_type='stock'
        )
        
        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ChatRoom.DoesNotExist:
        return Response({"error": "토론방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_loser_message(request):
    """패잔병 토론방에 메시지를 전송합니다."""
    try:
        loser_room = ChatRoom.objects.get(stock__isnull=True)  # 패잔병 토론방
        
        # 자동으로 참여자 추가
        if not loser_room.participants.filter(id=request.user.id).exists():
            loser_room.participants.add(request.user)
        
        content = request.data.get('content', '').strip()
        if not content:
            return Response({"error": "메시지 내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        message = ChatMessage.objects.create(
            user=request.user,
            chatroom=loser_room,
            content=content,
            room_type='loser'
        )
        
        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ChatRoom.DoesNotExist:
        # 패잔병 토론방이 없으면 생성
        loser_room = ChatRoom.objects.create(name="패잔병 토론방")
        loser_room.participants.add(request.user)
        
        content = request.data.get('content', '').strip()
        message = ChatMessage.objects.create(
            user=request.user,
            chatroom=loser_room,
            content=content,
            room_type='loser'
        )
        
        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_chat_rooms(request):
    """현재 사용자가 참여하고 있는 토론방 목록을 가져옵니다."""
    chat_rooms = ChatRoom.objects.filter(participants=request.user).order_by('-created_at')
    serializer = ChatRoomSerializer(chat_rooms, many=True)
    return Response({
        'results': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_chat_room(request, room_id):
    """특정 토론방에서 나갑니다."""
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        
        # 참여자가 아니면 에러 반환
        if not chatroom.participants.filter(id=request.user.id).exists():
            return Response({"error": "참여하지 않은 토론방입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 참여자에서 제거
        chatroom.participants.remove(request.user)
        
        return Response({"message": "토론방에서 나갔습니다."}, status=status.HTTP_200_OK)
    except ChatRoom.DoesNotExist:
        return Response({"error": "토론방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    """메시지를 삭제합니다. 자신이 작성한 메시지만 삭제 가능합니다."""
    try:
        message = ChatMessage.objects.get(id=message_id)
        
        # 자신이 작성한 메시지가 아니면 삭제 불가
        if message.user.id != request.user.id:
            return Response({"error": "자신이 작성한 메시지만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        message.delete()
        return Response({"message": "메시지가 삭제되었습니다."}, status=status.HTTP_200_OK)
    except ChatMessage.DoesNotExist:
        return Response({"error": "메시지를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_chat_room(request, room_id):
    """특정 토론방에 참여합니다."""
    try:
        chatroom = ChatRoom.objects.get(id=room_id)
        
        # 이미 참여 중이면 메시지만 반환
        if chatroom.participants.filter(id=request.user.id).exists():
            return Response({"message": "이미 참여 중인 토론방입니다."}, status=status.HTTP_200_OK)
        
        # 참여자에 추가
        chatroom.participants.add(request.user)
        
        return Response({"message": "토론방에 참여했습니다."}, status=status.HTTP_201_CREATED)
    except ChatRoom.DoesNotExist:
        return Response({"error": "토론방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
