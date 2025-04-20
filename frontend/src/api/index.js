import apiClient from './apiClient';


// api.js에서 내보내는 API 객체들 가져오기
import { authAPI, stockAPI, chatAPI, gameAPI, userAPI } from './api';

// API 모듈 내보내기
export {
  apiClient,
  authAPI,
  stockAPI,
  gameAPI,
  chatAPI,
  userAPI
};

// 기본 export
export default {
  auth: authAPI,
  stock: stockAPI,
  game: gameAPI,
  chat: chatAPI,
  user: userAPI
}; 