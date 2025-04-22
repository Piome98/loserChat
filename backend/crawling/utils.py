import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import pytz
from django.conf import settings
from django.core.cache import cache
from .models import NewsArticle, MarketIndex
import random
import time
import re

logger = logging.getLogger(__name__)

# User-Agent 헤더 설정
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

def _parse_investing_news_item(item, symbol=None):
    """인베스팅닷컴 뉴스 항목 파싱을 위한 공통 함수"""
    korea_tz = pytz.timezone('Asia/Seoul')
    
    # 제목과 링크
    title_elem = item.select_one('a.title') or item.select_one('a.js-article-title')
    if not title_elem:
        return None
        
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
    
    # 카테고리 설정
    if symbol:
        category = '종목'
    else:
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
    
    # 관련 종목
    related_symbols = [symbol] if symbol else []
    
    # 데이터 반환
    return {
        'title': title,
        'content_summary': summary,
        'source': source,
        'published_at': published_at,
        'url': url,
        'category': category,
        'image_url': img_url,
        'related_symbols': related_symbols
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
        
        for idx, item in enumerate(news_items[:15]):  # 상위 15개 뉴스만 처리
            try:
                news_item = _parse_investing_news_item(item)
                if news_item:
                    news_data.append(news_item)
                    
                    # 데이터베이스에 저장 (중복 방지)
                    NewsArticle.objects.update_or_create(
                        url=news_item['url'],
                        defaults={
                            'title': news_item['title'],
                            'content_summary': news_item['content_summary'],
                            'source': news_item['source'],
                            'published_at': news_item['published_at'],
                            'category': news_item['category'],
                            'image_url': news_item['image_url'],
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
        
        for idx, item in enumerate(news_items[:10]):  # 상위 10개 뉴스만 처리
            try:
                news_item = _parse_investing_news_item(item, symbol)
                if news_item:
                    news_data.append(news_item)
                    
                    # 데이터베이스에 저장 (중복 방지)
                    article, created = NewsArticle.objects.update_or_create(
                        url=news_item['url'],
                        defaults={
                            'title': news_item['title'],
                            'content_summary': news_item['content_summary'],
                            'source': news_item['source'],
                            'published_at': news_item['published_at'],
                            'category': news_item['category'],
                            'image_url': news_item['image_url'],
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

def crawl_naver_finance_news(symbol=None, max_news=15, max_pages=2):
    """네이버 금융 뉴스 크롤링 함수 - 여러 페이지 지원"""
    news_data = []
    
    for page in range(1, max_pages + 1):
        if symbol:
            # 종목별 뉴스 URL (페이지 번호 포함)
            url = f'https://finance.naver.com/item/news_news.naver?code={symbol}&page={page}'
        else:
            # 경제 뉴스 URL (페이지 번호 포함)
            url = f'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258&page={page}'
        
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
        
        # 지연 시간 추가
        time.sleep(random.uniform(0.2, 0.5))
        
        # 요청 보내기
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 응답 인코딩 설정 (네이버는 EUC-KR 인코딩 사용)
        response.encoding = 'euc-kr'
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        korea_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(korea_tz)
        
        if symbol:
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
                    date_str = info_elems[1].text.strip() if len(info_elems) > 1 else now.strftime("%Y.%m.%d")
                    
                    # 기사 세부 내용 가져오기 시도
                    summary = ""
                    try:
                        article_response = requests.get(link, headers=headers, timeout=3)
                        article_response.encoding = 'euc-kr'
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        
                        # 기사 내용 추출 시도
                        article_body = article_soup.select_one('div#news_read, div.articleCont')
                        if article_body:
                            # 불필요한 요소 제거
                            for tag in article_body.select('.link_news, .reporter_area, script'):
                                tag.extract()
                            
                            # 텍스트 추출 및 정리
                            article_text = article_body.text.strip()
                            article_text = re.sub(r'\s+', ' ', article_text)
                            
                            # 요약 (처음 100자)
                            summary = article_text[:100] + "..." if len(article_text) > 100 else article_text
                    except Exception as e:
                        logger.error(f"기사 내용 가져오기 실패: {str(e)}")
                    
                    # 날짜 형식 처리
                    published_at = now
                    try:
                        # "YYYY.MM.DD" 형식 변환
                        date_parts = date_str.split('.')
                        if len(date_parts) >= 3:
                            year = int(date_parts[0])
                            month = int(date_parts[1])
                            day = int(date_parts[2])
                            published_at = datetime(year, month, day, tzinfo=korea_tz)
                    except:
                        pass
                    
                    # 데이터베이스에 저장 (중복 방지)
                    article, created = NewsArticle.objects.update_or_create(
                        url=link,
                        defaults={
                            'title': title,
                            'content_summary': summary,
                            'source': source,
                            'published_at': published_at,
                            'category': '기업',
                            'image_url': None,
                        }
                    )
                    
                    # 관련 종목 업데이트
                    if symbol not in article.related_symbols:
                        article.related_symbols.append(symbol)
                        article.save()
                    
                    news_data.append({
                        'id': idx,
                        'title': title,
                        'summary': summary,
                        'source': source,
                        'date': published_at.strftime('%Y-%m-%d %H:%M'),
                        'url': link,
                        'category': '기업',
                        'imageUrl': None,
                        'relatedSymbols': [symbol]
                    })
                    
                    if len(news_data) >= max_news:
                        break
                        
                except Exception as e:
                    logger.error(f"개별 뉴스 파싱 오류: {str(e)}")
                    continue
        else:
            # 경제 뉴스 파싱 (네이버 금융 경제 뉴스 페이지)
            news_items = soup.select('.newslist li, .realtimeNewsList li, .articleSubject')
            
            # 디버깅을 위한 로깅 추가
            logger.info(f"네이버 뉴스 항목 찾음: {len(news_items)}개")
            
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
                    date_str = date_elem.text.strip() if date_elem else now.strftime("%Y.%m.%d")
                    
                    # 날짜 형식 처리
                    published_at = now
                    try:
                        # "YYYY.MM.DD" 형식 변환
                        date_parts = date_str.split('.')
                        if len(date_parts) >= 3:
                            year = int(date_parts[0])
                            month = int(date_parts[1])
                            day = int(date_parts[2])
                            published_at = datetime(year, month, day, tzinfo=korea_tz)
                    except:
                        pass
                    
                    # 데이터베이스에 저장 (중복 방지)
                    NewsArticle.objects.update_or_create(
                        url=link,
                        defaults={
                            'title': title,
                            'content_summary': summary,
                            'source': source,
                            'published_at': published_at,
                            'category': '경제',
                            'image_url': None,
                        }
                    )
                    
                    news_data.append({
                        'id': idx,
                        'title': title,
                        'summary': summary,
                        'source': source,
                        'date': published_at.strftime('%Y-%m-%d %H:%M'),
                        'url': link,
                        'category': '경제',
                        'imageUrl': None,
                        'relatedSymbols': []
                    })
                    
                    if len(news_data) >= max_news:
                        break
                        
                except Exception as e:
                    logger.error(f"개별 뉴스 파싱 오류: {str(e)}")
                    continue
        
        # 최대 뉴스 개수에 도달하면 중단
        if len(news_data) >= max_news:
            break
    
    return news_data

def crawl_naver_market_indices():
    """네이버 금융 시장 지수 크롤링 함수 (개선 버전)"""
    try:
        # 다양한 User-Agent 설정
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        ]
        
        # 헤더 설정
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # 결과 데이터 초기화
        indices_data = []
        
        # 1. 코스피, 코스닥 정보 가져오기 (네이버 금융 국내증시 페이지)
        domestic_url = 'https://finance.naver.com/sise/'
        logger.info(f"네이버 금융 국내증시 크롤링 시작: {domestic_url}")
        
        try:
            response = requests.get(domestic_url, headers=headers, timeout=10)
            response.raise_for_status()  # 에러가 발생하면 예외를 발생시킵니다
            response.encoding = 'euc-kr'  # 네이버는 euc-kr 인코딩 사용
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # KOSPI 정보 추출
            kospi_area = soup.select_one('#KOSPI_now')
            if kospi_area:
                kospi_price = kospi_area.text.strip()
                kospi_change_elem = soup.select_one('#KOSPI_change')
                kospi_change = kospi_change_elem.text.strip() if kospi_change_elem else '0'
                
                kospi_percent_elem = soup.select_one('#KOSPI_quant')
                kospi_percent = kospi_percent_elem.text.strip().replace('상승률 ', '') if kospi_percent_elem else '0%'
                
                # +/- 기호로 상태 판단
                kospi_status = 'up' if '+' in kospi_change else 'down' if '-' in kospi_change else 'unchanged'
                
                indices_data.append({
                    'name': 'KOSPI',
                    'symbol': 'kospi',
                    'price': kospi_price,
                    'change': kospi_change.replace('+', '').replace('-', ''),
                    'change_percent': kospi_percent.replace('+', '').replace('-', '').replace('%', ''),
                    'status': kospi_status
                })
                logger.info(f"KOSPI 데이터 추출 성공: {kospi_price}, {kospi_change}, {kospi_percent}")
            else:
                logger.warning("KOSPI 데이터를 찾을 수 없습니다")
            
            # KOSDAQ 정보 추출
            kosdaq_area = soup.select_one('#KOSDAQ_now')
            if kosdaq_area:
                kosdaq_price = kosdaq_area.text.strip()
                kosdaq_change_elem = soup.select_one('#KOSDAQ_change')
                kosdaq_change = kosdaq_change_elem.text.strip() if kosdaq_change_elem else '0'
                
                kosdaq_percent_elem = soup.select_one('#KOSDAQ_quant')
                kosdaq_percent = kosdaq_percent_elem.text.strip().replace('상승률 ', '') if kosdaq_percent_elem else '0%'
                
                # +/- 기호로 상태 판단
                kosdaq_status = 'up' if '+' in kosdaq_change else 'down' if '-' in kosdaq_change else 'unchanged'
                
                indices_data.append({
                    'name': 'KOSDAQ',
                    'symbol': 'kosdaq',
                    'price': kosdaq_price,
                    'change': kosdaq_change.replace('+', '').replace('-', ''),
                    'change_percent': kosdaq_percent.replace('+', '').replace('-', '').replace('%', ''),
                    'status': kosdaq_status
                })
                logger.info(f"KOSDAQ 데이터 추출 성공: {kosdaq_price}, {kosdaq_change}, {kosdaq_percent}")
            else:
                logger.warning("KOSDAQ 데이터를 찾을 수 없습니다")
        
        except Exception as e:
            logger.error(f"국내증시 크롤링 중 오류: {str(e)}")
        
        # 2. 해외 지수 정보 가져오기 (네이버 금융 세계증시 페이지)
        world_url = 'https://finance.naver.com/world/'
        logger.info(f"네이버 금융 세계증시 크롤링 시작: {world_url}")
        
        try:
            response = requests.get(world_url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'euc-kr'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 주요 지수 정보 추출 - 업데이트된 선택자
            # 새로운 선택자: .data_lst li 태그 또는 .market_data .data_lst li 태그
            world_indices = soup.select('.market_data .data_lst li') or soup.select('.data_lst li')
            
            # 지수 이름 매핑 (간략화를 위해)
            index_names = {
                '다우': '다우존스',
                '나스닥': '나스닥',
                'S&P': 'S&P 500',
                '항셍': '항셍지수'
            }
            
            # 크롤링할 지수 목록 (프론트엔드와 일치시키기 위함)
            target_indices = ['다우', '나스닥', 'S&P', '항셍']
            
            for index_item in world_indices:
                try:
                    # 해외증시 데이터가 있는지 확인
                    point_status = index_item.select_one('.point_status')
                    if not point_status:
                        continue
                    
                    # 지수명 가져오기
                    name_elem = index_item.select_one('.dt a') or index_item.select_one('dt a')
                    if not name_elem:
                        continue
                    
                    # 지수명 추출 - blind 태그가 있을 수 있음
                    blind_elem = name_elem.select_one('.blind')
                    name_text = blind_elem.text.strip() if blind_elem else name_elem.text.strip()
                    
                    logger.info(f"지수명 텍스트: {name_text}")
                    
                    # 지수가 타겟 목록에 있는지 확인
                    included = False
                    for target in target_indices:
                        if target.lower() in name_text.lower():
                            # 대소문자 구분 없이 비교
                            included = True
                            break
                    
                    # 타겟 목록에 없으면 건너뛰기
                    if not included:
                        continue
                    
                    # 지수 이름 매핑
                    for key, value in index_names.items():
                        if key in name_text:
                            name = value
                            break
                    else:
                        name = name_text
                    
                    # 심볼 생성 (심볼은 URL에서 추출 가능한 경우)
                    symbol = ""
                    if name_elem.get('href'):
                        href = name_elem.get('href')
                        if 'symbol=' in href:
                            symbol = href.split('symbol=')[1].split('&')[0].lower()
                        else:
                            symbol = name.lower().replace(' ', '-').replace('&', 'and')
                    else:
                        symbol = name.lower().replace(' ', '-').replace('&', 'and')
                    
                    # 가격 정보
                    strong_elem = point_status.select_one('strong')
                    price = strong_elem.text.strip() if strong_elem else '0'
                    
                    # 변화량
                    em_elem = point_status.select_one('em')
                    change = em_elem.text.strip() if em_elem else '0'
                    
                    # 변화율과 상태 (상승/하락/보합)
                    span_elem = point_status.select_one('span')
                    percent = span_elem.text.strip().replace('%', '') if span_elem else '0'
                    
                    # 상태 결정
                    status = 'unchanged'
                    if 'point_up' in index_item.get('class', []) or 'point_up' in point_status.get('class', []):
                        status = 'up'
                    elif 'point_dn' in index_item.get('class', []) or 'point_dn' in point_status.get('class', []):
                        status = 'down'
                    
                    indices_data.append({
                        'name': name,
                        'symbol': symbol,
                        'price': price,
                        'change': change.replace('+', '').replace('-', ''),
                        'change_percent': percent.replace('+', '').replace('-', '').replace('%', ''),
                        'status': status
                    })
                    logger.info(f"해외 지수 추출 성공: {name}, {price}, {change}, {percent}")
                
                except Exception as e:
                    logger.error(f"해외 지수 항목 파싱 오류: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"세계증시 크롤링 중 오류: {str(e)}")
        
        # 3. 환율 정보 가져오기
        exchange_url = 'https://finance.naver.com/marketindex/'
        logger.info(f"네이버 금융 환율 크롤링 시작: {exchange_url}")
        
        try:
            response = requests.get(exchange_url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'euc-kr'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 환율 정보 가져오기
            exchange_items = soup.select('#exchangeList li') or soup.select('.data_lst li')
            
            # 추출할 환율 정보
            exchange_currency_map = {
                'usd': {'name': '원/달러', 'symbol': 'krw-usd'},
                'jpy': {'name': '원/엔', 'symbol': 'krw-jpy'},
                'cny': {'name': '원/위안', 'symbol': 'krw-cny'},
                'eur': {'name': '원/유로', 'symbol': 'krw-eur'}
            }
            
            # 환율 정보 추출
            for exchange_item in exchange_items:
                try:
                    # 환율 ID나 클래스 확인
                    item_id = exchange_item.get('id', '')
                    item_data = None
                    
                    # 통화 종류 확인
                    for key, data in exchange_currency_map.items():
                        if key in item_id.lower() or key in str(exchange_item).lower():
                            item_data = data
                            break
                    
                    # 지원하는 통화가 아니면 건너뛰기
                    if not item_data:
                        continue
                    
                    # 환율 가격
                    price_elem = exchange_item.select_one('.value') or exchange_item.select_one('span.num')
                    price = price_elem.text.strip() if price_elem else '0'
                    
                    # 변화량
                    change_elem = exchange_item.select_one('.change') or exchange_item.select_one('span.num2')
                    change = change_elem.text.strip() if change_elem else '0'
                    
                    # 상태 확인 (상승/하락)
                    status = 'unchanged'
                    if exchange_item.select_one('.up') or ('class' in exchange_item.attrs and 'up' in exchange_item['class']):
                        status = 'up'
                        if not change.startswith('+'):
                            change = f"+{change}"
                    elif exchange_item.select_one('.down') or ('class' in exchange_item.attrs and 'down' in exchange_item['class']):
                        status = 'down'
                        if not change.startswith('-'):
                            change = f"-{change}"
                    
                    # 변화율 계산 (환율 페이지는 따로 변화율을 표시하지 않을 수 있으므로)
                    try:
                        price_float = float(price.replace(',', ''))
                        change_float = float(change.replace(',', '').replace('+', '').replace('-', ''))
                        percent = f"{(change_float / price_float * 100):.2f}"
                    except:
                        percent = '0.00'
                    
                    indices_data.append({
                        'name': item_data['name'],
                        'symbol': item_data['symbol'],
                        'price': price,
                        'change': change.replace('+', '').replace('-', ''),
                        'change_percent': percent,
                        'status': status
                    })
                    logger.info(f"환율 추출 성공: {item_data['name']}, {price}, {change}, {percent}")
                
                except Exception as e:
                    logger.error(f"환율 항목 파싱 오류: {str(e)}")
            
            if not any(item['name'] in ['원/달러', '원/엔', '원/위안', '원/유로'] for item in indices_data):
                logger.warning("환율 데이터를 찾을 수 없습니다")
        
        except Exception as e:
            logger.error(f"환율 크롤링 중 오류: {str(e)}")
        
        # 4. 원자재 정보 가져오기 (원유, 금)
        try:
            # 원자재는 marketindex 페이지의 원/달러 아래에 있는 정보를 활용
            commodity_items = soup.select('#oilGoldList li') or soup.select('.data_lst.eco_oil li')
            
            if commodity_items and len(commodity_items) > 0:
                # WTI 유가 정보
                oil_item = commodity_items[0]  # 첫 번째 항목은 보통 WTI
                
                try:
                    name = 'WTI'
                    
                    # 가격
                    price_elem = oil_item.select_one('.value') or oil_item.select_one('span.num')
                    price = price_elem.text.strip() if price_elem else '0'
                    
                    # 변화량
                    change_elem = oil_item.select_one('.change') or oil_item.select_one('span.num2')
                    change = change_elem.text.strip() if change_elem else '0'
                    
                    # 상태 확인
                    status = 'unchanged'
                    if oil_item.select_one('.up') or ('class' in oil_item.attrs and 'up' in oil_item['class']):
                        status = 'up'
                        if not change.startswith('+'):
                            change = f"+{change}"
                    elif oil_item.select_one('.down') or ('class' in oil_item.attrs and 'down' in oil_item['class']):
                        status = 'down'
                        if not change.startswith('-'):
                            change = f"-{change}"
                    
                    # 변화율 계산
                    try:
                        price_float = float(price.replace(',', ''))
                        change_float = float(change.replace(',', '').replace('+', '').replace('-', ''))
                        percent = f"{(change_float / price_float * 100):.2f}"
                    except:
                        percent = '0.00'
                    
                    indices_data.append({
                        'name': name,
                        'symbol': 'wti-oil',
                        'price': price,
                        'change': change.replace('+', '').replace('-', ''),
                        'change_percent': percent,
                        'status': status
                    })
                    logger.info(f"원자재(WTI) 추출 성공: {name}, {price}, {change}, {percent}")
                
                except Exception as e:
                    logger.error(f"원자재(WTI) 항목 파싱 오류: {str(e)}")
                
                # 금 시세가 있는 경우 (일반적으로 2번째 항목)
                if len(commodity_items) > 1:
                    gold_item = commodity_items[1]
                    
                    try:
                        name = '금'
                        
                        # 가격
                        price_elem = gold_item.select_one('.value') or gold_item.select_one('span.num')
                        price = price_elem.text.strip() if price_elem else '0'
                        
                        # 변화량
                        change_elem = gold_item.select_one('.change') or gold_item.select_one('span.num2')
                        change = change_elem.text.strip() if change_elem else '0'
                        
                        # 상태 확인
                        status = 'unchanged'
                        if gold_item.select_one('.up') or ('class' in gold_item.attrs and 'up' in gold_item['class']):
                            status = 'up'
                            if not change.startswith('+'):
                                change = f"+{change}"
                        elif gold_item.select_one('.down') or ('class' in gold_item.attrs and 'down' in gold_item['class']):
                            status = 'down'
                            if not change.startswith('-'):
                                change = f"-{change}"
                        
                        # 변화율 계산
                        try:
                            price_float = float(price.replace(',', ''))
                            change_float = float(change.replace(',', '').replace('+', '').replace('-', ''))
                            percent = f"{(change_float / price_float * 100):.2f}"
                        except:
                            percent = '0.00'
                        
                        indices_data.append({
                            'name': name,
                            'symbol': 'gold',
                            'price': price,
                            'change': change.replace('+', '').replace('-', ''),
                            'change_percent': percent,
                            'status': status
                        })
                        logger.info(f"원자재(금) 추출 성공: {name}, {price}, {change}, {percent}")
                    
                    except Exception as e:
                        logger.error(f"원자재(금) 항목 파싱 오류: {str(e)}")
            else:
                logger.warning("원자재 데이터를 찾을 수 없습니다")
        
        except Exception as e:
            logger.error(f"원자재 크롤링 중 오류: {str(e)}")
        
        # 결과 확인
        logger.info(f"총 크롤링된 시장 데이터: {len(indices_data)}개")
        
        if not indices_data:
            logger.warning("크롤링된 데이터가 없습니다.")
        
        return indices_data
        
    except Exception as e:
        logger.error(f"네이버 금융 시장 지수 크롤링 중 오류 발생: {str(e)}")
        logger.exception("상세 오류 스택:")
        return []
