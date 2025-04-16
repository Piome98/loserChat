import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, Button, Link, Container, Avatar, Alert, Tabs, Tab, Divider } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const { login, signup, error } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    nickname: '',
    confirmPassword: '',
  });
  const [formErrors, setFormErrors] = useState({});
  const [loading, setLoading] = useState(false);

  // 탭 변경 핸들러
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setFormErrors({});
  };

  // 입력 필드 변경 핸들러
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // 입력 시 해당 필드 에러 제거
    if (formErrors[name]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // 폼 유효성 검사
  const validateForm = () => {
    const errors = {};
    
    // 로그인 폼 유효성 검사
    if (activeTab === 0) {
      if (!formData.username) errors.username = '아이디를 입력해주세요.';
      if (!formData.password) errors.password = '비밀번호를 입력해주세요.';
    } 
    // 회원가입 폼 유효성 검사
    else {
      if (!formData.username) errors.username = '아이디를 입력해주세요.';
      if (!formData.password) errors.password = '비밀번호를 입력해주세요.';
      if (formData.password.length < 8) errors.password = '비밀번호는 8자 이상이어야 합니다.';
      if (formData.password !== formData.confirmPassword) errors.confirmPassword = '비밀번호가 일치하지 않습니다.';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 로그인 제출 핸들러
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      const result = await login({
        username: formData.username,
        password: formData.password,
      });
      
      if (result) {
        navigate('/');
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 회원가입 제출 핸들러
  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      const result = await signup({
        username: formData.username,
        password: formData.password,
        nickname: formData.nickname || '',
      });
      
      if (result) {
        // 회원가입 성공 시 로그인 탭으로 이동
        setActiveTab(0);
        setFormData((prev) => ({
          ...prev,
          password: '',
          confirmPassword: '',
        }));
      }
    } catch (error) {
      console.error('Signup error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container 
      maxWidth="sm" 
      sx={{ 
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
          {activeTab === 0 ? <LockOutlinedIcon /> : <PersonAddIcon />}
        </Avatar>
        
        <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
          루저챗에 오신 것을 환영합니다
        </Typography>
        
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ width: '100%', mb: 3 }}
        >
          <Tab label="로그인" />
          <Tab label="회원가입" />
        </Tabs>
        
        {error && (
          <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {/* 로그인 폼 */}
        {activeTab === 0 && (
          <Box component="form" onSubmit={handleLoginSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="아이디"
              name="username"
              autoComplete="username"
              autoFocus
              value={formData.username}
              onChange={handleChange}
              error={!!formErrors.username}
              helperText={formErrors.username}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="비밀번호"
              type="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              error={!!formErrors.password}
              helperText={formErrors.password}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              로그인
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link 
                component="button" 
                variant="body2" 
                onClick={() => setActiveTab(1)}
              >
                계정이 없으신가요? 회원가입
              </Link>
            </Box>
          </Box>
        )}
        
        {/* 회원가입 폼 */}
        {activeTab === 1 && (
          <Box component="form" onSubmit={handleSignupSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="아이디"
              name="username"
              autoComplete="username"
              autoFocus
              value={formData.username}
              onChange={handleChange}
              error={!!formErrors.username}
              helperText={formErrors.username}
            />
            <TextField
              margin="normal"
              fullWidth
              id="nickname"
              label="닉네임 (선택)"
              name="nickname"
              autoComplete="nickname"
              value={formData.nickname}
              onChange={handleChange}
              error={!!formErrors.nickname}
              helperText={formErrors.nickname}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="비밀번호"
              type="password"
              id="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              error={!!formErrors.password}
              helperText={formErrors.password}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="비밀번호 확인"
              type="password"
              id="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={!!formErrors.confirmPassword}
              helperText={formErrors.confirmPassword}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              회원가입
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link 
                component="button" 
                variant="body2" 
                onClick={() => setActiveTab(0)}
              >
                이미 계정이 있으신가요? 로그인
              </Link>
            </Box>
          </Box>
        )}
        
        <Divider sx={{ width: '100%', my: 3 }} />
        
        <Typography variant="body2" color="text.secondary" align="center">
          종목 토론 및 정보 공유 커뮤니티
        </Typography>
      </Paper>
    </Container>
  );
};

export default LoginPage; 