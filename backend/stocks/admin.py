from django.contrib import admin
from .models import Stock, StockRoom, StockRoomMembership, Message

class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'purchase_price', 'percentage_change', 'is_active')
    search_fields = ('symbol', 'name')
    list_filter = ('is_active',)

class StockRoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'stock', 'created_at')
    search_fields = ('title', 'stock__name', 'stock__symbol')

class StockRoomMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock_room', 'joined_at', 'is_kicked')
    search_fields = ('user__username', 'stock_room__title')
    list_filter = ('is_kicked',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room_type', 'content_preview', 'created_at')
    search_fields = ('user__username', 'content')
    list_filter = ('room_type',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = '메시지 내용'

admin.site.register(Stock, StockAdmin)
admin.site.register(StockRoom, StockRoomAdmin)
admin.site.register(StockRoomMembership, StockRoomMembershipAdmin)
admin.site.register(Message, MessageAdmin)
