import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { AuthProvider } from './contexts/AuthContextProvider'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import MainPage from './pages/MainPage'
import './App.css'
import { Box } from '@mui/material'

// 보호된 라우트 컴포넌트
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  // 로딩 중일 때는 아무것도 렌더링하지 않음
  if (loading) return null;
  
  // 인증되지 않은 사용자는 로그인 페이지로 리다이렉트
  if (!user) return <Navigate to="/login" />;
  
  // 인증된 사용자는 자식 컴포넌트 렌더링
  return children;
};

function App() {
  // 테마 설정
  const theme = createTheme({
    palette: {
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#9c27b0',
      },
      error: {
        main: '#f44336',
      },
      warning: {
        main: '#ff9800',
      },
      success: {
        main: '#4caf50',
      },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Box 
            sx={{ 
              width: '100%', 
              height: '100vh', 
              margin: '0 auto',
              maxWidth: '1400px', // 최대 너비 설정
            }}
          >
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route 
                path="/" 
                element={
                  <ProtectedRoute>
                    <MainPage />
                  </ProtectedRoute>
                } 
              />
              {/* 알 수 없는 경로는 메인 페이지로 리다이렉트 */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Box>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
