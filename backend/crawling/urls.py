from django.urls import path
from . import views

urlpatterns = [
    # 네이버 금융 관련 API 엔드포인트
    path('naver-finance-news/', views.naver_finance_news, name='naver_finance_news'),
    path('naver-finance-market/', views.naver_finance_market, name='naver_finance_market'),
    path('market-overview/', views.get_market_overview, name='market_overview'),
    path('market-news/', views.get_market_news, name='market_news'),
    
    # 새로 추가한 일별 시세 데이터 API 엔드포인트
    path('daily-index-data/', views.get_daily_index_data, name='daily_index_data'),
    path('supported-indices/', views.get_supported_indices, name='supported_indices'),
]
