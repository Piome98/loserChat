import time
import threading
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .utils import crawl_news_from_investing, crawl_market_indices, crawl_naver_finance_news, crawl_naver_market_indices

logger = logging.getLogger(__name__)

class CrawlingScheduler:
    """크롤링 작업 스케줄러"""
    
    def __init__(self):
        self.news_interval = 300  # 5분마다 뉴스 크롤링
        self.market_interval = 180  # 3분마다 시장 지수 크롤링
        self.naver_news_interval = 600  # 10분마다 네이버 뉴스 크롤링
        self.naver_market_interval = 240  # 4분마다 네이버 시장 지수 크롤링
        self._running = False
        self._thread = None
        self.last_news_crawl = None
        self.last_market_crawl = None
        self.last_naver_news_crawl = None
        self.last_naver_market_crawl = None
    
    def start(self):
        """스케줄러 시작"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("크롤링 스케줄러 시작됨")
    
    def stop(self):
        """스케줄러 중지"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("크롤링 스케줄러 중지됨")
    
    def _run(self):
        """스케줄러 실행 루프"""
        while self._running:
            now = timezone.now()
            
            # 뉴스 크롤링 체크
            if (self.last_news_crawl is None or 
                (now - self.last_news_crawl).total_seconds() >= self.news_interval):
                try:
                    logger.info("뉴스 크롤링 시작")
                    crawl_news_from_investing()
                    self.last_news_crawl = now
                    logger.info("뉴스 크롤링 완료")
                except Exception as e:
                    logger.error(f"뉴스 크롤링 실패: {str(e)}")
            
            # 시장 지수 크롤링 체크
            if (self.last_market_crawl is None or 
                (now - self.last_market_crawl).total_seconds() >= self.market_interval):
                try:
                    logger.info("시장 지수 크롤링 시작")
                    crawl_market_indices()
                    self.last_market_crawl = now
                    logger.info("시장 지수 크롤링 완료")
                except Exception as e:
                    logger.error(f"시장 지수 크롤링 실패: {str(e)}")
            
            # 네이버 금융 뉴스 크롤링 체크
            if (self.last_naver_news_crawl is None or 
                (now - self.last_naver_news_crawl).total_seconds() >= self.naver_news_interval):
                try:
                    logger.info("네이버 금융 뉴스 크롤링 시작")
                    crawl_naver_finance_news()
                    self.last_naver_news_crawl = now
                    logger.info("네이버 금융 뉴스 크롤링 완료")
                except Exception as e:
                    logger.error(f"네이버 금융 뉴스 크롤링 실패: {str(e)}")
            
            # 네이버 금융 시장 지수 크롤링 체크
            if (self.last_naver_market_crawl is None or 
                (now - self.last_naver_market_crawl).total_seconds() >= self.naver_market_interval):
                try:
                    logger.info("네이버 금융 시장 지수 크롤링 시작")
                    crawl_naver_market_indices()
                    self.last_naver_market_crawl = now
                    logger.info("네이버 금융 시장 지수 크롤링 완료")
                except Exception as e:
                    logger.error(f"네이버 금융 시장 지수 크롤링 실패: {str(e)}")
            
            # 1초 동안 대기
            time.sleep(1)

# 스케줄러 인스턴스 생성
scheduler = CrawlingScheduler()
