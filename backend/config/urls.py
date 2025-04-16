# config/urls.py
# 프로젝트 전체 url 라우팅 처리


from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/game/', include('game.urls')),
    path('api/stocks/', include('stocks.urls')),
    path('api/chats/', include('chats.urls')),
    path('api/crawling/', include('crawling.urls')),
]
