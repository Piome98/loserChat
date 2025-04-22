from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone
from .models import NewsArticle, MarketIndex
from .utils import crawl_news_from_investing, crawl_market_indices, fetch_news_by_symbol, crawl_naver_finance_news, crawl_naver_market_indices
import logging
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
import random
import time
import json
import re
import pandas as pd
from datetime import datetime, timedelta

# index_crawler에서 필요한 함수 임포트
try:
    from .index_crawler import crawl_index_daily_price, YAHOO_GLOBAL_INDEX_CODE_MAP, crawl_global_index_data, NAVER_GLOBAL_INDEX_SYMBOLS, crawl_naver_global_index, get_index_name, crawl_commodity_data, crawl_currency_data
except ImportError:
    # 개발 환경에서 임시 Mock 함수 구현
    def crawl_index_daily_price(index_code='KOSPI', pages=1):
        return pd.DataFrame()
    YAHOO_GLOBAL_INDEX_CODE_MAP = {}
    NAVER_GLOBAL_INDEX_SYMBOLS = {}
    def crawl_global_index_data(index_code, days=30):
        return pd.DataFrame()
    def crawl_naver_global_index(index_code, days=30):
        return pd.DataFrame()
    def get_index_name(code):
        return code
    def crawl_commodity_data(code, days=30):
        return None
    def crawl_currency_data(code, days=30):
        return None

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_market_overview(request):
    """시장 개요 데이터 가져오기"""
    try:
        # 캐싱 키
        cache_key = 'market_overview_data'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # 최신 시장 지수 가져오기
        indices = MarketIndex.objects.all()
        
        # 데이터가 없거나 오래된 경우 크롤링 실행
        if not indices.exists() or (timezone.now() - indices.first().updated_at).total_seconds() > 300:
            try:
                crawl_market_indices()
                indices = MarketIndex.objects.all()
            except Exception as e:
                logger.error(f"시장 개요 크롤링 오류: {str(e)}")
        
        # 응답 데이터 구성
        indices_data = []
        for idx in indices:
            indices_data.append({
                'name': idx.name,
                'symbol': idx.symbol,
                'price': str(idx.price),
                'change': str(idx.change),
                'changePercent': f"{idx.change_percent}%"
            })
        
        result = {
            'updateTime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': indices_data
        }
        
        # 결과 캐싱 (5분)
        cache.set(cache_key, result, 300)
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"시장 개요 데이터 가져오기 오류: {str(e)}")
        return Response({
            'error': '시장 데이터를 가져오는 중 오류가 발생했습니다.'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_market_news(request):
    """뉴스 데이터 가져오기"""
    try:
        symbol = request.GET.get('symbol', None)
        
        # 캐싱 키 (종목 심볼에 따라 다른 캐시 키 사용)
        cache_key = f'market_news_data_{symbol}' if symbol else 'market_news_data_all'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # 뉴스 데이터 가져오기
        if symbol:
            # 종목별 뉴스
            news_items = NewsArticle.objects.filter(related_symbols__contains=[symbol]).order_by('-published_at')[:10]
            
            # 데이터가 없거나 오래된 경우 크롤링 실행
            if not news_items.exists() or (timezone.now() - news_items.first().created_at).total_seconds() > 1800:  # 30분
                try:
                    fetch_news_by_symbol(symbol)
                    news_items = NewsArticle.objects.filter(related_symbols__contains=[symbol]).order_by('-published_at')[:10]
                except Exception as e:
                    logger.error(f"종목 뉴스 크롤링 오류: {str(e)}")
        else:
            # 일반 뉴스
            news_items = NewsArticle.objects.all().order_by('-published_at')[:15]
            
            # 데이터가 없거나 오래된 경우 크롤링 실행
            if not news_items.exists() or (timezone.now() - news_items.first().created_at).total_seconds() > 1800:  # 30분
                try:
                    crawl_news_from_investing()
                    news_items = NewsArticle.objects.all().order_by('-published_at')[:15]
                except Exception as e:
                    logger.error(f"일반 뉴스 크롤링 오류: {str(e)}")
        
        # 응답 데이터 구성
        news_data = []
        for item in news_items:
            news_data.append({
                'id': item.id,
                'title': item.title,
                'summary': item.content_summary,
                'source': item.source,
                'date': item.published_at.strftime('%Y-%m-%d %H:%M'),
                'url': item.url,
                'category': item.category,
                'imageUrl': item.image_url,
                'relatedSymbols': item.related_symbols
            })
        
        # 결과 캐싱 (10분)
        cache.set(cache_key, news_data, 600)
        
        return Response(news_data)
    
    except Exception as e:
        logger.error(f"뉴스 데이터 가져오기 오류: {str(e)}")
        return Response({
            'error': '뉴스 데이터를 가져오는 중 오류가 발생했습니다.'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def naver_finance_news(request):
    try:
        # 캐싱 키
        stock_symbol = request.GET.get('symbol')
        cache_key = f'naver_finance_news_{stock_symbol}' if stock_symbol else 'naver_finance_news_all'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return JsonResponse(cached_data, safe=False)
        
        # 네이버 금융 뉴스 크롤링
        news_data = crawl_naver_finance_news(symbol=stock_symbol, max_news=15)
        
        # 데이터가 비어있는 경우 재시도
        if not news_data:
            logger.warning("첫 번째 시도에서 뉴스를 찾지 못했습니다. 재시도합니다.")
            time.sleep(1)  # 잠시 기다렸다가 재시도
            news_data = crawl_naver_finance_news(symbol=stock_symbol, max_news=15)
        
        # 결과 캐싱 (5분)
        if news_data:  # 빈 리스트가 아닌 경우에만 캐싱
            cache.set(cache_key, news_data, 300)
        
        logger.info(f"네이버 금융 뉴스 로드됨: {len(news_data)}개")
        return JsonResponse(news_data, safe=False)
        
    except Exception as e:
        logger.error(f"네이버 금융 뉴스 크롤링 오류: {str(e)}")
        return JsonResponse([], safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # 인증 문제가 있다면 일시적으로 주석 처리하여 테스트
def naver_finance_market(request):
    try:
        # 요청 헤더에 Accept: application/json 추가 확인
        logger.info(f"Accept 헤더: {request.headers.get('Accept', '')}")
        
        # 캐싱 키
        cache_key = 'naver_finance_market_data'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info("캐시된 시장 데이터 사용")
            return JsonResponse(cached_data)
        
        # 네이버 금융 시장 데이터 크롤링
        logger.info("네이버 금융 시장 데이터 크롤링 시작")
        indices_data = crawl_naver_market_indices()
        
        # 데이터가 비어있는 경우 재시도
        if not indices_data:
            logger.warning("첫 번째 시도에서 시장 데이터를 찾지 못했습니다. 재시도합니다.")
            time.sleep(1)  # 잠시 기다렸다가 재시도
            indices_data = crawl_naver_market_indices()
        
        # 결과 데이터 구성
        market_data = {
            'updateTime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': [],
            'currencies': [],
            'commodities': []
        }
        
        # 데이터 분류
        for item in indices_data:
            symbol = item.get('symbol', '').lower()
            
            # 상태 및 변화율 형식 조정
            status = item.get('status', 'unchanged')
            change = item.get('change', '0')
            change_str = f"+{change}" if status == 'up' else f"-{change}" if status == 'down' else change
            
            percent = item.get('change_percent', '0')
            percent_str = f"{percent}%"
            
            result_item = {
                'name': item.get('name', ''),
                'price': item.get('price', '0'),
                'change': change_str,
                'changePercent': f"{'+' if status == 'up' else '-' if status == 'down' else ''}{percent_str}",
                'status': status
            }
            
            # 카테고리별 분류 - 로깅 추가
            if 'krw' in symbol and symbol.startswith('krw-'):
                market_data['currencies'].append(result_item)
                logger.info(f"환율 항목 추가: {item.get('name', '')}, 심볼: {symbol}")
            elif 'wti' in symbol or 'oil' in symbol or 'gold' in symbol:
                market_data['commodities'].append(result_item)
            else:
                market_data['indices'].append(result_item)
        
        # 결과 캐싱 (5분)
        if indices_data:
            logger.info(f"시장 데이터 캐싱 (항목 수: {len(indices_data)})")
            logger.info(f"환율 항목 수: {len(market_data['currencies'])}")
            logger.info(f"지수 항목 수: {len(market_data['indices'])}")
            cache.set(cache_key, market_data, 300)
        
        logger.info(f"네이버 금융 시장 데이터 로드 완료: {len(indices_data)}개 항목")
        return JsonResponse(market_data)
        
    except Exception as e:
        logger.error(f"네이버 금융 시장 데이터 API 오류: {str(e)}")
        logger.exception("상세 오류:")
        
        # 오류 시 빈 구조 반환
        empty_data = {
            'updateTime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': [],
            'currencies': [],

        }
        
        return JsonResponse(empty_data)

@api_view(['GET'])
def get_daily_index_data(request):
    """
    지수/원자재/환율 일별 시세 데이터를 제공하는 API 엔드포인트
    
    파라미터:
    - code: 코드 (필수, 예: KOSPI, KOSDAQ, WTI, USD/KRW 등)
    - days: 가져올 일 수 (선택, 기본값: 30)
    - page: 페이지 번호 (선택, 기본값: 1)
    """
    try:
        # 파라미터 가져오기
        code = request.GET.get('code')
        days = int(request.GET.get('days', 30))
        page = int(request.GET.get('page', 1))
        
        # 코드가 없으면 에러
        if not code:
            return Response({
                'error': '코드(code) 파라미터가 필요합니다.'
            }, status=400)
        
        # 캐싱 키 생성
        cache_key = f'daily_index_{code}_{days}_page{page}'
        cached_data = cache.get(cache_key)
        
        # 캐시된 데이터가 있으면 반환
        if cached_data:
            logger.info(f"캐시된 {code} 데이터 사용")
            return Response(cached_data)
            
        # 일별 지수 데이터 크롤링
        logger.info(f"{code} 일별 시세 데이터 크롤링 시작")
        
        # 코드 종류에 따라 처리
        data = None
        
        # 지원되는 코드 목록
        supported_indices = ['KOSPI', 'KOSDAQ', 'KPI200', 'DJI', 'NASDAQ', 'SP500', 'HSI']
        supported_commodities = ['WTI', 'GOLD', 'SILVER']
        supported_currencies = ['USD/KRW', 'JPY/KRW', 'EUR/KRW', 'CNY/KRW']
        
        # 국내 지수 또는 해외 지수인 경우
        if code in supported_indices:
            try:
                # 국내 지수: 일별 시세 크롤링 (네이버 금융)
                if code in ['KOSPI', 'KOSDAQ', 'KPI200']:
                    # 최대 페이지 수는 days 기반으로 계산
                    pages_to_crawl = min(5, (days + 9) // 10)  # 대략 한 페이지당 10일치 데이터라고 가정
                    df = crawl_index_daily_price(index_code=code, pages=pages_to_crawl)
                # 해외 지수: 네이버 금융 우선, 야후 파이낸스 대체
                else:
                    # 네이버 금융에서 데이터 가져오기 시도
                    if code in NAVER_GLOBAL_INDEX_SYMBOLS:
                        df = crawl_naver_global_index(code, days=days)
                    
                    # 네이버 금융에서 데이터를 가져오지 못했거나 지원하지 않는 코드인 경우 야후 파이낸스 시도
                    if df is None or df.empty:
                        if code in YAHOO_GLOBAL_INDEX_CODE_MAP:
                            df = crawl_global_index_data(code, days=days)
                        else:
                            logger.error(f"지원되지 않는 지수 코드: {code}")
                            return Response({
                                'error': f"지원되지 않는 지수 코드입니다: {code}"
                            }, status=400)
                
                if not df.empty:
                    # 날짜 형식 변환
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    
                    # 데이터 포맷팅
                    data = {
                        'code': code,
                        'name': get_index_name(code),
                        'data': df.to_dict('records'),
                        'total_count': len(df),
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            except Exception as e:
                logger.error(f"{code} 데이터 크롤링 오류: {str(e)}")
        
        
        # 환율의 경우
        elif code in supported_currencies:
            data = crawl_currency_data(code, days)
            
        else:
            # 지원되지 않는 코드인 경우
            return Response({
                'error': f"지원되지 않는 코드입니다: {code}",
                'supported_codes': {
                    'indices': supported_indices,
                    'commodities': supported_commodities,
                    'currencies': supported_currencies
                }
            }, status=400)
        
        # 데이터가 없으면 에러
        if not data:
            return Response({
                'error': f"{code} 데이터를 가져오는 중 오류가 발생했습니다."
            }, status=500)
        
        # 결과 캐싱 (1시간)
        cache.set(cache_key, data, 3600)
        
        return Response(data)
        
    except Exception as e:
        logger.error(f"일별 시세 데이터 요청 처리 오류: {str(e)}")
        return Response({
            'error': '데이터를 가져오는 중 오류가 발생했습니다.',
            'details': str(e)
        }, status=500)

@api_view(['GET'])
def get_supported_indices(request):
    """지원되는 지수, 원자재, 환율 코드 목록을 반환"""
    return Response({
        'indices': [
            {'code': 'KOSPI', 'name': '코스피'},
            {'code': 'KOSDAQ', 'name': '코스닥'},
            {'code': 'KPI200', 'name': '코스피 200'},
            {'code': 'DJI', 'name': '다우존스 산업평균지수'},
            {'code': 'NASDAQ', 'name': '나스닥 종합지수'},
            {'code': 'SP500', 'name': 'S&P 500'},
            {'code': 'HSI', 'name': '항셍지수'}
        ],
     
        'currencies': [
            {'code': 'USD/KRW', 'name': '원/달러'},
            {'code': 'JPY/KRW', 'name': '원/엔'},
            {'code': 'EUR/KRW', 'name': '원/유로'},
            {'code': 'CNY/KRW', 'name': '원/위안'}
        ]
    })
