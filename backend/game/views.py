# game/views.py
# 게임 관련 API View -> 가위 바위 보 게임 / 

import random
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

choices = ['rock', 'paper', 'scissors']
beats = {
    'rock': 'scissors',
    'scissors': 'paper',
    'paper': 'rock'
}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_rock_scissors_papers(request):
    user = request.user
    user_choice = request.data.get('choice')
    bot_choice = random.choice(choices)
    today = timezone.localdate()

    # 하루 한번만 게임 가능
    if user.last_game_played == today:
        return Response({'error': 'You can only play once a day.'}, status=400)

    # 가위 바위 보 승리 조건:
    if user_choice not in choices:
        return Response({'error': 'Invalid choice. Use rock, paper, or scissors.'}, status=400)

    if beats[user_choice] == bot_choice:
        result = 'win'
        user.bonus_points += 10
        user.save()
    elif user_choice == bot_choice:
        result = 'draw'
    else:
        result = 'lose'

    # 게임 결과 저장
    user.last_game_played = today
    user.save()

    return Response({
        'user_choice': user_choice,
        'bot_choice': bot_choice,
        'result': result,
        'bonus_points': user.bonus_points
    })


# 한국투자증권 API 연동 (가상)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_top_volume_stocks(request):
    """거래량 상위 종목을 가져오는 API (관리자용)"""
    # 실제로는 한국투자증권 API를 호출해야 함
    # 이 예제에서는 가상의 데이터 사용
    
    # 가상의 종목 데이터
    mock_stocks = [
        {"symbol": "005930", "name": "삼성전자", "price": 68800, "volume": 8542301, "change_rate": 1.25},
        {"symbol": "000660", "name": "SK하이닉스", "price": 143000, "volume": 3251478, "change_rate": 0.85},
        {"symbol": "035720", "name": "카카오", "price": 56800, "volume": 2154789, "change_rate": -0.53},
        {"symbol": "005380", "name": "현대차", "price": 187500, "volume": 1985632, "change_rate": 2.12},
        {"symbol": "051910", "name": "LG화학", "price": 508000, "volume": 1654123, "change_rate": 3.04},
        {"symbol": "035420", "name": "NAVER", "price": 215000, "volume": 1548972, "change_rate": -1.25},
        {"symbol": "068270", "name": "셀트리온", "price": 169500, "volume": 1325487, "change_rate": 0.59},
        {"symbol": "105560", "name": "KB금융", "price": 58700, "volume": 1254893, "change_rate": 0.17},
        {"symbol": "055550", "name": "신한지주", "price": 38800, "volume": 1154789, "change_rate": 0.26},
        {"symbol": "012330", "name": "현대모비스", "price": 219500, "volume": 1087421, "change_rate": 1.85},
    ]
    
    # 조건 필터링 (예: 등락률 1% 이상)
    change_rate_threshold = float(request.query_params.get('change_rate', 0))
    filtered_stocks = [
        stock for stock in mock_stocks 
        if stock["change_rate"] >= change_rate_threshold
    ]
    
    return Response({
        "stocks": filtered_stocks,
        "timestamp": timezone.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_stock_to_room(request):
    """종목을 토론방에 추가하는 API (관리자용)"""
    symbol = request.data.get('symbol')
    name = request.data.get('name')
    price = request.data.get('price')
    
    if not all([symbol, name, price]):
        return Response({"error": "종목 코드, 이름, 가격이 필요합니다."}, status=400)
    
    try:
        price = float(price)
    except ValueError:
        return Response({"error": "가격은 숫자여야 합니다."}, status=400)
    
    # 종목 생성 또는 업데이트
    from stocks.models import Stock, StockRoom
    
    stock, created = Stock.objects.get_or_create(
        symbol=symbol,
        defaults={
            "name": name,
            "current_price": price,
            "purchase_price": price,
            "volume": 0
        }
    )
    
    if not created:
        # 기존 종목 정보 업데이트
        stock.name = name
        stock.current_price = price
        stock.save()
    
    # 토론방이 없으면 생성
    room, room_created = StockRoom.objects.get_or_create(
        stock=stock,
        defaults={
            "title": f"{name} ({symbol}) 토론방",
            "description": f"{name} 종목에 대한 토론방입니다."
        }
    )
    
    status_text = "생성됨" if created else "업데이트됨"
    room_text = "새로 생성됨" if room_created else "이미 존재함"
    
    return Response({
        "message": f"종목이 {status_text}",
        "stock_id": stock.id,
        "room_id": room.id,
        "room_status": room_text
    })

