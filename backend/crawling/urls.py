from django.urls import path
from . import views
from .views import (
    get_market_overview, get_market_news, naver_finance_news, 
    get_market_gainers_losers, get_market_sectors, get_market_cap_dist, 
    naver_finance_detail, daily_prices_view, korean_index_daily_prices_view
)

urlpatterns = [
    # 네이버 금융 관련 API 엔드포인트
    path('naver-finance-news/', naver_finance_news, name='naver_finance_news'),
    path('naver-finance-market/', views.naver_finance_market, name='naver_finance_market'),
    path('market-overview/', get_market_overview, name='market_overview'),
    path('market-news/', get_market_news, name='market_news'),
    path('market-gainers-losers/', get_market_gainers_losers, name='market_gainers_losers'),
    path('market-sectors/', get_market_sectors, name='market_sectors'),
    path('market-cap-dist/', get_market_cap_dist, name='market_cap_dist'),
    path('stock-detail/', naver_finance_detail, name='naver_finance_detail'),
    path('daily-prices/', daily_prices_view, name='daily_prices'),
    path('korean-index-prices/', korean_index_daily_prices_view, name='korean_index_daily_prices'),
]
