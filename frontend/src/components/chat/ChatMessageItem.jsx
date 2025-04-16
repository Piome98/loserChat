import React from 'react';
import { Box, Avatar, Typography, Paper, Chip, Tooltip } from '@mui/material';
import { isBotMessage } from '../../services/chatbotService';

const ChatMessageItem = ({ 
  message, 
  currentUser, 
  onUserClick 
}) => {
  // 챗봇 메시지는 별도 컴포넌트에서 처리
  if (isBotMessage(message)) {
    return null;
  }
  
  const isMyMessage = message.user?.username === currentUser?.username;
  
  return (
    <Box
      sx={{
        display: 'flex',
        mb: 3,
        width: '100%',
        justifyContent: isMyMessage ? 'flex-end' : 'flex-start',
      }}
    >
      {/* 다른 사용자 메시지일 때만 아바타를 앞에 배치 */}
      {!isMyMessage && (
        <Tooltip title="사용자 정보 보기">
          <Avatar 
            sx={{ 
              bgcolor: message.user?.has_loser_badge ? 'error.main' : 
                      message.user?.has_champion_badge ? 'success.main' : 'primary.main',
              mr: 1,
              cursor: 'pointer',
              '&:hover': {
                opacity: 0.8,
                boxShadow: '0 0 5px rgba(0,0,0,0.3)',
              }
            }}
            onClick={() => onUserClick(message.user)}
          >
            {message.user?.username?.charAt(0).toUpperCase() || '?'}
          </Avatar>
        </Tooltip>
      )}
      
      <Box sx={{
        maxWidth: '50%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: isMyMessage ? 'flex-end' : 'flex-start',
      }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          mb: 0.5,
          width: '100%',
          justifyContent: isMyMessage ? 'flex-end' : 'flex-start',
        }}>
          <Typography variant="subtitle2" sx={{ mr: 1 }}>
            {message.user?.nickname || message.user?.username || '익명'}
          </Typography>
          {message.user?.has_loser_badge && (
            <Chip 
              label="루저" 
              size="small" 
              color="error" 
              sx={{ mr: 0.5, fontSize: '0.7rem' }}
            />
          )}
          {message.user?.has_champion_badge && (
            <Chip 
              label="챔피언" 
              size="small" 
              color="success" 
              sx={{ fontSize: '0.7rem' }}
            />
          )}
        </Box>
        
        <Box sx={{ 
          position: 'relative',
          maxWidth: '100%',
        }}>
          <Paper 
            sx={{ 
              p: 1, 
              bgcolor: isMyMessage ? '#e3f2fd' : 'white',
              borderRadius: 1,
              wordBreak: 'break-word',
            }}
          >
            <Typography variant="body2">{message.content}</Typography>
          </Paper>
          
          {/* 내 메시지: 왼쪽 아래 시간 표시 */}
          {isMyMessage && (
            <Typography 
              variant="caption" 
              color="textSecondary"
              sx={{ 
                position: 'absolute',
                bottom: -15,
                left: 0,
                fontSize: '0.6rem',
                lineHeight: 1,
              }}
            >
              {message.created_at ? new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ''}
            </Typography>
          )}
          
          {/* 다른 사용자 메시지: 오른쪽 아래 시간 표시 */}
          {!isMyMessage && (
            <Typography 
              variant="caption" 
              color="textSecondary"
              sx={{ 
                position: 'absolute',
                bottom: -15,
                right: 0,
                fontSize: '0.6rem',
                lineHeight: 1,
              }}
            >
              {message.created_at ? new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ''}
            </Typography>
          )}
        </Box>
      </Box>
      
      {/* 내 메시지일 때만 아바타를 뒤에 배치 */}
      {isMyMessage && (
        <Tooltip title="내 정보 보기">
          <Avatar 
            sx={{ 
              bgcolor: message.user?.has_loser_badge ? 'error.main' : 
                      message.user?.has_champion_badge ? 'success.main' : 'primary.main',
              ml: 1,
              cursor: 'pointer',
              '&:hover': {
                opacity: 0.8,
                boxShadow: '0 0 5px rgba(0,0,0,0.3)',
              }
            }}
            onClick={() => onUserClick(message.user)}
          >
            {message.user?.username?.charAt(0).toUpperCase() || '?'}
          </Avatar>
        </Tooltip>
      )}
    </Box>
  );
};

export default ChatMessageItem;