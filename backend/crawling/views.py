from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone
from .models import NewsArticle, MarketIndex
from .utils import crawl_news_from_investing, crawl_market_indices, fetch_news_by_symbol
import logging
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
import random
import time
import json
import re

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
        # 다양한 User-Agent 설정
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        
        # 헤더 설정
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
        
        # 주식 종목 코드 (요청에 있는 경우)
        stock_symbol = request.GET.get('symbol')
        
        if stock_symbol:
            # 종목별 뉴스 URL
            url = f'https://finance.naver.com/item/news_news.naver?code={stock_symbol}&page=1'
        else:
            # 경제 뉴스 URL
            url = 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258'
        
        # 지연 시간 추가
        time.sleep(random.uniform(0.2, 0.5))
        
        # 요청 보내기
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # 응답 인코딩 설정 (네이버는 EUC-KR 인코딩 사용)
        response.encoding = 'euc-kr'
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = []
        
        if stock_symbol:
            # 종목별 뉴스 파싱 (예: 네이버 금융 종목별 뉴스 페이지)
            news_items = soup.select('tbody tr')
            
            for idx, item in enumerate(news_items, 1):
                try:
                    if 'relation_lst' in item.get('class', []):
                        continue
                    
                    title_elem = item.select_one('td.title a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = 'https://finance.naver.com' + title_elem['href']
                    
                    info_elems = item.select('td.info')
                    source = info_elems[0].text.strip() if info_elems else '알 수 없음'
                    date = info_elems[1].text.strip() if len(info_elems) > 1 else '알 수 없음'
                    
                    result.append({
                        'id': idx,
                        'title': title,
                        'summary': '',  # 요약은 별도로 가져와야 함
                        'source': source,
                        'date': date,
                        'url': link,
                        'category': '기업',
                        'imageUrl': None,
                        'relatedSymbols': [stock_symbol]
                    })
                    
                    if len(result) >= 10:
                        break
                        
                except Exception as e:
                    print(f"개별 뉴스 파싱 오류: {e}")
                    continue
        else:
            # 경제 뉴스 파싱 (네이버 금융 경제 뉴스 페이지)
            news_items = soup.select('.newslist li, .realtimeNewsList li')
            
            for idx, item in enumerate(news_items, 1):
                try:
                    title_elem = item.select_one('a.articleSubject, .articleSubject a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    # 상대 경로를 절대 URL로 변환
                    link_path = title_elem['href']
                    if link_path.startswith('/'):
                        link = 'https://finance.naver.com' + link_path
                    else:
                        link = link_path
                    
                    # 간단한 요약 정보 (있는 경우)
                    summary_elem = item.select_one('.articleSummary')
                    summary = summary_elem.text.strip() if summary_elem else ''
                    
                    # 출처와 날짜 정보 (있는 경우)
                    source_elem = item.select_one('.press')
                    source = source_elem.text.strip() if source_elem else '네이버 금융'
                    
                    date_elem = item.select_one('.wdate')
                    date = date_elem.text.strip() if date_elem else time.strftime('%Y.%m.%d')
                    
                    result.append({
                        'id': idx,
                        'title': title,
                        'summary': summary,
                        'source': source,
                        'date': date,
                        'url': link,
                        'category': '경제',
                        'imageUrl': None,
                        'relatedSymbols': []
                    })
                    
                    if len(result) >= 10:
                        break
                        
                except Exception as e:
                    print(f"개별 뉴스 파싱 오류: {e}")
                    continue
        
        return JsonResponse(result, safe=False)
        
    except Exception as e:
        print(f"네이버 금융 뉴스 크롤링 오류: {e}")
        return JsonResponse([], safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def naver_finance_market(request):
    try:
        # 다양한 User-Agent 설정
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        
        # 헤더 설정
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
        
        # 네이버 금융 홈페이지 URL
        url = 'https://finance.naver.com/'
        
        # 요청 보내기
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # 응답 인코딩 설정 (네이버는 EUC-KR 인코딩 사용)
        response.encoding = 'euc-kr'
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 결과 데이터 초기화
        result = {
            'updateTime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'indices': [],
            'currencies': [],
            'commodities': []
        }
        
        # 주가 지수 추출 (KOSPI, KOSDAQ)
        indices_data = []
        
        kospi_area = soup.select_one('.kospi_area')
        if kospi_area:
            price_elem = kospi_area.select_one('.num')
            change_elem = kospi_area.select_one('.num_s')
            
            if price_elem and change_elem:
                price = price_elem.text.strip()
                change_text = change_elem.text.strip()
                
                # 상승/하락 판단
                status = 'up' if '상승' in change_text else 'down' if '하락' in change_text else 'unchanged'
                
                # 변화량과 변화율 추출
                change_match = re.search(r'([0-9.]+)', change_text)
                percent_match = re.search(r'([0-9.]+)%', change_text)
                
                change = change_match.group(1) if change_match else '0.00'
                percent = percent_match.group(1) if percent_match else '0.00'
                
                sign = '+' if status == 'up' else '-' if status == 'down' else ''
                
                indices_data.append({
                    'name': 'KOSPI',
                    'price': price,
                    'change': f'{sign}{change}',
                    'changePercent': f'{sign}{percent}%',
                    'status': status
                })
        
        kosdaq_area = soup.select_one('.kosdaq_area')
        if kosdaq_area:
            price_elem = kosdaq_area.select_one('.num')
            change_elem = kosdaq_area.select_one('.num_s')
            
            if price_elem and change_elem:
                price = price_elem.text.strip()
                change_text = change_elem.text.strip()
                
                # 상승/하락 판단
                status = 'up' if '상승' in change_text else 'down' if '하락' in change_text else 'unchanged'
                
                # 변화량과 변화율 추출
                change_match = re.search(r'([0-9.]+)', change_text)
                percent_match = re.search(r'([0-9.]+)%', change_text)
                
                change = change_match.group(1) if change_match else '0.00'
                percent = percent_match.group(1) if percent_match else '0.00'
                
                sign = '+' if status == 'up' else '-' if status == 'down' else ''
                
                indices_data.append({
                    'name': 'KOSDAQ',
                    'price': price,
                    'change': f'{sign}{change}',
                    'changePercent': f'{sign}{percent}%',
                    'status': status
                })
        
        # 해외 지수 추출
        global_indices = soup.select('.section_world .item_wrp')
        if global_indices:
            for item in global_indices[:3]:  # 최대 3개만 추출
                try:
                    name_elem = item.select_one('.h_area .name')
                    price_elem = item.select_one('.price')
                    change_elem = item.select_one('.gap')
                    
                    if name_elem and price_elem and change_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        
                        # 상승/하락 판단
                        status_classes = change_elem.get('class', [])
                        status = 'up' if 'up' in status_classes else 'down' if 'down' in status_classes else 'unchanged'
                        
                        change_text = change_elem.text.strip()
                        
                        # 변화량과 변화율 추출 - 다양한 형식 대응
                        change_parts = change_text.split()
                        change = change_parts[0] if len(change_parts) > 0 else '0.00'
                        
                        # 백분율이 괄호 안에 있는 경우를 처리
                        percent = None
                        for part in change_parts:
                            if '%' in part:
                                percent = part.strip('()')
                                break
                        
                        if percent is None and len(change_parts) > 1:
                            percent = change_parts[1].strip('()')
                        
                        if percent is None:
                            percent = '0.00%'
                        
                        sign = '+' if status == 'up' else '-' if status == 'down' else ''
                        if sign not in change:
                            change = f'{sign}{change}'
                        
                        indices_data.append({
                            'name': name,
                            'price': price,
                            'change': change,
                            'changePercent': percent,
                            'status': status
                        })
                except Exception as e:
                    print(f"해외 지수 파싱 오류: {e}")
                    continue
        
        result['indices'] = indices_data
        
        # 환율 데이터 추출
        currency_data = []
        exchange_section = soup.select('.section_exchange .item_wrp')
        
        if exchange_section:
            for item in exchange_section[:3]:  # 최대 3개만 추출
                try:
                    name_elem = item.select_one('.h_area .name')
                    price_elem = item.select_one('.price')
                    change_elem = item.select_one('.gap')
                    
                    if name_elem and price_elem and change_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        
                        # 상승/하락 판단
                        status_classes = change_elem.get('class', [])
                        status = 'up' if 'up' in status_classes else 'down' if 'down' in status_classes else 'unchanged'
                        
                        change_text = change_elem.text.strip()
                        
                        # 변화량과 변화율 추출
                        change_parts = change_text.split()
                        change = change_parts[0] if len(change_parts) > 0 else '0.00'
                        
                        # 백분율이 괄호 안에 있는 경우를 처리
                        percent = None
                        for part in change_parts:
                            if '%' in part:
                                percent = part.strip('()')
                                break
                        
                        if percent is None and len(change_parts) > 1:
                            percent = change_parts[1].strip('()')
                        
                        if percent is None:
                            percent = '0.00%'
                        
                        sign = '+' if status == 'up' else '-' if status == 'down' else ''
                        if sign not in change:
                            change = f'{sign}{change}'
                        
                        currency_data.append({
                            'name': name,
                            'price': price,
                            'change': change,
                            'changePercent': percent,
                            'status': status
                        })
                except Exception as e:
                    print(f"환율 파싱 오류: {e}")
                    continue
        
        result['currencies'] = currency_data
        
        # 원자재 데이터 추출
        commodity_data = []
        
        # 유가
        oil_section = soup.select('.section_oil .item_wrp')
        # 금시세
        gold_section = soup.select('.section_gold .item_wrp')
        
        commodity_sections = oil_section + gold_section
        
        if commodity_sections:
            for item in commodity_sections[:3]:  # 최대 3개만 추출
                try:
                    name_elem = item.select_one('.h_area .name')
                    price_elem = item.select_one('.price')
                    change_elem = item.select_one('.gap')
                    
                    if name_elem and price_elem and change_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        
                        # 상승/하락 판단
                        status_classes = change_elem.get('class', [])
                        status = 'up' if 'up' in status_classes else 'down' if 'down' in status_classes else 'unchanged'
                        
                        change_text = change_elem.text.strip()
                        
                        # 변화량과 변화율 추출
                        change_parts = change_text.split()
                        change = change_parts[0] if len(change_parts) > 0 else '0.00'
                        
                        # 백분율이 괄호 안에 있는 경우를 처리
                        percent = None
                        for part in change_parts:
                            if '%' in part:
                                percent = part.strip('()')
                                break
                        
                        if percent is None and len(change_parts) > 1:
                            percent = change_parts[1].strip('()')
                        
                        if percent is None:
                            percent = '0.00%'
                        
                        sign = '+' if status == 'up' else '-' if status == 'down' else ''
                        if sign not in change:
                            change = f'{sign}{change}'
                        
                        commodity_data.append({
                            'name': name,
                            'price': price,
                            'change': change,
                            'changePercent': percent,
                            'status': status
                        })
                except Exception as e:
                    print(f"원자재 파싱 오류: {e}")
                    continue
        
        result['commodities'] = commodity_data
        
        # 데이터가 없는 경우 기본 더미 데이터 반환
        if not result['indices'] and not result['currencies'] and not result['commodities']:
            raise Exception("크롤링된 데이터가 없습니다.")
        
        return JsonResponse(result)
    
    except Exception as e:
        print(f"네이버 금융 시장 데이터 크롤링 오류: {e}")
        # 기본 더미 데이터 반환
        dummy_data = {
            'updateTime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'indices': [
                {
                    'name': 'KOSPI',
                    'price': '2,477.41',
                    'change': '+21.52',
                    'changePercent': '+0.88%',
                    'status': 'up'
                },
                {
                    'name': 'KOSDAQ',
                    'price': '711.92',
                    'change': '+2.94',
                    'changePercent': '+0.41%',
                    'status': 'up'
                },
                {
                    'name': '다우존스',
                    'price': '40,697.53',
                    'change': '+172.74',
                    'changePercent': '+0.43%',
                    'status': 'up'
                }
            ],
            'currencies': [
                {
                    'name': '원/달러',
                    'price': '1,328.50',
                    'change': '-8.20',
                    'changePercent': '-0.61%',
                    'status': 'down'
                }
            ],
            'commodities': [
                {
                    'name': 'WTI',
                    'price': '61.53',
                    'change': '+0.03',
                    'changePercent': '+0.05%',
                    'status': 'up'
                }
            ]
        }
        return JsonResponse(dummy_data)
