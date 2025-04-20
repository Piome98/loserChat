import React, { useState, useEffect } from 'react';
import { List, ListItem, ListItemButton, ListItemText, ListItemAvatar, Avatar, Divider, Box, Typography, Paper, CircularProgress, Chip, Badge } from '@mui/material';
import { stockAPI } from '../api';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import GroupIcon from '@mui/icons-material/Group';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SentimentVeryDissatisfiedIcon from '@mui/icons-material/SentimentVeryDissatisfied';

const RoomList = ({ onRoomSelect, selectedRoomId }) => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 토론방 목록 가져오기
  const fetchRooms = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await stockAPI.getRooms();
      setRooms(response.data.results || []);
    } catch (error) {
      console.error('Room loading error:', error);
      setError('토론방 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
    
    // 1분마다 토론방 목록 갱신
    const interval = setInterval(fetchRooms, 60000);
    
    return () => clearInterval(interval);
  }, []);

  // 패잔병 토론방 선택 핸들러
  const handleLoserRoomSelect = () => {
    onRoomSelect({ id: 'loser', name: '패잔병 토론방', type: 'loser' });
  };

  // 일반 토론방 선택 핸들러
  const handleRoomSelect = (room) => {
    onRoomSelect({
      id: room.id,
      name: room.title,
      stockId: room.stock.id,
      stockSymbol: room.stock.symbol,
      type: 'stock'
    });
  };

  return (
    <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6">토론방 목록</Typography>
      </Box>
      
      <Divider />
      
      {/* 패잔병 토론방 */}
      <ListItem disablePadding>
        <ListItemButton 
          selected={selectedRoomId === 'loser'}
          onClick={handleLoserRoomSelect}
          sx={{ 
            bgcolor: 'warning.light',
            '&.Mui-selected': {
              bgcolor: 'warning.main',
            },
            '&.Mui-selected:hover': {
              bgcolor: 'warning.dark',
            },
            '&:hover': {
              bgcolor: 'warning.light',
            }
          }}
        >
          <ListItemAvatar>
            <Avatar sx={{ bgcolor: 'warning.dark' }}>
              <SentimentVeryDissatisfiedIcon />
            </Avatar>
          </ListItemAvatar>
          <ListItemText 
            primary={<Typography fontWeight="bold">패잔병 토론방</Typography>}
            secondary="루저 배지를 가진 유저들이 모이는 방"
          />
        </ListItemButton>
      </ListItem>
      
      <Divider sx={{ my: 1 }} />
      
      {/* 토론방 목록 */}
      {loading && rooms.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <ErrorOutlineIcon color="error" sx={{ fontSize: 40, mb: 1 }} />
          <Typography color="error">{error}</Typography>
        </Box>
      ) : rooms.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">토론방이 없습니다.</Typography>
        </Box>
      ) : (
        <List sx={{ flexGrow: 1, overflow: 'auto', pt: 0 }}>
          {rooms.map((room) => {
            const stock = room.stock;
            const isPositive = stock.percentage_change > 0;
            const isNegative = stock.percentage_change < 0;
            const isChampion = stock.percentage_change >= 20;
            const isLoser = stock.percentage_change <= -10;
            
            return (
              <React.Fragment key={room.id}>
                <ListItem disablePadding>
                  <ListItemButton 
                    selected={selectedRoomId === room.id}
                    onClick={() => handleRoomSelect(room)}
                    disabled={!stock.is_active}
                    sx={{ 
                      bgcolor: isLoser ? 'error.light' : isChampion ? 'success.light' : 'inherit',
                      opacity: stock.is_active ? 1 : 0.5,
                      '&.Mui-selected': {
                        bgcolor: isLoser ? 'error.light' : isChampion ? 'success.light' : 'primary.light',
                      }
                    }}
                  >
                    <ListItemAvatar>
                      <Badge
                        badgeContent={room.member_count}
                        color="primary"
                        overlap="circular"
                        anchorOrigin={{
                          vertical: 'bottom',
                          horizontal: 'right',
                        }}
                      >
                        <Avatar 
                          sx={{ 
                            bgcolor: isLoser ? 'error.main' : 
                                    isChampion ? 'success.main' : 
                                    'primary.main' 
                          }}
                        >
                          <ShowChartIcon />
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography sx={{ fontWeight: 'medium', mr: 1 }}>
                            {room.title}
                          </Typography>
                          {!stock.is_active && (
                            <Chip 
                              label="비활성화" 
                              size="small" 
                              color="default"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          )}
                          {isChampion && (
                            <Chip 
                              label="챔피언" 
                              size="small" 
                              color="success"
                              sx={{ fontSize: '0.7rem', ml: 0.5 }}
                            />
                          )}
                          {isLoser && (
                            <Chip 
                              label="루저" 
                              size="small" 
                              color="error"
                              sx={{ fontSize: '0.7rem', ml: 0.5 }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body2" component="span">
                            {stock.symbol} | {Number(stock.current_price).toLocaleString()}
                          </Typography>
                          <Box 
                            component="span" 
                            sx={{ 
                              display: 'inline-flex', 
                              alignItems: 'center',
                              ml: 1,
                              color: isPositive ? 'success.main' : 
                                     isNegative ? 'error.main' : 'text.secondary'
                            }}
                          >
                            {isPositive ? <TrendingUpIcon fontSize="small" /> : 
                             isNegative ? <TrendingDownIcon fontSize="small" /> : null}
                            <Typography variant="body2" component="span" sx={{ ml: 0.5 }}>
                              {isPositive ? '+' : ''}{stock.percentage_change}%
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            );
          })}
        </List>
      )}
    </Paper>
  );
};

export default RoomList; 