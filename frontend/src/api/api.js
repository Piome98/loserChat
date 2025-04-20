import axios from 'axios';

// API 기본 설정
// const API_BASE_URL = 'http://localhost:8000/api';
const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000/api';

console.log('API URL:', API_BASE_URL); // 디버깅용 로그

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // CORS 요청 시 쿠키 전송 허용
});

// 요청 인터셉터 - 모든 요청에 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 서버 연결 오류 처리 개선
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // 서버에 연결할 수 없는 경우
    if (!error.response || error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('서버에 연결할 수 없습니다. 로컬 더미 데이터를 사용합니다.');
      
      // API 엔드포인트에 따라 더미 데이터 반환
      const url = error.config?.url || '';
      
      // 뉴스 API인 경우
      if (url.includes('crawling/naver-finance-news')) {
        return Promise.resolve({
          data: generateDummyNewsData()
        });
      }
      
      // 시장 개요 API인 경우
      if (url.includes('crawling/naver-finance-market')) {
        return Promise.resolve({
          data: generateDummyMarketData()
        });
      }
      
      // 토큰 새로고침 API인 경우
      if (url.includes('accounts/token/refresh')) {
        console.warn('토큰 갱신 요청이 실패했습니다. 더미 데이터를 사용할 수 없습니다.');
        return Promise.reject({
          response: { 
            status: 503, 
            data: { detail: '서버에 연결할 수 없어 인증을 갱신할 수 없습니다.' } 
          }
        });
      }
      
      // 로그인 API인 경우
      if (url.includes('accounts/login')) {
        console.warn('로그인 요청이 실패했습니다. 서버에 연결할 수 없습니다.');
        return Promise.reject({
          response: { 
            status: 503, 
            data: { detail: '서버에 연결할 수 없어 로그인할 수 없습니다.' } 
          }
        });
      }
    }
    
    // 그 외 오류는 정상적으로 처리
    return Promise.reject(error);
  }
);

// 더미 뉴스 데이터 생성
function generateDummyNewsData() {
  const today = new Date();
  const formattedToday = today.toLocaleDateString();
  
  return [
    {
      id: 1,
      title: '삼성전자, 신규 AI 반도체 양산 본격화... 5나노 기반',
      summary: '삼성전자가 5나노 기술 기반의 AI 반도체 양산을 본격화한다고 밝혔다.',
      source: '한국경제',
      date: formattedToday,
      url: 'https://finance.naver.com/news/',
      category: '기업',
      imageUrl: null,
      relatedSymbols: ['005930']
    },
    {
      id: 2,
      title: '원/달러 환율, 1330원 붕괴... "중국발 경기 우려에 영향"',
      summary: '원/달러 환율이 1330원 선이 무너졌다. 전문가들은 중국 경기둔화 우려와 미국 경제지표 호조로 인한 달러 강세가 원인이라고 분석...',
      source: '연합인포맥스',
      date: formattedToday,
      url: 'https://finance.naver.com/news/',
      category: '경제',
      imageUrl: null,
      relatedSymbols: []
    }
  ];
}

// 더미 시장 데이터 생성
function generateDummyMarketData() {
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
      }
    ],
    currencies: [
      {
        name: '원/달러',
        price: '1,328.50',
        change: '-8.20',
        changePercent: '-0.61%',
        status: 'down'
      }
    ],
    commodities: [
      {
        name: 'WTI',
        price: '61.53',
        change: '+0.03',
        changePercent: '+0.05%',
        status: 'up'
      }
    ]
  };
}

// 인증 관련 API
export const authAPI = {
  // 회원가입
  signup: (userData) => api.post('/accounts/signup/', userData),
  
  // 로그인
  login: (credentials) => api.post('/accounts/login/', credentials),
  
  // 유저 프로필 조회 - 에러 처리 개선
  getProfile: async () => {
    try {
      const response = await api.get('/accounts/profile/');
      return response;
    } catch (error) {
      console.error('프로필 조회 오류:', error);
      // 오류 객체를 더 안전하게 처리
      if (error.response) {
        return Promise.reject(error);
      } else {
        // 네트워크 오류나 응답이 없는 경우
        return Promise.reject({
          response: { status: 503, data: { error: '서버에 연결할 수 없습니다.' } }
        });
      }
    }
  },
  
  // 토큰 리프레시 함수 추가
  refreshToken: (refreshData) => api.post('/accounts/token/refresh/', refreshData),
  
  // 루저 배지 제거
  removeLoserBadge: () => api.post('/accounts/remove_loser_badge/'),
  
  // 루저 배지 전달
  transferLoserBadge: (username) => api.post('/accounts/transfer_loser_badge/', { username }),
  
  // 테마 변경
  changeTheme: (theme) => api.post('/accounts/customization/', { theme }),
};

// 종목/토론방 관련 API
export const stockAPI = {
  // 종목 목록 조회
  getStocks: () => api.get('/stocks/stocks/'),
  
  // 특정 종목 조회
  getStock: (stockId) => api.get(`/stocks/stocks/${stockId}/`),
  
  // 토론방 목록 조회
  getRooms: () => api.get('/stocks/rooms/'),
  
  // 특정 토론방 조회
  getRoom: (roomId) => api.get(`/stocks/rooms/${roomId}/`),
  
  // 토론방 입장
  joinRoom: (roomId) => api.post(`/stocks/rooms/${roomId}/join/`),
  
  // 토론방 퇴장
  leaveRoom: (roomId) => api.post(`/stocks/rooms/${roomId}/leave/`),
  
  // 패잔병 토론방 조회
  getLoserRoom: () => api.get('/stocks/loser-room/'),
  
  // 메시지 조회 (일반 토론방)
  getMessages: (roomId) => api.get(`/stocks/rooms/${roomId}/messages/`),
  
  // 메시지 조회 (패잔병 토론방)
  getLoserMessages: () => api.get('/stocks/loser-room/messages/'),
  
  // 메시지 전송 (일반 토론방)
  sendMessage: (roomId, content) => api.post(`/stocks/rooms/${roomId}/send-message/`, { content }),
  
  // 메시지 전송 (패잔병 토론방)
  sendLoserMessage: (content) => api.post('/stocks/loser-room/send-message/', { content, room_type: 'loser' }),
};

// 게임 관련 API
export const gameAPI = {
  // 가위바위보 게임
  playRSP: (choice) => api.post('/game/rsp/', { choice }),
  
  // 거래량 상위 종목 조회 (관리자용)
  getTopVolumeStocks: (params) => api.get('/game/stocks/top-volume/', { params }),
  
  // 종목 토론방 추가 (관리자용)
  addStockToRoom: (stockData) => api.post('/game/stocks/add-to-room/', stockData),
};

// 채팅 관련 API
export const chatAPI = {
  // 토론방 목록 조회
  getRooms: () => api.get('/chats/rooms/'),
  
  // 특정 토론방 조회
  getRoom: (roomId) => api.get(`/chats/rooms/${roomId}/`),
  
  // 메시지 조회 (일반 토론방)
  getMessages: (roomId) => api.get(`/chats/rooms/${roomId}/messages/`),
  
  // 메시지 조회 (패잔병 토론방)
  getLoserMessages: () => api.get('/chats/loser-room/messages/'),
  
  // 메시지 전송 (일반 토론방)
  sendMessage: (roomId, content) => api.post(`/chats/rooms/${roomId}/send-message/`, { content }),
  
  // 메시지 전송 (패잔병 토론방)
  sendLoserMessage: (content) => api.post('/chats/loser-room/send-message/', { content }),
};

// 사용자 관련 API
export const userAPI = {
  // 사용자 정보 조회 (포인트 사용)
  viewUserProfile: (userId) => api.post(`/accounts/view-profile/${userId}/`),
  
  // 사용자의 보유 종목 조회
  getUserStocks: (userId) => api.get(`/accounts/user-stocks/${userId}/`),
  
  // 포인트 충전 또는 미니게임 포인트 획득
  addBonusPoints: (points) => api.post('/accounts/add-bonus-points/', { points }),
};

export default api; 