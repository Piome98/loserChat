// 챗봇 서비스 - 챗봇 메시지 및 명령어 처리

// 더 안전한 고유 ID 생성 함수 추가
let botMessageCounter = 0;
const generateBotMessageId = (prefix) => {
  botMessageCounter++;
  return `${prefix}-${Date.now()}-${botMessageCounter}-${Math.random().toString(36).substring(2, 7)}`;
};

// 챗봇 환영 메시지
export const getBotWelcomeMessage = (username) => {
  return {
    id: generateBotMessageId('bot-welcome'),
    content: `안녕하세요 ${username}님! 미니게임 챗봇입니다. 
명령어 목록을 보려면 '!명령어'를 입력해주세요.`,
    created_at: new Date().toISOString(),
    user: {
      id: 0,
      username: 'chatbot',
      nickname: '챗봇',
      has_champion_badge: true
    }
  };
};

// 챗봇 명령어 목록
export const getCommandListMessage = () => {
  return {
    id: generateBotMessageId('bot-commands'),
    content: `📋 명령어 목록:
!명령어 - 사용 가능한 명령어 목록 표시
!게임 - 미니게임 목록 표시
!포인트 - 보유 포인트 확인
!랭킹 - 포인트 랭킹 확인

미니게임에서 승리하면 보너스 포인트를 획득할 수 있습니다!`,
    created_at: new Date().toISOString(),
    user: {
      id: 0,
      username: 'chatbot',
      nickname: '챗봇',
      has_champion_badge: true
    }
  };
};

// 챗봇 게임 목록
export const getGameListMessage = () => {
  return {
    id: generateBotMessageId('bot-games'),
    content: `🎮 미니게임 목록:
!가위바위보 - 가위바위보 게임 시작
!주사위 - 주사위 게임 시작
!숫자맞추기 - 1~100 사이 숫자 맞추기 게임
!퀴즈 - 주식 관련 퀴즈 풀기

더 많은 게임이 업데이트될 예정입니다!`,
    created_at: new Date().toISOString(),
    user: {
      id: 0,
      username: 'chatbot',
      nickname: '챗봇',
      has_champion_badge: true
    }
  };
};

// 포인트 확인 메시지
export const getPointCheckMessage = (user) => {
  return {
    id: generateBotMessageId('bot-points'),
    content: `💰 ${user.nickname || user.username}님의 보유 포인트: ${user.bonus_points || 0} 포인트
    
매일 첫 접속 시 10포인트가 지급됩니다.
미니게임에서 승리하면 추가 포인트를 획득할 수 있습니다!`,
    created_at: new Date().toISOString(),
    user: {
      id: 0,
      username: 'chatbot',
      nickname: '챗봇',
      has_champion_badge: true
    }
  };
};

// 챗봇 명령어 처리
export const processBotCommand = (command, user) => {
  const lowerCommand = command.toLowerCase();
  
  // 명령어 처리
  if (lowerCommand === '!챗봇' || lowerCommand === '!명령어') {
    return getCommandListMessage();
  } 
  else if (lowerCommand === '!게임') {
    return getGameListMessage();
  }
  else if (lowerCommand === '!포인트') {
    return getPointCheckMessage(user);
  }
  else if (lowerCommand === '!랭킹') {
    return {
      id: generateBotMessageId('bot-ranking'),
      content: `🏆 현재 포인트 랭킹은 준비 중입니다. 곧 업데이트될 예정입니다!`,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  }
  // 지원하지 않는 명령어
  else if (lowerCommand.startsWith('!')) {
    return {
      id: generateBotMessageId('bot-unknown'),
      content: `❓ 알 수 없는 명령어입니다. '!명령어'를 입력하여 사용 가능한 명령어를 확인하세요.`,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  }
  
  // 명령어가 아닌 경우 null 반환
  return null;
};

// 챗봇 메시지인지 확인
export const isBotMessage = (message) => {
  return message.user?.username === 'chatbot';
};
