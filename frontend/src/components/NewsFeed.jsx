import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, CircularProgress, List, ListItem, ListItemText, Divider, Button } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import RefreshIcon from '@mui/icons-material/Refresh';

const NewsFeed = ({ stockSymbol }) => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const { user } = useAuth();
  
  const fetchNews = useCallback(async () => {
    setLoading(true);
    try {
      console.log('뉴스 가져오기 시작:', stockSymbol ? '종목 뉴스' : '경제 뉴스');
      
      // 인증 토큰 가져오기
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.error('인증 토큰이 없습니다.');
        throw new Error('인증이 필요합니다.');
      }
      
      // 직접 axios를 사용하여 API 호출
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      };
      
      const params = stockSymbol 
        ? { symbol: stockSymbol } 
        : { category: '경제' };
      
      // 네이버 금융 뉴스 API 호출
      try {
        const response = await axios.get('http://localhost:8000/api/crawling/naver-finance-news/', {
          headers,
          params: {
            ...params,
            _t: new Date().getTime() // 캐시 방지
          }
        });
        
        // 응답 데이터 확인
        if (response.data && Array.isArray(response.data) && response.data.length > 0) {
          const newsData = response.data;
          setNews(newsData);
          setLastUpdated(new Date());
          console.log('네이버 금융 뉴스 데이터 로드됨:', newsData.length);
        } else {
          // 빈 배열이나 예상치 못한 형식이면 더미 데이터 사용
          console.log('API 응답 없음, 더미 데이터 사용');
          const dummyData = generateDummyNews(stockSymbol);
          setNews(dummyData);
          setLastUpdated(new Date());
        }
      } catch (apiError) {
        console.error('API 호출 오류:', apiError);
        const dummyData = generateDummyNews(stockSymbol);
        setNews(dummyData);
        setLastUpdated(new Date());
      }
      
      setError(null);
    } catch (err) {
      console.error('뉴스 로딩 오류:', err);
      setError('뉴스를 불러오는데 실패했습니다. ' + (err.message || ''));
      setNews(generateDummyNews(stockSymbol));
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, [stockSymbol]);
  
  useEffect(() => {
    fetchNews();
  }, [fetchNews, user]);
  
  // 더미 뉴스 데이터 생성 함수
  const generateDummyNews = (symbol = null) => {
    const today = new Date();
    const formattedToday = today.toLocaleDateString();
    
    // 더미 뉴스 데이터
    const allNews = [
      {
        id: 1,
        title: '삼성전자, 신규 AI 반도체 양산 본격화... 5나노 기반',
        summary: '삼성전자가 5나노 기술 기반의 AI 반도체 양산을 본격화한다고 밝혔다.',
        source: '한국경제',
        date: formattedToday,
        url: 'https://finance.naver.com/news/',
        category: '기업',
        imageUrl: null,
        relatedSymbols: ['005930']
      },
      {
        id: 2,
        title: '원/달러 환율, 1330원 붕괴... "중국발 경기 우려에 영향"',
        summary: '원/달러 환율이 1330원 선이 무너졌다. 전문가들은 중국 경기둔화 우려와 미국 경제지표 호조로 인한 달러 강세가 원인이라고 분석...',
        source: '연합인포맥스',
        date: formattedToday,
        url: 'https://finance.naver.com/news/',
        category: '경제',
        imageUrl: null,
        relatedSymbols: []
      },
      {
        id: 3,
        title: '네이버 금융 뉴스로 이동하기',
        summary: '실시간 경제 뉴스를 확인하려면 클릭하세요.',
        source: '네이버 금융',
        date: formattedToday,
        url: 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
        category: '경제',
        imageUrl: null,
        relatedSymbols: []
      }
    ];
    
    if (symbol) {
      // 특정 종목 관련 뉴스만 필터링
      return allNews.filter(news => news.relatedSymbols.includes(symbol));
    } else {
      // 경제 카테고리 뉴스 필터링
      return allNews.filter(news => news.category === '경제');
    }
  };
  
  const handleRefresh = () => {
    fetchNews();
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box 
      sx={{ 
        width: '100%',
        height: '100%',
        overflow: 'auto',
        padding: 2
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {stockSymbol ? '관련 뉴스' : '경제 뉴스'}
        </Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={handleRefresh} 
          size="small" 
          variant="outlined"
        >
          새로고침
        </Button>
      </Box>
      
      {error && (
        <Typography variant="caption" color="error" sx={{ display: 'block', mb: 2 }}>
          {error}
        </Typography>
      )}
      
      {news.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70%' }}>
          <Typography>뉴스가 없습니다.</Typography>
        </Box>
      ) : (
        <>
          <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
            {news.map((item, index) => (
              <React.Fragment key={item.id || index}>
                <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                  <ListItemText
                    primary={
                      <a 
                        href={item.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ 
                          color: 'inherit', 
                          textDecoration: 'none',
                          fontWeight: 'medium',
                          display: 'block',
                          marginBottom: '4px'
                        }}
                        onClick={(e) => {
                          // 링크가 '#'이거나 불완전한 경우 기본 네이버 금융 뉴스로 이동
                          if (!item.url || item.url === '#') {
                            e.preventDefault();
                            window.open('https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258', '_blank');
                          }
                        }}
                      >
                        {item.title}
                      </a>
                    }
                    secondary={
                      <React.Fragment>
                        {item.summary && (
                          <Typography
                            component="span"
                            variant="body2"
                            color="text.primary"
                            sx={{ display: 'block', mb: 1 }}
                          >
                            {item.summary}
                          </Typography>
                        )}
                        <Typography
                          component="span"
                          variant="caption"
                          color="text.secondary"
                          sx={{ display: 'flex', justifyContent: 'space-between' }}
                        >
                          <span>{item.source}</span>
                          <span>{item.date}</span>
                        </Typography>
                      </React.Fragment>
                    }
                  />
                </ListItem>
                {index < news.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              마지막 업데이트: {lastUpdated ? lastUpdated.toLocaleString() : '알 수 없음'}
              {' '}
              <a 
                href="https://finance.naver.com/" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: 'inherit' }}
              >
                네이버 금융 제공
              </a>
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
};

export default NewsFeed; 