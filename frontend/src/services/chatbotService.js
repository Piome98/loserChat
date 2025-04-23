// 챗봇 서비스 - 챗봇 메시지 및 명령어 처리
import { gameAPI } from '../api';

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
!가위바위보 [가위/바위/보] - 가위바위보 게임
!바카라 [플레이어/뱅커/타이] - 바카라 게임
!인디언홀덤 [콜/폴드] - 인디언 홀덤 게임

게임 방법:
- 가위바위보: !가위바위보 가위 (또는 바위, 보)
- 바카라: !바카라 플레이어 (또는 뱅커, 타이)
- 인디언홀덤: !인디언홀덤 콜 (또는 폴드)

승리 시 10포인트를 획득할 수 있습니다!`,
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

// 게임 에러 메시지
const getGameErrorMessage = (error) => {
  return {
    id: generateBotMessageId('bot-game-error'),
    content: `❌ 게임 실행 중 오류가 발생했습니다: ${error}`,
    created_at: new Date().toISOString(),
    user: {
      id: 0,
      username: 'chatbot',
      nickname: '챗봇',
      has_champion_badge: true
    }
  };
};

// 가위바위보 게임 실행
const playRockScissorsPaper = async (choice) => {
  try {
    const validChoices = {
      '가위': 'scissors',
      '바위': 'rock',
      '보': 'paper',
      'scissors': 'scissors',
      'rock': 'rock',
      'paper': 'paper'
    };
    
    if (!validChoices[choice]) {
      return {
        id: generateBotMessageId('bot-rsp-error'),
        content: `❌ 잘못된 선택입니다. '가위', '바위', '보' 중 하나를 선택해주세요.
예시: !가위바위보 가위`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    const response = await gameAPI.playRSP(validChoices[choice]);
    const result = response.data;
    
    // 결과 메시지 생성
    let resultIcon = '';
    if (result.result === 'win') resultIcon = '🎉';
    else if (result.result === 'lose') resultIcon = '😢';
    else resultIcon = '🤝';
    
    const choiceEmoji = {
      'rock': '👊',
      'scissors': '✌️',
      'paper': '✋'
    };
    
    const choiceKorean = {
      'rock': '바위',
      'scissors': '가위',
      'paper': '보'
    };
    
    const resultKorean = {
      'win': '승리',
      'lose': '패배',
      'draw': '무승부'
    };
    
    let content = `🎮 가위바위보 게임 결과 ${resultIcon}

당신의 선택: ${choiceEmoji[result.user_choice]} ${choiceKorean[result.user_choice]}
봇의 선택: ${choiceEmoji[result.bot_choice]} ${choiceKorean[result.bot_choice]}
결과: ${resultKorean[result.result]}`;
    
    if (result.result === 'win') {
      content += `\n\n🎉 축하합니다! 10포인트를 획득했습니다!
현재 보유 포인트: ${result.bonus_points}`;
    }
    
    return {
      id: generateBotMessageId('bot-rsp-result'),
      content,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  } catch (error) {
    console.error('가위바위보 게임 오류:', error);
    
    // 서버에서 오류 메시지가 있는 경우
    if (error.response?.data?.error) {
      return {
        id: generateBotMessageId('bot-rsp-error'),
        content: `❌ ${error.response.data.error}`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    return getGameErrorMessage('게임 서버와 통신 중 오류가 발생했습니다.');
  }
};

// 바카라 게임 실행
const playBaccarat = async (bet) => {
  try {
    const validBets = {
      '플레이어': 'player',
      '뱅커': 'banker',
      '타이': 'tie',
      'player': 'player',
      'banker': 'banker',
      'tie': 'tie'
    };
    
    if (!validBets[bet]) {
      return {
        id: generateBotMessageId('bot-baccarat-error'),
        content: `❌ 잘못된 베팅입니다. '플레이어', '뱅커', '타이' 중 하나를 선택해주세요.
예시: !바카라 플레이어`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    const response = await gameAPI.playBaccarat(validBets[bet]);
    const result = response.data;
    
    // 결과 메시지 생성
    let resultIcon = '';
    if (result.user_result === 'win') resultIcon = '🎉';
    else resultIcon = '😢';
    
    const betKorean = {
      'player': '플레이어',
      'banker': '뱅커',
      'tie': '타이'
    };
    
    const resultKorean = {
      'win': '승리',
      'lose': '패배'
    };
    
    let content = `🎮 바카라 게임 결과 ${resultIcon}

당신의 베팅: ${betKorean[result.bet_on]}
플레이어 카드: ${result.player_cards.join(', ')} (점수: ${result.player_score})
뱅커 카드: ${result.banker_cards.join(', ')} (점수: ${result.banker_score})
결과: ${betKorean[result.result]} 승리
당신의 결과: ${resultKorean[result.user_result]}`;
    
    if (result.user_result === 'win') {
      content += `\n\n🎉 축하합니다! 10포인트를 획득했습니다!
현재 보유 포인트: ${result.bonus_points}`;
    }
    
    return {
      id: generateBotMessageId('bot-baccarat-result'),
      content,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  } catch (error) {
    console.error('바카라 게임 오류:', error);
    
    // 서버에서 오류 메시지가 있는 경우
    if (error.response?.data?.error) {
      return {
        id: generateBotMessageId('bot-baccarat-error'),
        content: `❌ ${error.response.data.error}`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    return getGameErrorMessage('게임 서버와 통신 중 오류가 발생했습니다.');
  }
};

// 인디언 홀덤 게임 실행
const playIndianHoldem = async (action) => {
  try {
    const validActions = {
      '콜': 'call',
      '폴드': 'fold',
      'call': 'call',
      'fold': 'fold'
    };
    
    if (!validActions[action]) {
      return {
        id: generateBotMessageId('bot-holdem-error'),
        content: `❌ 잘못된 액션입니다. '콜' 또는 '폴드' 중 하나를 선택해주세요.
예시: !인디언홀덤 콜`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    const response = await gameAPI.playIndianHoldem(validActions[action]);
    const result = response.data;
    
    // 결과 메시지 생성
    let resultIcon = '';
    if (result.result === 'win') resultIcon = '🎉';
    else if (result.result === 'lose') resultIcon = '😢';
    else resultIcon = '🤝';
    
    const actionKorean = {
      'call': '콜',
      'fold': '폴드'
    };
    
    const resultKorean = {
      'win': '승리',
      'lose': '패배',
      'draw': '무승부'
    };
    
    let content = `🎮 인디언 홀덤 게임 결과 ${resultIcon}

당신의 카드: ${result.user_card}
봇의 카드: ${result.bot_card}
선택한 액션: ${actionKorean[result.action]}
결과: ${resultKorean[result.result]}`;
    
    if (result.result === 'win') {
      content += `\n\n🎉 축하합니다! 10포인트를 획득했습니다!
현재 보유 포인트: ${result.bonus_points}`;
    }
    
    return {
      id: generateBotMessageId('bot-holdem-result'),
      content,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  } catch (error) {
    console.error('인디언 홀덤 게임 오류:', error);
    
    // 서버에서 오류 메시지가 있는 경우
    if (error.response?.data?.error) {
      return {
        id: generateBotMessageId('bot-holdem-error'),
        content: `❌ ${error.response.data.error}`,
        created_at: new Date().toISOString(),
        user: {
          id: 0,
          username: 'chatbot',
          nickname: '챗봇',
          has_champion_badge: true
        }
      };
    }
    
    return getGameErrorMessage('게임 서버와 통신 중 오류가 발생했습니다.');
  }
};

// 챗봇 명령어 처리
export const processBotCommand = async (command, user) => {
  try {
    if (!command || !command.startsWith('!')) {
      return null;
    }
    
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
    // 가위바위보 게임
    else if (lowerCommand.startsWith('!가위바위보') || lowerCommand.startsWith('!rsp')) {
      const parts = command.split(' ');
      if (parts.length < 2) {
        return {
          id: generateBotMessageId('bot-rsp-help'),
          content: `가위바위보 게임 방법:
!가위바위보 [가위/바위/보]

예시: !가위바위보 가위`,
          created_at: new Date().toISOString(),
          user: {
            id: 0,
            username: 'chatbot',
            nickname: '챗봇',
            has_champion_badge: true
          }
        };
      }
      
      const choice = parts[1];
      return await playRockScissorsPaper(choice);
    }
    // 바카라 게임
    else if (lowerCommand.startsWith('!바카라') || lowerCommand.startsWith('!baccarat')) {
      const parts = command.split(' ');
      if (parts.length < 2) {
        return {
          id: generateBotMessageId('bot-baccarat-help'),
          content: `바카라 게임 방법:
!바카라 [플레이어/뱅커/타이]

예시: !바카라 플레이어`,
          created_at: new Date().toISOString(),
          user: {
            id: 0,
            username: 'chatbot',
            nickname: '챗봇',
            has_champion_badge: true
          }
        };
      }
      
      const bet = parts[1];
      return await playBaccarat(bet);
    }
    // 인디언 홀덤 게임
    else if (lowerCommand.startsWith('!인디언홀덤') || lowerCommand.startsWith('!홀덤') || lowerCommand.startsWith('!holdem')) {
      const parts = command.split(' ');
      if (parts.length < 2) {
        return {
          id: generateBotMessageId('bot-holdem-help'),
          content: `인디언 홀덤 게임 방법:
!인디언홀덤 [콜/폴드]

예시: !인디언홀덤 콜`,
          created_at: new Date().toISOString(),
          user: {
            id: 0,
            username: 'chatbot',
            nickname: '챗봇',
            has_champion_badge: true
          }
        };
      }
      
      const action = parts[1];
      return await playIndianHoldem(action);
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
  } catch (error) {
    console.error('챗봇 명령어 처리 중 오류 발생:', error);
    return {
      id: generateBotMessageId('bot-error'),
      content: `⚠️ 명령어 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.`,
      created_at: new Date().toISOString(),
      user: {
        id: 0,
        username: 'chatbot',
        nickname: '챗봇',
        has_champion_badge: true
      }
    };
  }
};

// 챗봇 메시지인지 확인
export const isBotMessage = (message) => {
  return message && message.user && message.user.username === 'chatbot';
};
