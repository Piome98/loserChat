import React, { useState, useRef, useEffect, useContext, useCallback } from 'react';
import { 
  Box, Paper, Typography, Divider, TextField, Button, 
  Avatar, CircularProgress, Chip, Modal, List, ListItem, 
  ListItemText, ListItemIcon, IconButton, Tooltip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import VideogameAssetIcon from '@mui/icons-material/VideogameAsset';
import { chatAPI } from '../api';
import { AuthContext } from '../contexts/AuthContext.context';

// 분리된 컴포넌트 가져오기
import ChatMessageItem from './chat/ChatMessageItem';
import ChatInputArea from './chat/ChatInputArea';
import UserProfileModal from './chat/UserProfileModal';
import ProfileConfirmationModal from './chat/ProfileConfirmationModal';
import { viewOwnProfile, viewUserProfile } from '../services/userProfileService';
import ChatbotMessage from './chat/ChatbotMessage';
import { processBotCommand, getBotWelcomeMessage, isBotMessage } from '../services/chatbotService';

const ChatRoom = ({ roomId, roomType = 'stock' }) => {
  const { user } = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const [participantsCount, setParticipantsCount] = useState(0);
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  
  // 사용자 프로필 관련 상태 추가
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userStocks, setUserStocks] = useState([]);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  // 1. 먼저 loadMessages 함수를 정의
  const loadMessages = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      let response;
      if (roomType === 'loser') {
        response = await chatAPI.getLoserMessages();
      } else {
        response = await chatAPI.getMessages(roomId);
      }
      
      setMessages(response.data.results || []);
      setParticipantsCount(response.data.participants_count || 0);
    } catch (error) {
      console.error('메시지 로딩 오류:', error);
      
      if (error.response?.status === 400) {
        setMessages([]);
        setError('현재 채팅방에 메시지가 없습니다. 첫 메시지를 작성해보세요!');
      } else {
        setError('메시지를 불러오는데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  }, [roomId, roomType]);

  // 2. 그 다음 웹소켓 연결 useEffect
  useEffect(() => {
    let isComponentMounted = true;
    
    const connectWebSocket = async () => {
      try {
        // 초기 메시지 로드
        await loadMessages();
        
        if (!isComponentMounted) return;
        
        // 웹소켓 URL 설정
        let wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        let wsHost = 'localhost:8000';
        let wsUrl = '';
        
        if (roomType === 'loser') {
          wsUrl = `${wsProtocol}${wsHost}/ws/chat/loser-room/`;
        } else {
          wsUrl = `${wsProtocol}${wsHost}/ws/chat/rooms/${roomId}/`;
        }
        
        const token = localStorage.getItem('access_token');
        if (token) {
          wsUrl += `?token=${token}`;
        }
        
        if (socketRef.current) {
          try {
            socketRef.current.close(1000, "정상 종료");
          } catch (err) {
            console.log("이전 소켓 종료 중 오류:", err);
          }
        }
        
        if (!isComponentMounted) return;
        
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;
        
        socket.onopen = () => {
          if (!isComponentMounted) {
            socket.close(1000, "컴포넌트 언마운트");
            return;
          }
          
          console.log('WebSocket 연결 성공');
          setConnected(true);
          setError(null);
        };
        
        socket.onmessage = async (event) => {
          if (!isComponentMounted) return;
          
          try {
            console.log('메시지 수신:', event.data);
            const data = JSON.parse(event.data);
            
            if (data.type === 'chat_message') {
              const newMsg = data.message;
              
              setMessages(prevMessages => {
                const exists = prevMessages.some(msg => msg.id === newMsg.id);
                if (exists) {
                  return prevMessages;
                }
                
                // processBotCommand가 Promise를 반환하므로 여기서는 직접 호출할 수 없음
                // 응답을 따로 처리하는 로직으로 변경
                return [...prevMessages, newMsg];
              });
              
              // 새 메시지가 자신의 메시지이고 명령어라면 봇 응답을 처리
              if (newMsg.user?.username === user?.username && 
                  newMsg.content?.startsWith('!')) {
                console.log('챗봇 명령어 감지:', newMsg.content);
                // 비동기 처리를 위해 separate effect로 처리
                const botResponse = await processBotCommand(newMsg.content, user);
                console.log('챗봇 응답 결과:', botResponse);
                if (botResponse) {
                  setMessages(prev => [...prev, botResponse]);
                }
              }
            } else if (data.type === 'user_joined') {
              setParticipantsCount(data.participants_count);
              
              if (data.username && data.username !== user?.username) {
                const welcomeMessage = {
                  id: `bot-welcome-user-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
                  content: `${data.username}님이 입장하셨습니다. 환영합니다! 미니게임을 하려면 '!게임'을 입력해보세요.`,
                  created_at: new Date().toISOString(),
                  user: {
                    id: 0,
                    username: 'chatbot',
                    nickname: '챗봇',
                    has_champion_badge: true
                  }
                };
                
                setMessages(prev => {
                  const welcomeExists = prev.some(
                    msg => msg.user?.username === 'chatbot' && 
                          msg.content.includes(`${data.username}님이 입장하셨습니다`)
                  );
                  
                  if (!welcomeExists) {
                    return [...prev, welcomeMessage];
                  }
                  return prev;
                });
              }
            } else if (data.type === 'user_left') {
              setParticipantsCount(data.participants_count);
            } else if (data.type === 'connection_established') {
              console.log('연결 확립 메시지 수신:', data);
              setError(null);
            }
          } catch (e) {
            console.error('WebSocket 메시지 처리 오류:', e);
          }
        };
        
        socket.onclose = (event) => {
          if (!isComponentMounted) return;
          
          console.log('WebSocket 연결 종료:', event.code, event.reason);
          setConnected(false);
          
          if (event.code !== 1000 && event.code !== 1001) {
            setError('채팅 서버 연결이 종료되었습니다. 재연결 중...');
          }
          
          if (event.code !== 1000 && isComponentMounted) {
            console.log('3초 후 재연결 시도...');
            setTimeout(() => {
              if (isComponentMounted && socketRef.current === socket) {
                connectWebSocket();
              }
            }, 3000);
          }
        };
        
        socket.onerror = (error) => {
          if (!isComponentMounted) return;
          console.error('WebSocket 오류:', error);
        };
      } catch (err) {
        console.error("WebSocket 연결 중 오류:", err);
        if (isComponentMounted) {
          setError('채팅 서버 연결에 실패했습니다. 잠시 후 다시 시도하세요.');
        }
      }
    };
    
    connectWebSocket();
    
    return () => {
      isComponentMounted = false;
      
      if (socketRef.current) {
        console.log('WebSocket 연결 정리');
        try {
          socketRef.current.close(1000, "정상 종료");
        } catch (err) {
          console.log("소켓 종료 중 오류:", err);
        }
        socketRef.current = null;
      }
    };
  }, [roomId, roomType, user, loadMessages]);

  // 새 메시지가 추가될 때 스크롤 최하단으로 이동
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // 사용자 입장 시 챗봇 메시지 표시
  useEffect(() => {
    if (messages.length > 0 && user && !messages.some(msg => isBotMessage(msg))) {
      const timer = setTimeout(() => {
        const welcomeMessage = getBotWelcomeMessage(user.username);
        setMessages(prev => [...prev, welcomeMessage]);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [messages, user]);

  // 메시지 전송 핸들러
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;
    
    const messageContent = newMessage.trim();
    setNewMessage('');
    
    try {
      setLoading(true);
      
      if (connected && socketRef.current) {
        socketRef.current.send(JSON.stringify({
          type: 'chat_message',
          content: messageContent,
          room_type: roomType,
          room_id: roomType === 'loser' ? null : roomId
        }));
        // 웹소켓으로 전송했을 때는 onmessage 이벤트에서 처리됨
      } else {
        // 웹소켓 연결이 없을 때는 HTTP API로 전송
        if (roomType === 'loser') {
          await chatAPI.sendLoserMessage(messageContent);
        } else {
          await chatAPI.sendMessage(roomId, messageContent);
        }
        
        // 메시지 로드 후 명령어 처리
        await loadMessages();
        
        // 명령어 처리 - 비동기 처리 개선
        if (messageContent.startsWith('!')) {
          console.log('HTTP 전송 후 챗봇 명령어 처리:', messageContent);
          const botResponse = await processBotCommand(messageContent, user);
          console.log('HTTP 전송 후 챗봇 응답 결과:', botResponse);
          if (botResponse) {
            setMessages(prev => [...prev, botResponse]);
          }
        }
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      setError('메시지 전송에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  // 사용자 아이콘 클릭 핸들러
  const handleUserClick = async (clickedUser) => {
    // 자기 자신의 프로필은 포인트 없이 볼 수 있음
    if (clickedUser.username === user?.username) {
      setSelectedUser(clickedUser);
      try {
        setLoadingProfile(true);
        setProfileError(null);
        
        const result = await viewOwnProfile(clickedUser.id);
        if (result.success) {
          setUserStocks(result.data);
        } else {
          setProfileError(result.error);
          setUserStocks([]);
        }
      } finally {
        setLoadingProfile(false);
        setProfileModalOpen(true);
      }
      return;
    }
    
    // 다른 사용자의 프로필은 확인 모달 표시
    setSelectedUser(clickedUser);
    setShowConfirmation(true);
  };
  
  // 프로필 보기 확정 핸들러 (20포인트 사용)
  const handleConfirmViewProfile = async () => {
    try {
      setLoadingProfile(true);
      setProfileError(null);
      setShowConfirmation(false);
      
      const result = await viewUserProfile(selectedUser.id);
      if (result.success) {
        setUserStocks(result.data);
      } else {
        setProfileError(result.error);
        setUserStocks([]);
      }
      
      // 모달 열기
      setProfileModalOpen(true);
    } finally {
      setLoadingProfile(false);
    }
  };
  
  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setProfileModalOpen(false);
    setShowConfirmation(false);
    setSelectedUser(null);
    setUserStocks([]);
    setProfileError(null);
  };

  return (
    <Paper elevation={1} sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden',
      borderRadius: 0,
      p: 0,
      m: 0,
      width: '100%',
    }}>
      {/* 채팅방 헤더 */}
      <Box sx={{ 
        p: 1.5, 
        bgcolor: roomType === 'loser' ? '#ff9800' : '#2196f3', 
        color: 'white',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h6">
          {roomType === 'loser' ? '패잔병 토론방' : '종목 토론방'}
          {!connected && <span> (연결 중...)</span>}
        </Typography>
        
        <Chip 
          label={`참여자: ${participantsCount}명`} 
          size="small" 
          sx={{ 
            color: 'white', 
            bgcolor: 'rgba(255,255,255,0.2)', 
            '& .MuiChip-label': { px: 1 } 
          }} 
        />
      </Box>
      
      <Divider />
      
      {/* 메시지 영역 - 스크롤바 개선 */}
      <Box sx={{ 
        flexGrow: 1, 
        p: 1.5, 
        overflowY: 'scroll',
        overflowX: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: roomType === 'loser' ? '#fff8e1' : '#f5f5f5',
        // 스크롤바 스타일
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'rgba(0,0,0,0.05)',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: roomType === 'loser' ? 'rgba(255,152,0,0.5)' : 'rgba(33,150,243,0.5)',
          '&:hover': {
            backgroundColor: roomType === 'loser' ? 'rgba(255,152,0,0.7)' : 'rgba(33,150,243,0.7)',
          }
        }
      }}>
        {loading && messages.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : messages.length > 0 ? (
          <Box sx={{ width: '100%' }}>
            {/* 메시지 갯수 표시 */}
            <Box sx={{ textAlign: 'center', mb: 2, opacity: 0.7 }}>
              <Typography variant="caption">
                총 {messages.length}개 메시지 (최대 300개까지 표시)
              </Typography>
            </Box>
            
            {/* 메시지 목록 - 분리된 컴포넌트 사용 */}
            {messages.filter(message => message && message.id && typeof message.id.toString === 'function' && !message.id.toString().startsWith('temp-')).map((message) => {
              // 챗봇 메시지인 경우 전용 컴포넌트 사용
              if (isBotMessage(message)) {
                return <ChatbotMessage key={message.id} message={message} />;
              }
              
              // 일반 메시지는 기존 처리 방식 유지
              return (
                <ChatMessageItem 
                  key={message.id}
                  message={message}
                  currentUser={user}
                  onUserClick={handleUserClick}
                />
              );
            })}
            
            {/* 스크롤 위치 참조 */}
            <div ref={messagesEndRef} />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column' }}>
            <Typography color="textSecondary" sx={{ mb: 2 }}>
              아직 메시지가 없습니다.
            </Typography>
            <Typography color="textSecondary" variant="body2">
              첫 메시지를 작성해보세요!
            </Typography>
          </Box>
        )}
        
        {error && (
          <Typography color="error" align="center" sx={{ my: 2 }}>
            {error}
          </Typography>
        )}
      </Box>
      
      <Divider />
      
      {/* 메시지 입력 영역 - 분리된 컴포넌트 사용 */}
      <ChatInputArea 
        newMessage={newMessage}
        setNewMessage={setNewMessage}
        handleSendMessage={handleSendMessage}
        connected={connected}
        loading={loading}
        roomType={roomType}
      />
      
      {/* 사용자 프로필 확인 모달 - 분리된 컴포넌트 사용 */}
      <UserProfileModal 
        open={profileModalOpen}
        onClose={handleCloseModal}
        selectedUser={selectedUser}
        userStocks={userStocks}
        loading={loadingProfile}
        error={profileError}
      />
      
      {/* 프로필 확인 확인 모달 - 분리된 컴포넌트 사용 */}
      <ProfileConfirmationModal 
        open={showConfirmation}
        onClose={() => setShowConfirmation(false)}
        onConfirm={handleConfirmViewProfile}
        selectedUser={selectedUser}
        loading={loadingProfile}
        currentUserPoints={user?.bonus_points}
      />
    </Paper>
  );
};

export default ChatRoom; 