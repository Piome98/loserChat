import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, CircularProgress, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button } from '@mui/material';
import axios from 'axios';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import OilBarrelIcon from '@mui/icons-material/OilBarrel';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAuth } from '../contexts/AuthContext';

const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('indices');
  const [lastUpdated, setLastUpdated] = useState(null);
  const { user } = useAuth();
  
  const fetchMarketData = useCallback(async () => {
    setLoading(true);
    try {
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
      
      // 네이버 금융 시장 개요 데이터 API 호출
      try {
        const response = await axios.get('http://localhost:8000/api/crawling/naver-finance-market/', {
          headers,
          params: {
            _t: new Date().getTime() // 캐시 방지
          }
        });
        
        // 응답 데이터 확인
        if (response.data) {
          setMarketData(response.data);
          setLastUpdated(new Date());
          console.log('네이버 금융 시장 데이터 로드됨');
        } else {
          // 예상치 못한 형식이면 더미 데이터 사용
          console.log('API 응답 없음, 더미 데이터 사용');
          setMarketData(generateDummyMarketData());
          setLastUpdated(new Date());
        }
      } catch (apiError) {
        console.error('API 호출 오류:', apiError);
        setMarketData(generateDummyMarketData());
        setLastUpdated(new Date());
      }
      
      setError(null);
    } catch (err) {
      console.error('시장 데이터 로딩 오류:', err);
      setError('시장 데이터를 불러오는데 실패했습니다. ' + (err.message || ''));
      setMarketData(generateDummyMarketData());
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, []);  // 의존성이 없으므로 빈 배열
  
  useEffect(() => {
    fetchMarketData();
    
    // 5분마다 데이터 자동 갱신
    const intervalId = setInterval(fetchMarketData, 300000);
    
    return () => clearInterval(intervalId);
  }, [fetchMarketData, user]);  // fetchMarketData를 의존성 배열에 추가
  
  // 더미 시장 데이터 생성 함수
  const generateDummyMarketData = () => {
    return {
      updateTime: new Date().toLocaleString(),
      indices: [
        {
          name: 'KOSPI',
          price: '2,477.41',
          change: '+21.52',
          changePercent: '+0.88%',
          status: 'up'
        },
        {
          name: 'KOSDAQ',
          price: '711.92',
          change: '+2.94',
          changePercent: '+0.41%',
          status: 'up'
        },
        {
          name: '다우존스',
          price: '40,697.53',
          change: '+172.74',
          changePercent: '+0.43%',
          status: 'up'
        },
        {
          name: '나스닥',
          price: '16,953.14',
          change: '+121.66',
          changePercent: '+0.72%',
          status: 'up'
        },
        {
          name: '상하이종합',
          price: '3,267.66',
          change: '+4.85',
          changePercent: '+0.15%',
          status: 'up'
        }
      ],
      currencies: [
        {
          name: '원/달러',
          price: '1,328.50',
          change: '-8.20',
          changePercent: '-0.61%',
          status: 'down'
        },
        {
          name: '원/엔',
          price: '881.53',
          change: '+3.47',
          changePercent: '+0.40%',
          status: 'up'
        },
        {
          name: '국고채 3년',
          price: '3.387%',
          change: '+0.012',
          changePercent: '+0.36%',
          status: 'up'
        }
      ],
      commodities: [
        {
          name: '국제유가(WTI)',
          price: '61.53',
          change: '+0.03',
          changePercent: '+0.05%',
          status: 'up'
        },
        {
          name: '국내금값',
          price: '147,551.76',
          change: '+736.44',
          changePercent: '+0.50%',
          status: 'up'
        }
      ]
    };
  };
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  const handleRefresh = () => {
    fetchMarketData();
  };
  
  if (loading && !marketData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error && !marketData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: 2 }}>
        <Typography color="error">{error}</Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={handleRefresh} 
          variant="contained"
        >
          다시 시도
        </Button>
      </Box>
    );
  }
  
  if (!marketData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography>데이터가 없습니다.</Typography>
      </Box>
    );
  }
  
  // 현재 활성 탭에 따른 데이터 배열
  let currentData = [];
  switch(activeTab) {
    case 'indices':
      currentData = marketData.indices || [];
      break;
    case 'currencies':
      currentData = marketData.currencies || [];
      break;
    case 'commodities':
      currentData = marketData.commodities || [];
      break;
    default:
      currentData = marketData.indices || [];
  }
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">시장 개요</Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={handleRefresh} 
          size="small" 
          variant="outlined"
          disabled={loading}
        >
          새로고침
        </Button>
      </Box>
      
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange}
        variant="fullWidth"
        sx={{ mb: 2 }}
      >
        <Tab 
          icon={<ShowChartIcon />} 
          label="주요 지수" 
          value="indices" 
          iconPosition="start"
        />
        <Tab 
          icon={<CurrencyExchangeIcon />} 
          label="환율/금리" 
          value="currencies" 
          iconPosition="start"
        />
        <Tab 
          icon={<OilBarrelIcon />} 
          label="원자재" 
          value="commodities" 
          iconPosition="start"
        />
      </Tabs>
      
      <TableContainer component={Paper} sx={{ flexGrow: 1, overflowY: 'auto' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>종목</TableCell>
              <TableCell align="right">현재가</TableCell>
              <TableCell align="right">전일대비</TableCell>
              <TableCell align="right">등락률</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentData.map((item, index) => (
              <TableRow key={index}>
                <TableCell component="th" scope="row">
                  {item.name}
                </TableCell>
                <TableCell align="right">{item.price}</TableCell>
                <TableCell 
                  align="right"
                  sx={{ 
                    color: item.status === 'up' ? 'success.main' : 
                           item.status === 'down' ? 'error.main' : 
                           'text.primary'
                  }}
                >
                  {item.change}
                </TableCell>
                <TableCell 
                  align="right"
                  sx={{ 
                    color: item.status === 'up' ? 'success.main' : 
                           item.status === 'down' ? 'error.main' : 
                           'text.primary',
                    fontWeight: 'medium'
                  }}
                >
                  {item.changePercent}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
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
      
      {loading && (
        <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.7)' }}>
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
};

export default MarketOverview;
