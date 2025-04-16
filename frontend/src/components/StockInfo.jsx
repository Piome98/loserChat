import React, { useState, useEffect, useCallback } from 'react';
import { Paper, Typography, Box, Chip, Divider, CircularProgress, Button } from '@mui/material';
import { stockAPI } from '../api/api';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { useAuth } from '../contexts/AuthContext';

const StockInfo = ({ stockId }) => {
  const { user } = useAuth();
  const [stock, setStock] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [joining, setJoining] = useState(false);
  const [inRoom, setInRoom] = useState(false);

  // 종목 정보 가져오기 - useCallback으로 감싸기
  const fetchStockInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await stockAPI.getStock(stockId);
      setStock(response.data);
      
      // 토론방 참여 여부 확인
      try {
        // 여기서는 간단하게 구현. 실제로는 멤버십 API가 필요할 수 있음
        const roomResponse = await stockAPI.getRoom(response.data.room.id);
        const members = roomResponse.data.members || [];
        setInRoom(members.some(member => member.id === user?.id));
      } catch (roomError) {
        console.error('Room membership check error:', roomError);
      }
      
    } catch (error) {
      console.error('Stock info loading error:', error);
      setError('종목 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [stockId, user]);

  useEffect(() => {
    if (stockId) {
      fetchStockInfo();
    }
  }, [stockId, fetchStockInfo]);

  // 토론방 입장 처리
  const handleJoinRoom = async () => {
    if (!stock?.room?.id) return;
    
    try {
      setJoining(true);
      await stockAPI.joinRoom(stock.room.id);
      setInRoom(true);
    } catch (error) {
      console.error('Join room error:', error);
      setError(error.response?.data?.error || '토론방 입장에 실패했습니다.');
    } finally {
      setJoining(false);
    }
  };

  // 토론방 퇴장 처리
  const handleLeaveRoom = async () => {
    if (!stock?.room?.id) return;
    
    try {
      setJoining(true);
      await stockAPI.leaveRoom(stock.room.id);
      setInRoom(false);
    } catch (error) {
      console.error('Leave room error:', error);
      setError(error.response?.data?.error || '토론방 퇴장에 실패했습니다.');
    } finally {
      setJoining(false);
    }
  };

  if (loading && !stock) {
    return (
      <Paper elevation={3} sx={{ p: 3, height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
        <Typography color="error" align="center">
          {error}
        </Typography>
      </Paper>
    );
  }

  if (!stock) {
    return (
      <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
        <Typography align="center">종목을 선택해주세요.</Typography>
      </Paper>
    );
  }

  const isPositive = stock.percentage_change > 0;
  const isNegative = stock.percentage_change < 0;
  const isChampion = stock.percentage_change >= 20;
  const isLoser = stock.percentage_change <= -10;

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 종목 헤더 */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5" component="h2">
            {stock.name}
          </Typography>
          <Chip 
            label={stock.symbol} 
            color="primary" 
            variant="outlined" 
            size="small"
          />
        </Box>
        
        <Box 
          sx={{ 
            mt: 1, 
            display: 'flex', 
            alignItems: 'center',
            color: isPositive ? 'success.main' : isNegative ? 'error.main' : 'text.primary'
          }}
        >
          <Typography variant="h4" component="p" sx={{ fontWeight: 'bold', mr: 1 }}>
            {Number(stock.current_price).toLocaleString()}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {isPositive ? <TrendingUpIcon color="success" /> : 
             isNegative ? <TrendingDownIcon color="error" /> : null}
            <Typography variant="body1">
              {isPositive ? '+' : ''}{stock.percentage_change}%
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
          {isChampion && (
            <Chip 
              label="챔피언 종목" 
              color="success" 
              size="small"
            />
          )}
          
          {isLoser && (
            <Chip 
              label="루저 종목" 
              color="error" 
              size="small"
            />
          )}
        </Box>
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      {/* 종목 상세 정보 */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          종목 정보
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            매입가
          </Typography>
          <Typography variant="body2">
            {Number(stock.purchase_price).toLocaleString()}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            거래량
          </Typography>
          <Typography variant="body2">
            {Number(stock.volume).toLocaleString()}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            토론방 상태
          </Typography>
          <Chip 
            label={stock.is_active ? '활성화' : '비활성화'} 
            color={stock.is_active ? 'success' : 'default'} 
            size="small"
          />
        </Box>
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      {/* 토론방 참여 버튼 */}
      <Box sx={{ mt: 'auto' }}>
        {stock.is_active ? (
          inRoom ? (
            <Button 
              variant="outlined" 
              color="error" 
              fullWidth 
              disabled={joining}
              onClick={handleLeaveRoom}
            >
              {joining ? <CircularProgress size={24} /> : '토론방 나가기'}
            </Button>
          ) : (
            <Button 
              variant="contained" 
              color="primary" 
              fullWidth 
              disabled={joining}
              onClick={handleJoinRoom}
            >
              {joining ? <CircularProgress size={24} /> : '토론방 참여하기'}
            </Button>
          )
        ) : (
          <Button 
            variant="outlined" 
            color="error" 
            fullWidth 
            disabled
          >
            비활성화된 토론방
          </Button>
        )}
      </Box>
    </Paper>
  );
};

export default StockInfo; 