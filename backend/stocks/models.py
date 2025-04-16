from django.db import models
from django.utils import timezone
# User 모델을 문자열 참조로 변경
# from accounts.models import User

class Stock(models.Model):
    """주식 종목 정보를 저장하는 모델"""
    symbol = models.CharField(max_length=20, unique=True)  # 종목 코드
    name = models.CharField(max_length=100)  # 종목명
    current_price = models.DecimalField(max_digits=12, decimal_places=2)  # 현재가
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)  # 매입가 (기준가)
    percentage_change = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # 등락률
    volume = models.BigIntegerField(default=0)  # 거래량
    is_active = models.BooleanField(default=True)  # 토론방 활성화 여부
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
    @property
    def is_champion(self):
        """챔피언 조건 (매입가 대비 20% 이상 상승) 확인"""
        return self.percentage_change >= 20
    
    @property
    def is_loser(self):
        """루저 조건 (매입가 대비 10% 이상 하락) 확인"""
        return self.percentage_change <= -10


class StockRoom(models.Model):
    """종목 토론방 모델"""
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, related_name='room')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # 문자열 참조로 변경
    members = models.ManyToManyField('accounts.User', through='StockRoomMembership', related_name='stock_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.stock.symbol}"


class StockRoomMembership(models.Model):
    """유저와 종목 토론방 간의 관계를 정의하는 모델"""
    # 문자열 참조로 변경
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    stock_room = models.ForeignKey(StockRoom, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_kicked = models.BooleanField(default=False)  # 퇴출 여부
    kicked_time = models.DateTimeField(null=True, blank=True)  # 퇴출 시간
    
    class Meta:
        unique_together = ('user', 'stock_room')
    
    def kick_user(self):
        """유저를 토론방에서 퇴출시키는 메서드"""
        self.is_kicked = True
        self.kicked_time = timezone.now()
        self.save()


class Message(models.Model):
    """채팅 메시지 모델"""
    ROOM_TYPES = (
        ('stock', '종목 토론방'),
        ('loser', '패잔병 토론방'),
    )
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    stock_room = models.ForeignKey(StockRoom, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='stock')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}{'...' if len(self.content) > 30 else ''}"


class Portfolio(models.Model):
    """사용자의 주식 포트폴리오를 저장하는 모델"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='portfolios')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username}'s {self.stock.name} portfolio"


class Transaction(models.Model):
    """주식 거래 내역을 저장하는 모델"""
    TRANSACTION_TYPES = (
        ('buy', '매수'),
        ('sell', '매도'),
    )

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.get_transaction_type_display()} of {self.stock.name}"

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.quantity * self.price
        super().save(*args, **kwargs)


class StockPriceHistory(models.Model):
    """주식 가격 변동 이력을 저장하는 모델"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    percentage_change = models.DecimalField(max_digits=6, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.stock.name} price at {self.timestamp}"
