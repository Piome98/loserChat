import React from 'react';
import { Box, Paper, Typography, Avatar, Chip } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';

// 챗봇 메시지 컴포넌트
const ChatbotMessage = ({ message }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        mb: 2,
        width: '100%',
        justifyContent: 'flex-start',
      }}
    >
      <Avatar 
        sx={{ 
          bgcolor: 'success.main',
          mr: 1
        }}
      >
        <SmartToyIcon />
      </Avatar>
      
      <Box sx={{
        maxWidth: '70%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
      }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          mb: 0.5,
        }}>
          <Typography variant="subtitle2" sx={{ mr: 1 }}>
            챗봇
          </Typography>
          <Chip 
            label="챔피언" 
            size="small" 
            color="success" 
            sx={{ fontSize: '0.7rem' }}
          />
        </Box>
        
        <Box sx={{ 
          position: 'relative',
          maxWidth: '100%',
        }}>
          <Paper 
            sx={{ 
              p: 1, 
              bgcolor: '#e8f5e9', // 연한 초록색 배경
              borderRadius: 1,
              wordBreak: 'break-word',
              whiteSpace: 'pre-line', // 줄바꿈 지원
            }}
          >
            <Typography variant="body2">{message.content}</Typography>
          </Paper>
          
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
        </Box>
      </Box>
    </Box>
  );
};

export default ChatbotMessage;
