import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('index_crawler')

# 심볼 매핑을 통합적으로 관리
INDEX_SYMBOLS = {
    # 국내 지수
    'KOSPI': {
        'name': '코스피',
        'naver_domestic': 'KOSPI'
    },
    'KOSDAQ': {
        'name': '코스닥',
        'naver_domestic': 'KOSDAQ'
    },
    'KPI200': {
        'name': '코스피 200',
        'naver_domestic': 'KPI200'
    },
    
    # 해외 지수
    'DJI': {
        'name': '다우존스 산업평균지수',
        'yahoo': '^DJI',
        'naver_global': 'DJI@DJI'
    },
    'NASDAQ': {
        'name': '나스닥 종합지수',
        'yahoo': '^IXIC',
        'naver_global': 'NAS@IXIC'
    },
    'SP500': {
        'name': 'S&P 500',
        'yahoo': '^GSPC',
        'naver_global': 'SPI@SPX'
    },
    'HSI': {
        'name': '항셍지수',
        'yahoo': '^HSI',
        'naver_global': 'HSI@HSI'
    },
    
    # 원자재
    'WTI': {
        'name': 'WTI 원유',
        'yahoo': 'CL=F',
        'naver_commodity': 'OIL_CL'
    },
    'GOLD': {
        'name': '금',
        'yahoo': 'GC=F',
        'naver_commodity': 'CMDT_GC'
    },
    'SILVER': {
        'name': '은',
        'yahoo': 'SI=F',
        'naver_commodity': 'CMDT_SI'
    },
    
    # 환율
    'USD/KRW': {
        'name': '원/달러',
        'naver_exchange': 'FX_USDKRW'
    },
    'JPY/KRW': {
        'name': '원/엔',
        'naver_exchange': 'FX_JPYKRW'
    },
    'EUR/KRW': {
        'name': '원/유로',
        'naver_exchange': 'FX_EURKRW'
    },
    'CNY/KRW': {
        'name': '원/위안',
        'naver_exchange': 'FX_CNYKRW'
    }
}

# 기존 딕셔너리는 하위 호환성을 위해 유지하되 통합 심볼에서 파생
YAHOO_GLOBAL_INDEX_CODE_MAP = {code: info['yahoo'] for code, info in INDEX_SYMBOLS.items() if 'yahoo' in info}
NAVER_GLOBAL_INDEX_SYMBOLS = {code: info['naver_global'] for code, info in INDEX_SYMBOLS.items() if 'naver_global' in info}

# 통합 URL 정의
URLS = {
    'naver_domestic': "https://finance.naver.com/sise/sise_index_day.naver",
    'naver_global': "https://finance.naver.com/world/sise.naver",
    'naver_commodity': "https://finance.naver.com/marketindex/worldDailyQuote.nhn",
    'naver_exchange': "https://finance.naver.com/marketindex/exchangeDailyQuote.nhn",
    'yahoo_finance': "https://query1.finance.yahoo.com/v7/finance/download"
}

# 표준 User-Agent 정의
STANDARD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def get_index_name(code):
    """지수 코드에 대한 이름 반환"""
    return INDEX_SYMBOLS.get(code, {}).get('name', code)

def crawl_index_daily_price(index_code='KOSPI', pages=1):
    """
    네이버 금융에서 지수(코스피/코스닥) 일별 시세를 크롤링하는 함수
    
    Args:
        index_code (str): 지수 코드 ('KOSPI' 또는 'KOSDAQ')
        pages (int): 크롤링할 페이지 수
    
    Returns:
        pandas.DataFrame: 크롤링한 지수 일별 시세 데이터
    """
    # 해외 지수나 원자재인 경우 해당 크롤링 함수 호출
    if index_code in NAVER_GLOBAL_INDEX_SYMBOLS:
        return crawl_naver_global_index(index_code, days=pages * 10)  # 페이지당 약 10일치 데이터로 가정
    elif index_code in YAHOO_GLOBAL_INDEX_CODE_MAP:
        return crawl_global_index_data(index_code, days=pages * 10)  # 페이지당 약 10일치 데이터로 가정
    
    # 국내 지수 크롤링 로직
    all_data = []
    
    try:
        for page in range(1, pages + 1):
            print(f"크롤링 페이지: {page} (인덱스: {index_code})")
            logger.info(f"크롤링 페이지: {page} (인덱스: {index_code})")
            
            # 요청 파라미터 설정
            params = {
                'code': index_code,
                'page': page
            }
            
            # HTTP 요청
            response = requests.get(URLS['naver_domestic'], params=params, headers=STANDARD_HEADERS)
            response.raise_for_status()  # 오류 발생 시 예외 발생
            
            print(f"HTTP 상태 코드: {response.status_code}")
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 테이블 데이터 찾기 - 지수 테이블
            table = soup.select_one('table.type_1')
            if not table:
                print(f"페이지 {page}에서 테이블을 찾을 수 없습니다.")
                logger.warning(f"페이지 {page}에서 테이블을 찾을 수 없습니다. (인덱스: {index_code})")
                # HTML 일부 출력
                print("HTML 일부:", soup.prettify()[:500])
                continue
            
            print(f"테이블 찾음: {bool(table)}")
                
            # 행 데이터 추출
            rows = table.select('tr')
            print(f"행 개수: {len(rows)}")
            
            for row in rows:
                # 날짜 컬럼이 있는 행만 처리
                date_cell = row.select_one('td.date')
                if not date_cell:
                    continue
                
                # 날짜 추출
                date_text = date_cell.text.strip()
                
                # 지수 추출
                index_cell = row.select('td.number_1')
                if len(index_cell) < 4:  # 최소 4개의 셀이 필요 (지수, 전일대비, 거래량, 거래대금)
                    continue
                
                # 지수 값 추출
                index_value = index_cell[0].text.strip().replace(',', '')
                
                # 전일 대비 추출
                change_text = index_cell[1].text.strip()
                change_value = re.sub(r'[^\d.-]', '', change_text)
                
                # 등락률 계산
                is_up = len(row.select('img[src*="up"]')) > 0
                is_down = len(row.select('img[src*="down"]')) > 0
                
                if change_value:
                    change_value = float(change_value)
                    if is_down:
                        change_value = -change_value
                else:
                    change_value = 0
                
                # 거래량 추출
                volume = index_cell[2].text.strip().replace(',', '')
                
                # 데이터 저장
                data = {
                    'date': date_text,
                    'index_value': index_value,
                    'change': change_value,
                    'volume': volume
                }
                all_data.append(data)
                print(f"데이터 추가: {data}")
            
            print(f"페이지 {page} 크롤링 완료: {len(all_data)}개 데이터 수집됨")
            logger.info(f"페이지 {page} 크롤링 완료: {len(all_data)}개 데이터 수집됨 (인덱스: {index_code})")
    
    except requests.RequestException as e:
        print(f"데이터 요청 중 오류 발생: {e}")
        logger.error(f"데이터 요청 중 오류 발생: {e} (인덱스: {index_code})")
    except Exception as e:
        print(f"크롤링 중 예외 발생: {e}")
        logger.error(f"크롤링 중 예외 발생: {e} (인덱스: {index_code})")
    
    # 데이터프레임 변환
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 데이터 타입 변환
        df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d')
        df['index_value'] = pd.to_numeric(df['index_value'], errors='coerce')
        df['change'] = pd.to_numeric(df['change'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 날짜 기준 정렬
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
        
        return df
    else:
        print(f"수집된 데이터가 없습니다. (인덱스: {index_code})")
        logger.warning(f"수집된 데이터가 없습니다. (인덱스: {index_code})")
        return pd.DataFrame()

def crawl_naver_global_index(index_code, days=30):
    """
    네이버 금융에서 해외 지수 일별 시세를 크롤링하는 함수
    
    Args:
        index_code (str): 지수 코드 ('DJI', 'NASDAQ', 'SP500', 'HSI')
        days (int): 가져올 일 수
    
    Returns:
        pandas.DataFrame: 크롤링한 해외 지수 일별 시세 데이터
    """
    print(f"네이버 금융 해외 지수 크롤링 시작: {index_code}")
    logger.info(f"네이버 금융 해외 지수 크롤링 시작: {index_code}")
    
    # 심볼 가져오기
    symbol = NAVER_GLOBAL_INDEX_SYMBOLS.get(index_code)
    if not symbol:
        print(f"지원되지 않는 네이버 금융 해외 지수 코드: {index_code}")
        logger.error(f"지원되지 않는 네이버 금융 해외 지수 코드: {index_code}")
        return pd.DataFrame()
    
    # 요청 파라미터 설정
    params = {
        'symbol': symbol
    }
    
    try:
        # 기본 URL로 요청
        url = URLS['naver_global']
        
        # HTTP 요청
        response = requests.get(url, params=params, headers=STANDARD_HEADERS)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블 찾기
        table = None
        
        # id가 'dayTable'인 테이블 찾기
        table = soup.select_one('#dayTable')
        
        # 테이블을 찾지 못했다면 다른 선택자 시도
        if not table:
            table = soup.select_one('table.tb_status2')
            
        # 테이블을 찾지 못했다면 모든 테이블 중에서 찾기
        if not table:
            tables = soup.find_all('table')
            for t in tables:
                date_cells = t.select('td.tb_td')
                if date_cells:
                    table = t
                    break
        
        if not table:
            print(f"테이블 찾음: {bool(table)}")
            logger.warning(f"해외 지수 {index_code} 테이블을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        # 행 데이터 추출
        rows = table.select('tr')
        print(f"행 개수: {len(rows)}")
        
        all_data = []
        for row in rows:
            # 날짜 셀이 있는 행만 처리
            date_cell = row.select_one('td.tb_td')
            if not date_cell:
                continue
            
            # 날짜 추출
            date_text = date_cell.text.strip()
            
            # 지수 값 추출 - 두 번째 셀 (종가)
            index_cells = row.select('td.tb_td2')
            if not index_cells:
                continue
                
            index_cell = index_cells[0]
            index_text = index_cell.text.strip()
            index_value = index_text.replace(',', '')
            
            # 전일 대비 추출 - 세 번째 셀
            change_cells = row.select('td.tb_td3')
            change_value = 0
            if change_cells:
                change_text = change_cells[0].text.strip()
                # 숫자만 추출
                change_match = re.search(r'[+-]?\d+\.?\d*', change_text)
                if change_match:
                    change_value = float(change_match.group())
                    
                    # 상승/하락 확인
                    is_up = 'point_up' in row.get('class', [])
                    is_down = 'point_dn' in row.get('class', [])
                    
                    if is_down and change_value > 0:
                        change_value = -change_value
            
            # 시가 추출 - 네 번째 셀 (거래량 대신 사용)
            volume_cells = row.select('td.tb_td4')
            volume = 0
            if volume_cells:
                volume_text = volume_cells[0].text.strip()
                volume = volume_text.replace(',', '')
            
            # 데이터 저장
            data = {
                'date': date_text,
                'index_value': index_value,
                'change': change_value,
                'volume': volume
            }
            all_data.append(data)
        
        # 데이터프레임 변환
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 데이터 타입 변환
            df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d')
            df['index_value'] = pd.to_numeric(df['index_value'], errors='coerce')
            df['change'] = pd.to_numeric(df['change'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            # 날짜 기준 정렬
            df = df.sort_values('date', ascending=False).reset_index(drop=True)
            
            # 결과 출력
            print(f"해외 지수 {index_code} 크롤링 완료: {len(all_data)}개 데이터 수집됨")
            logger.info(f"해외 지수 {index_code} 크롤링 완료: {len(all_data)}개 데이터 수집됨")
            
            return df
        else:
            print(f"해외 지수 {index_code} 수집된 데이터가 없습니다.")
            logger.warning(f"해외 지수 {index_code} 수집된 데이터가 없습니다.")
            return pd.DataFrame()
    
    except requests.RequestException as e:
        print(f"데이터 요청 중 오류 발생: {e}")
        logger.error(f"데이터 요청 중 오류 발생: {e} (인덱스: {index_code})")
        return pd.DataFrame()
    except Exception as e:
        print(f"크롤링 중 예외 발생: {e}")
        logger.error(f"크롤링 중 예외 발생: {e} (인덱스: {index_code})")
        return pd.DataFrame()

def crawl_global_index_data(index_code, days=30):
    """
    해외 지수 및 원자재 일별 시세를 크롤링하는 함수
    
    Args:
        index_code (str): 지수 코드 ('DJI', 'NASDAQ', 'SP500', 'WTI', 'GOLD', 'SILVER')
        days (int): 가져올 일 수
    
    Returns:
        pandas.DataFrame: 크롤링한 해외 지수 또는 원자재 일별 시세 데이터
    """
    # 네이버 금융에서 크롤링 시도
    if index_code in NAVER_GLOBAL_INDEX_SYMBOLS:
        df = crawl_naver_global_index(index_code, days)
        if not df.empty:
            return df
    
    print(f"야후 파이낸스 해외 지수/원자재 크롤링 시작: {index_code}")
    logger.info(f"야후 파이낸스 해외 지수/원자재 크롤링 시작: {index_code}")
    
    # 야후 파이낸스 일별 시세 데이터 URL
    yahoo_code = YAHOO_GLOBAL_INDEX_CODE_MAP.get(index_code)
    if not yahoo_code:
        print(f"지원되지 않는 해외 지수/원자재 코드: {index_code}")
        logger.error(f"지원되지 않는 해외 지수/원자재 코드: {index_code}")
        return pd.DataFrame()
    
    # 현재 시간에서 1년 전까지의 데이터를 요청 (필요한 일수만큼 가져오기 위함)
    now = int(datetime.now().timestamp())
    one_year_ago = int((datetime.now() - pd.DateOffset(years=1)).timestamp())
    
    base_url = f"{URLS['yahoo_finance']}/{yahoo_code}"
    params = {
        'period1': one_year_ago,
        'period2': now,
        'interval': '1d',
        'events': 'history',
        'includeAdjustedClose': 'true'
    }
    
    try:
        # 인증 문제로 401 에러가 발생할 경우, 다른 방법으로 데이터를 가져올 준비
        try:
            response = requests.get(base_url, params=params, headers=STANDARD_HEADERS)
            response.raise_for_status()
            
            # CSV 데이터를 pandas DataFrame으로 변환
            df = pd.read_csv(pd.StringIO(response.text))
        except requests.RequestException as e:
            print(f"야후 파이낸스 API 오류: {e}, 대체 방법 시도")
            logger.warning(f"야후 파이낸스 API 오류: {e}, 대체 방법 시도")
            
            # API 요청이 실패한 경우 dummy 데이터 반환 (실제로는 다른 데이터 소스를 시도해야 함)
            # 나중에 더 많은 데이터 소스를 추가할 수 있음
            return pd.DataFrame()
        
        # 필요한 컬럼만 선택하고 이름 변경
        df = df[['Date', 'Close', 'Volume']]
        df.rename(columns={
            'Date': 'date',
            'Close': 'index_value',
            'Volume': 'volume'
        }, inplace=True)
        
        # 변화량 계산 (당일 종가 - 전일 종가)
        df['change'] = df['index_value'].diff(-1) * -1  # diff는 이전 행과의 차이를 계산
        
        # 날짜 형식 변환
        df['date'] = pd.to_datetime(df['date'])
        
        # 최근 데이터 먼저 정렬
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
        
        # 요청한 일수만큼 자르기
        df = df.head(days)
        
        print(f"해외 지수/원자재 {index_code} 데이터 수집 완료: {len(df)}개")
        logger.info(f"해외 지수/원자재 {index_code} 데이터 수집 완료: {len(df)}개")
        
        return df
    
    except Exception as e:
        print(f"해외 지수/원자재 크롤링 중 예외 발생: {e}")
        logger.error(f"해외 지수/원자재 크롤링 중 예외 발생: {e} (인덱스: {index_code})")
        return pd.DataFrame()

def crawl_commodity_data(code, days=30):
    """원자재 데이터 크롤링 함수"""
    try:
        # 심볼 정보 가져오기
        symbol_info = INDEX_SYMBOLS.get(code, {})
        naver_code = symbol_info.get('naver_commodity')
        
        if not naver_code:
            print(f"지원되지 않는 원자재 코드: {code}")
            logger.error(f"지원되지 않는 원자재 코드: {code}")
            return None
            
        # 요청 파라미터 설정
        params = {'marketindexCd': naver_code}
            
        # 요청 보내기
        response = requests.get(URLS['naver_commodity'], params=params, headers=STANDARD_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블 데이터 추출
        table = soup.select_one('table.tbl_exchange')
        if not table:
            return None
            
        rows = table.select('tr')
        
        data_list = []
        for row in rows:
            date_cell = row.select_one('td.date')
            price_cell = row.select_one('td:nth-child(2)')
            
            if not date_cell or not price_cell:
                continue
                
            date_text = date_cell.text.strip()
            price_text = price_cell.text.strip().replace(',', '')
            
            # 등락 방향과 값 추출
            change_cell = row.select_one('td:nth-child(3)')
            if change_cell:
                is_up = 'up' in change_cell.get('class', [])
                is_down = 'down' in change_cell.get('class', [])
                
                change_text = change_cell.text.strip().replace(',', '')
                if change_text:
                    change_value = float(re.sub(r'[^\d.]+', '', change_text))
                    if is_down:
                        change_value = -change_value
                else:
                    change_value = 0
            else:
                change_value = 0
            
            try:
                # 데이터 추가
                data_list.append({
                    'date': date_text,
                    'index_value': float(price_text) if price_text else None,
                    'change': change_value,
                    'volume': None  # 거래량 데이터가 없음
                })
            except (ValueError, TypeError):
                continue
                
        # 리스트를 데이터프레임으로 변환하여 반환
        df = pd.DataFrame(data_list)
        if df.empty:
            return None
            
        # 최대 days만큼만 반환
        df = df.head(days)
        
        return {
            'code': code,
            'name': get_index_name(code),
            'data': df.to_dict('records'),
            'total_count': len(df),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"원자재 데이터 크롤링 오류: {str(e)}")
        return None

def crawl_currency_data(code, days=30):
    """환율 데이터 크롤링 함수"""
    try:
        # 심볼 정보 가져오기
        symbol_info = INDEX_SYMBOLS.get(code, {})
        naver_code = symbol_info.get('naver_exchange')
        
        if not naver_code:
            print(f"지원되지 않는 환율 코드: {code}")
            logger.error(f"지원되지 않는 환율 코드: {code}")
            return None
        
        # 요청 파라미터 설정
        params = {'marketindexCd': naver_code}
            
        # 요청 보내기
        response = requests.get(URLS['naver_exchange'], params=params, headers=STANDARD_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블 데이터 추출
        table = soup.select_one('table.tbl_exchange')
        if not table:
            return None
            
        rows = table.select('tr')
        
        data_list = []
        for row in rows:
            date_cell = row.select_one('td.date')
            price_cell = row.select_one('td:nth-child(2)')
            
            if not date_cell or not price_cell:
                continue
                
            date_text = date_cell.text.strip()
            price_text = price_cell.text.strip().replace(',', '')
            
            # 등락 방향과 값 추출
            change_cell = row.select_one('td:nth-child(3)')
            if change_cell:
                is_up = 'up' in change_cell.get('class', [])
                is_down = 'down' in change_cell.get('class', [])
                
                change_text = change_cell.text.strip().replace(',', '')
                if change_text:
                    change_value = float(re.sub(r'[^\d.]+', '', change_text))
                    if is_down:
                        change_value = -change_value
                else:
                    change_value = 0
            else:
                change_value = 0
                
            try:
                # 데이터 추가
                data_list.append({
                    'date': date_text,
                    'index_value': float(price_text) if price_text else None,
                    'change': change_value,
                    'volume': None  # 거래량 데이터가 없음
                })
            except (ValueError, TypeError):
                continue
                
        # 리스트를 데이터프레임으로 변환하여 반환
        df = pd.DataFrame(data_list)
        if df.empty:
            return None
            
        # 최대 days만큼만 반환
        df = df.head(days)
        
        return {
            'code': code,
            'name': get_index_name(code),
            'data': df.to_dict('records'),
            'total_count': len(df),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"환율 데이터 크롤링 오류: {str(e)}")
        return None

def save_to_csv(df, index_code='KOSPI', filename=None):
    """
    데이터프레임을 CSV 파일로 저장하는 함수
    
    Args:
        df (pandas.DataFrame): 저장할 데이터프레임
        index_code (str): 지수 코드 ('KOSPI' 또는 'KOSDAQ')
        filename (str, optional): 저장할 파일명. 기본값은 {index_code}_data_YYYYMMDD.csv
    """
    if df.empty:
        print(f"저장할 데이터가 없습니다. (인덱스: {index_code})")
        logger.warning(f"저장할 데이터가 없습니다. (인덱스: {index_code})")
        return
    
    if not filename:
        today = datetime.now().strftime('%Y%m%d')
        filename = f'{index_code.lower()}_data_{today}.csv'
    
    try:
        # 현재 작업 디렉토리 확인
        current_dir = os.getcwd()
        print(f"현재 작업 디렉토리: {current_dir}")
        
        # 전체 파일 경로
        full_path = os.path.join(current_dir, filename)
        print(f"저장할 파일 경로: {full_path}")
        
        df.to_csv(full_path, index=False, encoding='utf-8-sig')
        print(f"데이터가 {full_path}에 성공적으로 저장되었습니다. (인덱스: {index_code})")
        logger.info(f"데이터가 {full_path}에 성공적으로 저장되었습니다. (인덱스: {index_code})")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        logger.error(f"파일 저장 중 오류 발생: {e} (인덱스: {index_code})")

def crawl_and_save_indices(indices=['KOSPI', 'KOSDAQ'], pages=2):
    """
    여러 지수의 일별 시세를 크롤링하고 저장하는 함수
    
    Args:
        indices (list): 크롤링할 지수 코드 리스트
        pages (int): 각 지수마다 크롤링할 페이지 수
    """
    results = {}
    
    for index_code in indices:
        print(f"\n=== {index_code} 일별 시세 크롤링 시작 ===")
        df = crawl_index_daily_price(index_code=index_code, pages=pages)
        
        if not df.empty:
            # 데이터 출력
            print(f"\n=== {index_code} 일별 시세 데이터 ===")
            print(df.head(5))
            print(f"\n총 {len(df)}개의 데이터가 수집되었습니다.")
            
            # CSV 저장
            save_to_csv(df, index_code=index_code)
            
            # 결과 저장
            results[index_code] = df
        
        print(f"\n=== {index_code} 크롤링 완료 ===")
    
    return results

if __name__ == '__main__':
    print("\n=== 주식 지수 일별 시세 크롤링 시작 ===")
    
    # 국내외 주요 지수와 원자재 모두 크롤링
    results = crawl_and_save_indices(
        indices=['KOSPI', 'KOSDAQ', 'DJI', 'NASDAQ', 'SP500', 'WTI', 'GOLD', 'SILVER'], 
        pages=2
    )
    
    print("\n=== 모든 지수 크롤링 완료 ===\n") 