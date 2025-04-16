import React from 'react';
import { Box, Paper, Typography, Modal, Button } from '@mui/material';

const ProfileConfirmationModal = ({ 
  open, 
  onClose, 
  onConfirm, 
  selectedUser,
  loading,
  currentUserPoints 
}) => {
  const hasEnoughPoints = (currentUserPoints || 0) >= 20;

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="profile-confirmation-modal"
    >
      <Paper 
        sx={{ 
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 350,
          maxWidth: '90%',
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 3,
          borderRadius: 2,
        }}
      >
        <Typography id="confirm-title" variant="h6" component="h2" sx={{ mb: 2 }}>
          사용자 정보 확인
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 3 }}>
          <Box component="span" fontWeight="bold">{selectedUser?.username || 'User'}</Box>님의 정보를 확인하시려면 
          <Box component="span" fontWeight="bold" color="primary.main"> 20 포인트</Box>가 필요합니다.
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button 
            variant="outlined" 
            onClick={onClose}
          >
            취소
          </Button>
          <Button 
            variant="contained" 
            color="primary"
            onClick={onConfirm}
            disabled={loading || !hasEnoughPoints}
          >
            {loading ? "로딩 중..." : "확인 (20P)"}
          </Button>
        </Box>
        
        {!hasEnoughPoints && (
          <Typography color="error" sx={{ mt: 2, fontSize: '0.875rem' }}>
            포인트가 부족합니다. 미니게임에서 포인트를 획득해주세요.
          </Typography>
        )}
      </Paper>
    </Modal>
  );
};

export default ProfileConfirmationModal;