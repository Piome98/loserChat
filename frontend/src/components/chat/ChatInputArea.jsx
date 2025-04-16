import React from 'react';
import { Box, TextField, Button } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatInputArea = ({ 
  newMessage, 
  setNewMessage, 
  handleSendMessage, 
  connected,
  loading,
  roomType
}) => {
  return (
    <Box sx={{ p: 1.5, bgcolor: 'background.paper' }}>
      <form onSubmit={handleSendMessage} style={{ display: 'flex' }}>
        <TextField
          fullWidth
          placeholder={connected ? "메시지 입력..." : "서버에 연결 중..."}
          variant="outlined"
          size="small"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          disabled={loading || !connected}
        />
        <Button
          type="submit"
          variant="contained"
          color={roomType === 'loser' ? 'warning' : 'primary'}
          sx={{ ml: 1 }}
          disabled={loading || !newMessage.trim() || !connected}
        >
          <SendIcon />
        </Button>
      </form>
    </Box>
  );
};

export default ChatInputArea;