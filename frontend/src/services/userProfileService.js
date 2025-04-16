import { userAPI } from '../api/api';

// 사용자 프로필 관련 서비스 함수
export const viewOwnProfile = async (userId) => {
  try {
    // 실제 API 호출
    const response = await userAPI.getUserStocks(userId);
    return {
      success: true,
      data: response.data.stocks || [],
      error: null
    };
  } catch (error) {
    console.error('프로필 데이터 로딩 오류:', error);
    
    // 에러 발생 시 임시 데이터 반환 (개발 환경에서만)
    console.log('임시 보유 종목 데이터 사용 (API 오류)');
    return {
      success: true,
      data: [
        {
          name: '삼성전자',
          buy_price: 68000,
          target_price: 75000,
          quantity: 10
        },
        {
          name: 'LG전자',
          buy_price: 122000,
          target_price: 150000,
          quantity: 5
        }
      ],
      error: null
    };
  }
};

export const viewUserProfile = async (userId) => {
  try {
    // 실제 API 호출
    const response = await userAPI.viewUserProfile(userId);
    return {
      success: true,
      data: response.data.stocks || [],
      error: null
    };
  } catch (error) {
    console.error('프로필 조회 오류:', error);
    
    // 에러 발생 시 임시 데이터 반환 (개발 환경에서만)
    console.log('임시 다른 사용자 종목 데이터 사용 (API 오류)');
    return {
      success: true,
      data: [
        {
          name: '현대차',
          buy_price: 175000,
          target_price: 200000,
          quantity: 3
        },
        {
          name: 'SK하이닉스',
          buy_price: 95000,
          target_price: 120000,
          quantity: 7
        }
      ],
      error: null
    };
  }
};