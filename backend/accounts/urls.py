# accounts/urls.py
# API 경로 등록

from django.urls import path
from .views import (
    signup_view,
    user_profile,
    remove_loser_badge,
    customization_theme,
    transfer_loser_badge,
    view_user_profile,
    get_user_stocks,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('signup/', signup_view),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', user_profile, name='user_profile'),
    path('remove_loser_badge/', remove_loser_badge, name='remove_loser_badge'),
    path('transfer_loser_badge/', transfer_loser_badge, name='transfer_loser_badge'),
    path('customization/', customization_theme, name='customization_theme'),
    path('user-stocks/<int:user_id>/', get_user_stocks, name='user-stocks'),
    path('view-profile/<int:user_id>/', view_user_profile, name='view-profile'),
]




# refresh_token -> 장기 인증용 토큰(access token 재발급용)
# access_token -> 단기 인증용 토큰(로그인 인증용)