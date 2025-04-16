import React, { useState, useEffect, useCallback } from 'react';
import { authAPI } from '../api/api';
import { jwtDecode } from 'jwt-decode';
import { AuthContext } from './AuthContext.context';

// 컨텍스트 프로바이더 컴포넌트
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 로그아웃 함수
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  // 토큰 갱신 함수 - useCallback으로 감싸기
  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        throw new Error('Refresh token not found');
      }
      
      const response = await authAPI.refreshToken({ refresh: refreshToken });
      localStorage.setItem('access_token', response.data.access);
      
      // 사용자 정보 갱신
      const userResponse = await authAPI.getProfile();
      setUser(userResponse.data);
      
      return true;
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError);
      logout();
      return false;
    }
  }, [logout]);

  // 초기 로드 시 로컬 스토리지에서 토큰 확인
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // 토큰 유효성 검사
          const decoded = jwtDecode(token);
          const currentTime = Date.now() / 1000;
          
          if (decoded.exp < currentTime) {
            // 토큰 만료됨, 리프레시 토큰으로 갱신 시도
            await refreshToken();
          } else {
            // 유저 정보 가져오기
            try {
              const response = await authAPI.getProfile();
              setUser(response.data);
            } catch (profileError) {
              console.error('프로필 조회 실패:', profileError);
              // 프로필 조회 실패 시에도 기본 정보라도 설정
              setUser({ username: decoded.username });
            }
          }
        } catch (error) {
          console.error('Authentication error:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [refreshToken, logout]);

  // 로그인 함수
  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authAPI.login(credentials);
      
      // 토큰 저장
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      
      // 사용자 정보 가져오기
      const userResponse = await authAPI.getProfile();
      setUser(userResponse.data);
      
      return true;
    } catch (error) {
      setError(error.response?.data?.detail || '로그인에 실패했습니다.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 회원가입 함수
  const signup = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      await authAPI.signup(userData);
      return true;
    } catch (error) {
      // 에러가 객체일 경우 적절히 처리
      if (typeof error.response?.data === 'object') {
        const errorMessages = Object.entries(error.response.data)
          .map(([key, value]) => `${key}: ${value}`)
          .join(', ');
        setError(errorMessages || '회원가입에 실패했습니다.');
      } else {
        setError(error.response?.data || '회원가입에 실패했습니다.');
      }
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 제공할 값
  const value = {
    user,
    loading,
    error,
    login,
    signup,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
