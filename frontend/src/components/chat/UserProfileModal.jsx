import React from 'react';
import { 
  Box, Paper, Typography, Modal, List, ListItem, 
  ListItemText, ListItemIcon, IconButton, Divider, CircularProgress, Avatar
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import VideogameAssetIcon from '@mui/icons-material/VideogameAsset';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';

const UserProfileModal = ({ 
  open, 
  onClose, 
  selectedUser, 
  userStocks, 
  loading, 
  error 
}) => {
  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="user-profile-modal"
    >
      <Paper 
        sx={{ 
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          maxWidth: '90%',
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 3,
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography id="modal-title" variant="h6" component="h2">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar 
                sx={{ 
                  bgcolor: selectedUser?.has_loser_badge ? 'error.main' : 
                          selectedUser?.has_champion_badge ? 'success.main' : 'primary.main',
                }}
              >
                {selectedUser?.username?.charAt(0).toUpperCase() || '?'}
              </Avatar>
              사용자 상세 정보
            </Box>
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        ) : (
          <>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <AccountBalanceWalletIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="아이디" 
                  secondary={selectedUser?.username || 'user123'}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <MonetizationOnIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="보너스 포인트" 
                  secondary={`${selectedUser?.bonus_points || 30} 포인트`}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <VideogameAssetIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="미니게임 승리 횟수" 
                  secondary={`${selectedUser?.game_wins || 3}회`}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <EmojiEventsIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="챔피온" 
                  secondary={`${selectedUser?.champion_badge_count || 3}개`}
                />
              </ListItem>
            </List>
            
            <Divider sx={{ my: 1.5 }} />
            
            <Typography variant="h6" gutterBottom>
              보유 종목 현황
            </Typography>
            
            {userStocks.length === 0 ? (
              <Typography color="text.secondary" sx={{ py: 1 }}>
                보유 종목 정보가 없습니다.
              </Typography>
            ) : (
              <List dense>
                {userStocks.map((stock, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <ShoppingCartIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={stock.name} 
                      secondary={`매수가: ${stock.buy_price}원 / 목표가: ${stock.target_price}원`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </>
        )}
      </Paper>
    </Modal>
  );
};

export default UserProfileModal;