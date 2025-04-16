from django.db import models

# Create your models here.

class NewsArticle(models.Model):
    """뉴스 기사 데이터 모델"""
    title = models.CharField(max_length=255, verbose_name='제목')
    content_summary = models.TextField(blank=True, null=True, verbose_name='내용 요약')
    source = models.CharField(max_length=100, verbose_name='출처')
    published_at = models.DateTimeField(verbose_name='발행일')
    url = models.URLField(unique=True, verbose_name='기사 URL')
    category = models.CharField(max_length=50, verbose_name='카테고리')
    image_url = models.URLField(blank=True, null=True, verbose_name='이미지 URL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    # 종목 관련 정보
    related_symbols = models.JSONField(default=list, blank=True, verbose_name='관련 종목 코드')
    
    class Meta:
        verbose_name = '뉴스 기사'
        verbose_name_plural = '뉴스 기사들'
        ordering = ['-published_at']
        
    def __str__(self):
        return f"{self.title} ({self.source})"

class MarketIndex(models.Model):
    """시장 지수 데이터 모델"""
    name = models.CharField(max_length=50, unique=True, verbose_name='지수명')
    symbol = models.CharField(max_length=20, unique=True, verbose_name='심볼')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='가격')
    change = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='변동액')
    change_percent = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='변동률(%)')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='갱신일')
    
    class Meta:
        verbose_name = '시장 지수'
        verbose_name_plural = '시장 지수들'
        
    def __str__(self):
        return f"{self.name} ({self.symbol})"
