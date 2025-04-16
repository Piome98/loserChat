from django.urls import path
from . import views

urlpatterns = [
    # 네이버 금융 관련 API 엔드포인트
    path('naver-finance-news/', views.naver_finance_news, name='naver_finance_news'),
    path('naver-finance-market/', views.naver_finance_market, name='naver_finance_market'),
]
