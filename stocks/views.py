from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Stock, StockRoom, StockRoomMembership, Message
from .serializers import (
    StockSerializer, 
    StockRoomSerializer, 
    StockRoomDetailSerializer, 
    MessageSerializer
)


class StockViewSet(viewsets.ModelViewSet):
    """종목 관리 ViewSet"""
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    
    def get_permissions(self):
        """관리자만 종목 생성/수정/삭제 가능"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, pk=None):
        """종목 가격 수동 업데이트 (관리자용)"""
        stock = self.get_object()
        
        try:
            price = float(request.data.get('price', 0))
        except ValueError:
            return Response({"error": "유효한 가격을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        if price <= 0:
            return Response({"error": "가격은 0보다 커야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 가격 업데이트
        stock.current_price = price
        
        # 등락률 계산
        if stock.purchase_price:
            change = ((price - stock.purchase_price) / stock.purchase_price) * 100
            stock.percentage_change = round(change, 2)
        
        stock.save()
        
        # 종목이 루저 조건에 해당하면 멤버들을 퇴출시키고 루저 배지 부여
        if stock.is_loser and stock.is_active:
            self._handle_loser_stock(stock)
        
        # 종목이 챔피언 조건에 해당하면 멤버들에게 챔피언 배지 부여
        if stock.is_champion:
            self._handle_champion_stock(stock)
        
        serializer = self.get_serializer(stock)
        return Response(serializer.data)
    
    def _handle_loser_stock(self, stock):
        """루저 종목 처리 (멤버 퇴출 및 루저 배지 부여)"""
        # 해당 종목 토론방이 있는지 확인
        try:
            room = stock.room
        except StockRoom.DoesNotExist:
            return
        
        # 종목 비활성화
        stock.is_active = False
        stock.save()
        
        # 모든 멤버를 퇴출하고 루저 배지 부여
        memberships = StockRoomMembership.objects.filter(stock_room=room, is_kicked=False)
        for membership in memberships:
            # 유저 퇴출
            membership.kick_user()
            
            # 루저 배지 부여
            user = membership.user
            user.loser_badge_count += 1
            user.is_in_loser_room = True
            user.save()
            
            # 패잔병 토론방에 환영 메시지 추가
            Message.objects.create(
                user=user,
                stock_room=room,
                room_type='loser',
                content=f"{user.username}님이 패잔병 토론방에 입장했습니다."
            )
    
    def _handle_champion_stock(self, stock):
        """챔피언 종목 처리 (챔피언 배지 부여)"""
        try:
            room = stock.room
        except StockRoom.DoesNotExist:
            return
        
        # 모든 활성 멤버에게 챔피언 배지 부여
        memberships = StockRoomMembership.objects.filter(stock_room=room, is_kicked=False)
        for membership in memberships:
            user = membership.user
            user.champion_badge_count += 1
            user.bonus_points += 50  # 챔피언 보너스 포인트 지급
            user.save()
            
            # 축하 메시지 생성
            Message.objects.create(
                user=user,
                stock_room=room,
                room_type='stock',
                content=f"축하합니다! {user.username}님이 {stock.name} 종목의 챔피언이 되었습니다! (+50 포인트)"
            )


class StockRoomViewSet(viewsets.ModelViewSet):
    """종목 토론방 ViewSet"""
    queryset = StockRoom.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StockRoomDetailSerializer
        return StockRoomSerializer
    
    def get_permissions(self):
        """관리자만 토론방 생성/수정/삭제 가능"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """토론방 입장"""
        room = self.get_object()
        user = request.user
        
        # 토론방이 비활성화된 경우
        if not room.stock.is_active:
            return Response({"error": "이 토론방은 현재 비활성화되어 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미 토론방에 가입되어 있는지 확인
        membership = StockRoomMembership.objects.filter(user=user, stock_room=room).first()
        
        if membership:
            if membership.is_kicked:
                return Response({"error": "이 토론방에서 퇴출되어 입장할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "이미 토론방에 가입되어 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 새로운 멤버십 생성
        StockRoomMembership.objects.create(user=user, stock_room=room)
        
        # 환영 메시지 생성
        Message.objects.create(
            user=user, 
            stock_room=room,
            content=f"{user.username}님이 토론방에 입장했습니다."
        )
        
        return Response({"message": f"{room.title} 토론방에 입장했습니다."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """토론방 퇴장"""
        room = self.get_object()
        user = request.user
        
        # 가입 여부 확인
        membership = get_object_or_404(StockRoomMembership, user=user, stock_room=room, is_kicked=False)
        
        # 퇴장 메시지 생성
        Message.objects.create(
            user=user, 
            stock_room=room,
            content=f"{user.username}님이 토론방을 나갔습니다."
        )
        
        # 멤버십 삭제
        membership.delete()
        
        return Response({"message": f"{room.title} 토론방에서 퇴장했습니다."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loser_room(request):
    """패잔병 토론방 정보 조회"""
    user = request.user
    
    # 패잔병 토론방에 있는 유저 목록
    loser_users = User.objects.filter(is_in_loser_room=True)
    
    # 유저가 루저 배지를 가지고 있는지 확인
    is_loser = user.loser_badge_count > 0
    
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 50
    
    result_page = paginator.paginate_queryset(loser_users, request)
    from .serializers import SimpleUserSerializer
    serializer = SimpleUserSerializer(result_page, many=True)
    
    return paginator.get_paginated_response({
        "users": serializer.data,
        "is_loser": is_loser
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, room_id=None):
    """메시지 전송 API"""
    user = request.user
    content = request.data.get('content')
    room_type = request.data.get('room_type', 'stock')
    
    if not content:
        return Response({"error": "메시지 내용이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    # 루저 배지를 가진 유저의 메시지 제한 확인
    if not user.can_send_message:
        return Response(
            {"error": "루저 배지를 가진 유저는 1분에 한 번만 메시지를 보낼 수 있습니다."}, 
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # 메시지 생성 데이터 준비
    message_data = {
        'user': user,
        'content': content,
        'room_type': room_type
    }
    
    # 일반 토론방 메시지인 경우 방 ID 확인
    if room_type == 'stock' and room_id:
        room = get_object_or_404(StockRoom, id=room_id)
        
        # 방에 가입되어 있는지 확인
        membership = get_object_or_404(StockRoomMembership, user=user, stock_room=room, is_kicked=False)
        message_data['stock_room'] = room
    
    # 메시지 생성
    message = Message.objects.create(**message_data)
    
    # 유저 마지막 메시지 시간 업데이트
    user.last_message_time = timezone.now()
    user.save()
    
    serializer = MessageSerializer(message)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, room_id=None):
    """메시지 조회 API"""
    room_type = request.query_params.get('room_type', 'stock')
    
    if room_type == 'stock' and room_id:
        # 특정 종목 토론방 메시지 조회
        room = get_object_or_404(StockRoom, id=room_id)
        messages = Message.objects.filter(stock_room=room, room_type=room_type)
    elif room_type == 'loser':
        # 패잔병 토론방 메시지 조회
        messages = Message.objects.filter(room_type='loser')
    else:
        return Response({"error": "올바른 방 정보가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    # 페이지네이션
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 50
    
    result_page = paginator.paginate_queryset(messages, request)
    serializer = MessageSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)
