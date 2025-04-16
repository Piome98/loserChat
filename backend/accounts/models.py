from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser): # USER 객체 생성
    nickname = models.CharField(max_length=30, blank=True)
    loser_badge_count = models.IntegerField(default=0)
    champion_badge_count = models.IntegerField(default=0)  # 챔피언 배지 카운트 추가
    bonus_points = models.IntegerField(default=0)
    last_game_played = models.DateField(null=True, blank=True)
    last_message_time = models.DateTimeField(null=True, blank=True)  # 마지막 메시지 작성 시간
    selected_theme = models.CharField(max_length=20, default='default_theme')
    unlocked_themes = models.JSONField(default=list)  # ["dark", "neon", ...]
    is_in_loser_room = models.BooleanField(default=False)  # 패잔병 토론방에 있는지 여부

    def __str__(self):
        return self.username

    @property
    def can_send_message(self):
        """
        루저 배지가 있는 유저의 메시지 제한 확인
        1분에 1회만 메시지 전송 가능
        """
        from django.utils import timezone
        import datetime
        
        if self.loser_badge_count == 0 or not self.last_message_time:
            return True
            
        time_diff = timezone.now() - self.last_message_time
        return time_diff > datetime.timedelta(minutes=1)

# UserStock 모델은 별도의 파일에 정의하는 것이 좋지만, 
# 지연 임포트(lazy import)를 사용하여 임시로 해결
class UserStock(models.Model):
    """사용자가 보유한 종목 정보 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_stocks')
    # 지연 임포트를 위해 문자열로 모델 참조
    stock = models.ForeignKey('stocks.Stock', on_delete=models.CASCADE)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2)  # 매수가
    target_price = models.DecimalField(max_digits=12, decimal_places=2)  # 목표가
    quantity = models.IntegerField(default=1)  # 보유 수량
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'stock')
        
    def __str__(self):
        return f"{self.user.username}의 {self.stock.name} 보유 정보"
