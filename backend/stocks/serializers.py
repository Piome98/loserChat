from rest_framework import serializers
from .models import Stock, StockRoom, StockRoomMembership, Message, Portfolio, Transaction
from accounts.models import User

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class SimpleUserSerializer(serializers.ModelSerializer):
    """간단한 유저 정보만 포함하는 시리얼라이저"""
    has_loser_badge = serializers.SerializerMethodField()
    has_champion_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'has_loser_badge', 'has_champion_badge', 'selected_theme')
    
    def get_has_loser_badge(self, obj):
        return obj.loser_badge_count > 0
    
    def get_has_champion_badge(self, obj):
        return obj.champion_badge_count > 0


class StockRoomSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StockRoom
        fields = ('id', 'title', 'description', 'stock', 'created_at', 'member_count')
    
    def get_member_count(self, obj):
        return obj.members.filter(stockroommembership__is_kicked=False).count()


class StockRoomDetailSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = StockRoom
        fields = ('id', 'title', 'description', 'stock', 'created_at', 'members')
    
    def get_members(self, obj):
        active_members = obj.members.filter(stockroommembership__is_kicked=False)
        return SimpleUserSerializer(active_members, many=True).data


class MessageSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'user', 'content', 'room_type', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # 루저 배지가 있는 유저의 메시지 제한 확인
        if not user.can_send_message:
            raise serializers.ValidationError("루저 배지를 가진 유저는 1분에 한 번만 메시지를 보낼 수 있습니다.")
        
        # 메시지 생성 시 유저의 마지막 메시지 시간 업데이트
        from django.utils import timezone
        user.last_message_time = timezone.now()
        user.save()
        
        return super().create(validated_data)


class PortfolioSerializer(serializers.ModelSerializer):
    """사용자의 포트폴리오 시리얼라이저"""
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(
        queryset=Stock.objects.all(), write_only=True, source='stock'
    )
    current_value = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = (
            'id', 'stock', 'stock_id', 'quantity', 'average_price', 
            'current_value', 'profit_loss', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_current_value(self, obj):
        return float(obj.stock.current_price) * obj.quantity
    
    def get_profit_loss(self, obj):
        current_value = float(obj.stock.current_price) * obj.quantity
        invested_value = float(obj.average_price) * obj.quantity
        return current_value - invested_value


class TransactionSerializer(serializers.ModelSerializer):
    """주식 거래 내역 시리얼라이저"""
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(
        queryset=Stock.objects.all(), write_only=True, source='stock'
    )
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'user', 'stock', 'stock_id', 'transaction_type', 
            'transaction_type_display', 'quantity', 'price', 
            'total_amount', 'created_at'
        )
        read_only_fields = ('id', 'user', 'total_amount', 'created_at')
    
    def create(self, validated_data):
        # 요청한 사용자를 거래 내역에 저장
        validated_data['user'] = self.context['request'].user
        
        # 총 거래 금액 계산
        price = validated_data.get('price')
        quantity = validated_data.get('quantity')
        validated_data['total_amount'] = price * quantity
        
        return super().create(validated_data) 