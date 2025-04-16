import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import pytz
from django.conf import settings
from django.core.cache import cache
from .models import NewsArticle, MarketIndex

logger = logging.getLogger(__name__)

# User-Agent 헤더 설정
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

def crawl_news_from_investing():
    """인베스팅닷컴에서 경제 뉴스 크롤링"""
    try:
        # 뉴스 페이지 URL
        url = 'https://kr.investing.com/news/economy/'
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.error(f"뉴스 크롤링 실패: HTTP {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 경제 뉴스 항목들 찾기
        news_items = soup.select('div.largeTitle article') or soup.select('div.js-article-item')
        
        news_data = []
        korea_tz = pytz.timezone('Asia/Seoul')
        
        for idx, item in enumerate(news_items[:15]):  # 상위 15개 뉴스만 처리
            try:
                # 제목과 링크
                title_elem = item.select_one('a.title') or item.select_one('a.js-article-title')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                url = title_elem['href']
                if not url.startswith('http'):
                    url = f"https://kr.investing.com{url}"
                
                # 요약 (있는 경우)
                summary_elem = item.select_one('p') or item.select_one('div.textDiv')
                summary = summary_elem.text.strip() if summary_elem else ""
                
                # 출처와 날짜
                source_elem = item.select_one('span.sourceName') or item.select_one('span.js-article-source')
                source = source_elem.text.strip() if source_elem else "인베스팅닷컴"
                
                date_elem = item.select_one('span.date') or item.select_one('span.js-article-date')
                date_str = date_elem.text.strip() if date_elem else datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # 날짜 파싱 시도
                try:
                    # "1시간 전", "10분 전" 등의 상대적 시간 처리
                    if '전' in date_str:
                        published_at = datetime.now(korea_tz)
                    else:
                        # 특정 형식의 날짜 파싱 시도
                        published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                        published_at = korea_tz.localize(published_at)
                except ValueError:
                    published_at = datetime.now(korea_tz)
                
                # 카테고리 추출
                category_elem = item.select_one('span.articleDetails') or item.select_one('a.categoryLink')
                if category_elem:
                    category_text = category_elem.text.strip()
                    if '주식' in category_text:
                        category = '증시'
                    elif '경제' in category_text:
                        category = '경제'
                    elif '기업' in category_text or '산업' in category_text:
                        category = '기업'
                    elif '세계' in category_text or '국제' in category_text:
                        category = '국제'
                    else:
                        category = '경제'
                else:
                    category = '경제'
                
                # 이미지 URL (있는 경우)
                img_elem = item.select_one('img')
                img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                
                # 데이터 저장
                news_data.append({
                    'title': title,
                    'content_summary': summary,
                    'source': source,
                    'published_at': published_at,
                    'url': url,
                    'category': category,
                    'image_url': img_url,
                    'related_symbols': []  # 기본 빈 리스트
                })
                
                # 데이터베이스에 저장 (중복 방지)
                NewsArticle.objects.update_or_create(
                    url=url,
                    defaults={
                        'title': title,
                        'content_summary': summary,
                        'source': source,
                        'published_at': published_at,
                        'category': category,
                        'image_url': img_url,
                    }
                )
                
            except Exception as e:
                logger.error(f"뉴스 항목 파싱 오류: {str(e)}")
                continue
        
        return news_data
        
    except Exception as e:
        logger.error(f"뉴스 크롤링 중 오류 발생: {str(e)}")
        return []

def crawl_market_indices():
    """인베스팅닷컴에서 주요 시장 지수 크롤링"""
    try:
        # 시장 지수 페이지 URL
        url = 'https://kr.investing.com/indices/major-indices'
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.error(f"시장 지수 크롤링 실패: HTTP {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 주요 지수 테이블 찾기
        indices_table = soup.select_one('table.common-data-table')
        if not indices_table:
            logger.error("시장 지수 테이블을 찾을 수 없음")
            return []
        
        indices_data = []
        rows = indices_table.select('tbody tr')
        
        korea_indices = ['kospi', 'kosdaq']  # 국내 주요 지수 심볼 (소문자)
        major_indices = ['dow-jones', 'nasdaq-composite', 's-p-500', 'dax', 'nikkei-225']  # 해외 주요 지수 심볼 (소문자)
        
        for row in rows:
            try:
                # 지수 정보 추출
                name_elem = row.select_one('td.col-name a')
                if not name_elem:
                    continue
                
                name = name_elem.text.strip()
                symbol = name_elem['href'].split('/')[-1].lower()
                
                # 국내 지수 또는 주요 해외 지수만 추출
                if symbol not in korea_indices and symbol not in major_indices:
                    continue
                
                price_elem = row.select_one('td.last')
                price = price_elem.text.strip().replace(',', '') if price_elem else '0'
                
                change_elem = row.select_one('td.chg')
                change = change_elem.text.strip().replace(',', '') if change_elem else '0'
                
                percent_elem = row.select_one('td.chg_pct')
                percent = percent_elem.text.strip().replace('%', '').replace(',', '') if percent_elem else '0'
                
                # 데이터 저장
                indices_data.append({
                    'name': name,
                    'symbol': symbol,
                    'price': float(price),
                    'change': float(change),
                    'change_percent': float(percent)
                })
                
                # 데이터베이스에 저장 (업데이트)
                MarketIndex.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'name': name,
                        'price': price,
                        'change': change,
                        'change_percent': percent
                    }
                )
                
            except Exception as e:
                logger.error(f"지수 항목 파싱 오류: {str(e)}")
                continue
        
        return indices_data
        
    except Exception as e:
        logger.error(f"시장 지수 크롤링 중 오류 발생: {str(e)}")
        return []

def fetch_news_by_symbol(symbol):
    """특정 종목 관련 뉴스 크롤링"""
    try:
        # 종목별 뉴스 검색 페이지 URL
        url = f'https://kr.investing.com/search/?q={symbol}&tab=news'
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.error(f"종목 뉴스 크롤링 실패: HTTP {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 검색 결과 뉴스 항목 찾기
        news_items = soup.select('div.searchSectionMain article') or soup.select('div.js-article-item')
        
        news_data = []
        korea_tz = pytz.timezone('Asia/Seoul')
        
        for idx, item in enumerate(news_items[:10]):  # 상위 10개 뉴스만 처리
            try:
                # 제목과 링크
                title_elem = item.select_one('a.title') or item.select_one('a.js-article-title')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                url = title_elem['href']
                if not url.startswith('http'):
                    url = f"https://kr.investing.com{url}"
                
                # 요약 (있는 경우)
                summary_elem = item.select_one('p') or item.select_one('div.textDiv')
                summary = summary_elem.text.strip() if summary_elem else ""
                
                # 출처와 날짜
                source_elem = item.select_one('span.sourceName') or item.select_one('span.js-article-source')
                source = source_elem.text.strip() if source_elem else "인베스팅닷컴"
                
                date_elem = item.select_one('span.date') or item.select_one('span.js-article-date')
                date_str = date_elem.text.strip() if date_elem else datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # 날짜 파싱 시도
                try:
                    # "1시간 전", "10분 전" 등의 상대적 시간 처리
                    if '전' in date_str:
                        published_at = datetime.now(korea_tz)
                    else:
                        # 특정 형식의 날짜 파싱 시도
                        published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                        published_at = korea_tz.localize(published_at)
                except ValueError:
                    published_at = datetime.now(korea_tz)
                
                # 기본 카테고리는 종목 관련
                category = '종목'
                
                # 이미지 URL (있는 경우)
                img_elem = item.select_one('img')
                img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
                
                # 데이터 저장
                news_data.append({
                    'title': title,
                    'content_summary': summary,
                    'source': source,
                    'published_at': published_at,
                    'url': url,
                    'category': category,
                    'image_url': img_url,
                    'related_symbols': [symbol]  # 관련 종목 추가
                })
                
                # 데이터베이스에 저장 (중복 방지)
                article, created = NewsArticle.objects.update_or_create(
                    url=url,
                    defaults={
                        'title': title,
                        'content_summary': summary,
                        'source': source,
                        'published_at': published_at,
                        'category': category,
                        'image_url': img_url,
                    }
                )
                
                # 관련 종목 업데이트
                if symbol not in article.related_symbols:
                    article.related_symbols.append(symbol)
                    article.save()
                
            except Exception as e:
                logger.error(f"종목 뉴스 항목 파싱 오류: {str(e)}")
                continue
        
        return news_data
        
    except Exception as e:
        logger.error(f"종목 뉴스 크롤링 중 오류 발생: {str(e)}")
        return []
