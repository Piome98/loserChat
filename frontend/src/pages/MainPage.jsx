import React, { useState } from 'react';
import { 
  Box, Paper, Typography, AppBar, Toolbar, Button, Avatar, 
  Chip, Menu, MenuItem, IconButton, Tabs, Tab, useMediaQuery, 
  useTheme
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import PersonRemoveIcon from '@mui/icons-material/PersonRemove';
import ColorLensIcon from '@mui/icons-material/ColorLens';
import GamesIcon from '@mui/icons-material/Games';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import NewspaperIcon from '@mui/icons-material/Newspaper';
import InfoIcon from '@mui/icons-material/Info';

import RoomList from '../components/RoomList';
import ChatRoom from '../components/ChatRoom';
import StockInfo from '../components/StockInfo';
import NewsFeed from '../components/NewsFeed';
import MarketOverview from '../components/MarketOverview';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../api/api';

const MainPage = () => {
  const { user, logout } = useAuth();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  
  const [leftSection, setLeftSection] = useState('roomList');
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [menuAnchor, setMenuAnchor] = useState(null);
  
  // 오른쪽 섹션 탭 관련 state
  const [activeTab, setActiveTab] = useState('market');
  
  // 탭 변경 핸들러
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // 토론방 선택 핸들러
  const handleRoomSelect = (room) => {
    setSelectedRoom(room);
    setLeftSection('chatRoom');
    
    // 종목 토론방 선택 시 해당 종목 정보 탭으로 바로 전환
    if (room.type === 'stock') {
      setActiveTab('stockInfo'); // 탭을 '종목 정보'로 변경
    }
  };
  
  // 토론방 목록으로 돌아가기
  const handleBackToList = () => {
    setLeftSection('roomList');
  };
  
  // 메뉴 열기/닫기
  const handleMenuOpen = (event) => {
    setMenuAnchor(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  // 메뉴 아이템
  const menuItems = [
    {
      label: '로그아웃',
      icon: <LogoutIcon fontSize="small" />,
      action: () => {
        logout();
        handleMenuClose();
      }
    },
    {
      label: '루저 배지 제거',
      icon: <PersonRemoveIcon fontSize="small" />,
      disabled: !user?.loser_badge_count || user?.bonus_points < 50,
      action: async () => {
        try {
          await authAPI.removeLoserBadge();
          // 사용자 정보 갱신 로직
        } catch (error) {
          console.error('Failed to remove loser badge:', error);
        }
        handleMenuClose();
      }
    },
    {
      label: '테마 변경',
      icon: <ColorLensIcon fontSize="small" />,
      action: () => {
        // 테마 변경 로직
        handleMenuClose();
      }
    }
  ];

  // 렌더링할 왼쪽 섹션 컨텐츠 결정
  const renderLeftSection = () => {
    switch(leftSection) {
      case 'roomList':
        return (
          <RoomList 
            onRoomSelect={handleRoomSelect}
            selectedRoomId={selectedRoom?.id}
          />
        );
      case 'chatRoom':
        return (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ 
              flexGrow: 1, 
              display: 'flex', 
              flexDirection: 'column',
              overflow: 'hidden',
            }}>
              <ChatRoom 
                roomId={selectedRoom?.id === 'loser' ? null : selectedRoom?.id}
                roomType={selectedRoom?.type}
              />
            </Box>
          </Box>
        );
      default:
        return (
          <Paper sx={{ 
            height: '100%', 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center' 
          }}>
            <Typography color="text.secondary">
              콘텐츠를 찾을 수 없습니다.
            </Typography>
          </Paper>
        );
    }
  };

  // 렌더링할 오른쪽 섹션 컨텐츠 결정
  const renderRightSection = () => {
    // 탭 기반 UI로 통합
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* 탭 헤더 */}
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            '& .MuiTab-root': { 
              minHeight: '48px',
              fontWeight: 'medium'
            }
          }}
        >
          <Tab 
            icon={<ShowChartIcon fontSize="small" />}
            iconPosition="start" 
            label="시장 개요" 
            value="market" 
          />
          <Tab 
            icon={<NewspaperIcon fontSize="small" />}
            iconPosition="start" 
            label="경제 뉴스" 
            value="news" 
          />
          {selectedRoom?.type === 'stock' && (
            <Tab 
              icon={<InfoIcon fontSize="small" />}
              iconPosition="start" 
              label="종목 정보" 
              value="stockInfo" 
            />
          )}
        </Tabs>
        
        {/* 탭 콘텐츠 */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}>
          {/* 시장 개요 탭 */}
          {activeTab === 'market' && (
            <Box sx={{ width: '100%', height: '100%' }}>
              <MarketOverview />
            </Box>
          )}
          
          {/* 경제 뉴스 탭 */}
          {activeTab === 'news' && (
            <Box sx={{ width: '100%', height: '100%' }}>
              <NewsFeed />
            </Box>
          )}
          
          {/* 종목 정보 탭 */}
          {activeTab === 'stockInfo' && selectedRoom?.type === 'stock' && (
            <Box sx={{ width: '100%', height: '100%', p: 1 }}>
              <Paper 
                elevation={1} 
                sx={{ 
                  height: '100%', 
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h6" gutterBottom>
                  {selectedRoom?.name} 정보
                </Typography>
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  <StockInfo stockId={selectedRoom?.stockId} />
                </Box>
              </Paper>
            </Box>
          )}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      overflow: 'hidden',
      margin: '0 auto',
      maxWidth: '1920px', // 16:10 비율에 적합한 최대 너비
    }}>
      {/* 앱 바 */}
      <AppBar position="static" sx={{ zIndex: 1100 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            루저챗
          </Typography>
          
          <IconButton 
            color="inherit" 
            sx={{ mr: 1 }}
          >
            <GamesIcon />
          </IconButton>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {user?.loser_badge_count > 0 && (
              <Chip 
                label={`루저 배지: ${user.loser_badge_count}`} 
                color="error" 
                size="small" 
                sx={{ mr: 1, height: 24 }}
              />
            )}
            
            {user?.champion_badge_count > 0 && (
              <Chip 
                label={`챔피언 배지: ${user.champion_badge_count}`} 
                color="success" 
                size="small" 
                sx={{ mr: 1, height: 24 }}
              />
            )}
            
            <Chip 
              label={`${user?.bonus_points || 0} 포인트`} 
              color="secondary" 
              size="small" 
              sx={{ mr: 2, height: 24 }}
            />
            
            <Button 
              color="inherit" 
              startIcon={<Avatar sx={{ width: 24, height: 24 }}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </Avatar>}
              onClick={handleMenuOpen}
            >
              {user?.nickname || user?.username || 'User'}
            </Button>
            
            <Menu
              anchorEl={menuAnchor}
              open={Boolean(menuAnchor)}
              onClose={handleMenuClose}
            >
              {menuItems.map((item, index) => (
                <MenuItem 
                  key={index} 
                  onClick={item.action}
                  disabled={item.disabled}
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    gap: 1,
                    opacity: item.disabled ? 0.5 : 1
                  }}
                >
                  {item.icon}
                  {item.label}
                </MenuItem>
              ))}
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
      
      {/* 메인 콘텐츠 - 좌우 분할, 16:10 비율 적용 */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'hidden',
        display: 'flex', 
        flexDirection: { xs: 'column', md: 'row' },
        gap: 1, // 좌우 섹션 사이 약간의 간격
        p: 1, // 전체 패딩 약간 추가
        height: isDesktop ? 'calc(100vh - 64px)' : 'auto', // AppBar 높이 제외
      }}>
        {/* 왼쪽 섹션 */}
        <Box sx={{ 
          width: { xs: '100%', md: '40%' }, // PC에서는 40% 너비
          height: { xs: '50%', md: '100%' },
          display: 'flex',
          minHeight: isDesktop ? 'auto' : '500px', // 모바일에서 최소 높이 지정
        }}>
          <Paper 
            elevation={2}
            sx={{ 
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              height: '100%',
              borderRadius: 1, // 약간의 둥근 모서리
            }}
          >
            {leftSection === 'chatRoom' && (
              <Box sx={{ 
                p: 2, 
                bgcolor: 'primary.main', 
                color: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid rgba(0,0,0,0.1)'
              }}>
                <Button 
                  startIcon={<ArrowBackIcon />} 
                  onClick={handleBackToList}
                  variant="outlined"
                  size="small"
                  sx={{ 
                    color: 'white', 
                    borderColor: 'rgba(255,255,255,0.5)',
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: 'rgba(255,255,255,0.1)'
                    }
                  }}
                >
                  토론방 목록
                </Button>
                
                <Typography variant="h6">
                  {selectedRoom?.name || '토론방'}
                </Typography>
              </Box>
            )}
            
            <Box sx={{ 
              flexGrow: 1, 
              overflow: 'hidden', 
              display: 'flex', 
              flexDirection: 'column',
              height: leftSection === 'chatRoom' ? 'calc(100% - 56px)' : '100%'
            }}>
              {renderLeftSection()}
            </Box>
          </Paper>
        </Box>
        
        {/* 오른쪽 섹션 */}
        <Box sx={{ 
          width: { xs: '100%', md: '60%' }, // PC에서는 60% 너비로 더 넓게
          height: { xs: '50%', md: '100%' },
          display: 'flex',
          minHeight: isDesktop ? 'auto' : '500px', // 모바일에서 최소 높이 지정
        }}>
          <Paper 
            elevation={2}
            sx={{ 
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              borderRadius: 1, // 약간의 둥근 모서리
            }}
          >
            {renderRightSection()}
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default MainPage; 