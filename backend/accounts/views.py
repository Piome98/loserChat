# accounts/views.py
# 회원가입 API View 

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer
from django.contrib.auth import get_user_model
from stocks.models import Stock
from accounts.models import User, UserStock  # UserStock 임포트 추가

User = get_user_model()

@api_view(['POST'])
def signup_view(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "회원가입 성공"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    data = {
        "username": user.username,
        "nickname": user.nickname,
        "bonus_points": user.bonus_points,
        "loser_badge_count": user.loser_badge_count,
        "selected_theme": user.selected_theme,
        "unlocked_themes": user.unlocked_themes}
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_loser_badge(request):
    user = request.user
    if user.bonus_points >= 50 and user.loser_badge_count > 0:
        user.bonus_points -= 50
        user.loser_badge_count -= 1
        user.save()
        return Response({
            'message': '루저 딱지 1개가 제거되었습니다!',
            'remaining_badges': user.loser_badge_count,
            'remaining_points': user.bonus_points
        })
    return Response({
        'error': '포인트가 부족하거나 제거할 딱지가 없습니다.'
    }, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_loser_badge(request):
    """다른 사용자에게 루저 배지 전달하기 (보너스 포인트 소모)"""
    user = request.user
    target_username = request.data.get('username')
    
    # 타겟 유저 확인
    try:
        target_user = User.objects.get(username=target_username)
    except User.DoesNotExist:
        return Response({"error": "존재하지 않는 사용자입니다."}, status=400)
    
    # 자기 자신에게 전달 불가
    if target_user == user:
        return Response({"error": "자기 자신에게 루저 배지를 전달할 수 없습니다."}, status=400)
    
    # 포인트 확인 (루저 배지 제거의 3배)
    required_points = 150
    
    if user.bonus_points < required_points:
        return Response({"error": f"포인트가 부족합니다. (필요: {required_points}, 보유: {user.bonus_points})"}, status=400)
    
    # 포인트 차감 및 배지 전달
    user.bonus_points -= required_points
    target_user.loser_badge_count += 1
    
    user.save()
    target_user.save()
    
    return Response({
        "message": f"{target_user.username}님에게 루저 배지를 전달했습니다!",
        "remaining_points": user.bonus_points
    })


# USER 커스터마이징 관련 API View
# 각각의 커스터마이징 이미지 및 이펙트 추가 필요
CUSTOMIZATION_STORE = {
    "dark": 30,
    "neon": 50,
    "cute": 80,
    "cyberpunk": 100,
}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def customization_theme(request):
    user = request.user
    theme = request.data.get("theme")

    if theme not in CUSTOMIZATION_STORE:
        return Response({"error": "존재하지 않는 테마입니다."}, status=400)

    price = CUSTOMIZATION_STORE[theme]

    if theme not in user.unlocked_themes:
        if user.bonus_points < price:
            return Response({"error": "보너스 포인트가 부족합니다."}, status=403)
        user.bonus_points -= price
        user.unlocked_themes.append(theme)

    user.selected_theme = theme
    user.save()

    return Response({
        "message": f"'{theme}' 테마가 적용되었습니다!",
        "selected_theme": user.selected_theme,
        "remaining_points": user.bonus_points
    })

# 사용자 프로필 조회 (포인트 사용)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def view_user_profile(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
        current_user = request.user
        
        # 자기 자신의 프로필은 무료로 볼 수 있음
        if current_user.id == target_user.id:
            # 보유 종목 데이터 가져오기
            stocks = UserStock.objects.filter(user=target_user)
            stock_data = [
                {
                    'name': stock.stock.name,
                    'buy_price': stock.buy_price,
                    'target_price': stock.target_price,
                    'quantity': stock.quantity
                } 
                for stock in stocks
            ]
            
            user_data = {
                'id': target_user.id,
                'username': target_user.username,
                'nickname': target_user.nickname,
                'bonus_points': target_user.bonus_points,
                'loser_badge_count': target_user.loser_badge_count,
                'champion_badge_count': target_user.champion_badge_count,
                'stocks': stock_data
            }
            
            return Response(user_data)
        
        # 포인트 확인
        if current_user.bonus_points < 20:
            return Response(
                {"error": "포인트가 부족합니다. 미니게임에서 포인트를 획득해주세요."}, 
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # 포인트 차감
        current_user.bonus_points -= 20
        current_user.save()
        
        # 보유 종목 데이터 가져오기
        stocks = UserStock.objects.filter(user=target_user)
        stock_data = [
            {
                'name': stock.stock.name,
                'buy_price': stock.buy_price,
                'target_price': stock.target_price,
                'quantity': stock.quantity
            } 
            for stock in stocks
        ]
        
        user_data = {
            'id': target_user.id,
            'username': target_user.username,
            'nickname': target_user.nickname,
            'bonus_points': target_user.bonus_points,
            'loser_badge_count': target_user.loser_badge_count,
            'champion_badge_count': target_user.champion_badge_count,
            'stocks': stock_data
        }
        
        return Response(user_data)
        
    except User.DoesNotExist:
        return Response({"error": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 사용자 보유 종목 조회 (자신의 것만)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stocks(request, user_id):
    try:
        # 요청한 사용자가 자신의 정보만 볼 수 있도록 검증
        if int(user_id) != request.user.id:
            return Response({"error": "자신의 정보만 볼 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        # UserStock 모델이 없는 경우 임시 데이터 반환
        from django.db import ProgrammingError
        try:
            stocks = UserStock.objects.filter(user_id=user_id)
            stock_data = [
                {
                    'name': stock.stock.name,
                    'buy_price': stock.buy_price,
                    'target_price': stock.target_price,
                    'quantity': stock.quantity
                } 
                for stock in stocks
            ]
        except (ImportError, ProgrammingError):
            # 임시 데이터 반환
            stock_data = [
                {
                    'name': '삼성전자',
                    'buy_price': 68000,
                    'target_price': 75000,
                    'quantity': 10
                },
                {
                    'name': 'LG전자',
                    'buy_price': 122000,
                    'target_price': 150000,
                    'quantity': 5
                },
                {
                    'name': '네이버',
                    'buy_price': 284000,
                    'target_price': 320000,
                    'quantity': 3
                }
            ]
        
        return Response({"stocks": stock_data})
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)