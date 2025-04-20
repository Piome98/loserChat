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
from rest_framework import status

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
            logger.info(f"원자재 항목 수: {len(market_data['commodities'])}")
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
            'commodities': []
        }
        
        return JsonResponse(empty_data)

@api_view(['GET'])
def korean_index_daily_prices_view(request):
    """국내 주요 지수(KOSPI, KOSDAQ)의 일별 시세 데이터를 가져옵니다."""
    try:
        # 요청 파라미터에서 지수 코드 가져오기
        index_symbol = request.GET.get('symbol', '').upper()
        
        # 지수 코드 매핑
        index_code_map = {
            'KOSPI': 'KOSPI',   # 코스피
            'KS11': 'KOSPI',    # 코스피 (야후 파이낸스 코드)
            'KOSDAQ': 'KOSDAQ', # 코스닥
            'KQ11': 'KOSDAQ',   # 코스닥 (야후 파이낸스 코드)
        }
        
        # 코드 변환
        index_code = index_code_map.get(index_symbol)
        
        if not index_code:
            return Response(
                {"error": f"지원하지 않는 지수 심볼입니다: {index_symbol}. 지원되는 심볼: KOSPI, KS11, KOSDAQ, KQ11"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 일별 시세 크롤링
        daily_prices = utils.crawl_korean_index_daily_prices(index_code)
        
        if not daily_prices:
            return Response(
                {"error": f"{index_symbol} 일별 시세 데이터를 가져오지 못했습니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 응답 데이터 구성
        response_data = {
            "symbol": index_symbol,
            "name": f"{index_code} 지수",
            "data": daily_prices
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"국내 지수 일별 시세 조회 오류: {str(e)}")
        logger.exception("상세 오류:")
        return Response(
            {"error": "일별 시세 데이터를 처리하는 중 오류가 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
