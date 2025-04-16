from django.urls import path
from .views import play_rock_scissors_papers as play_rps
from .views import get_top_volume_stocks, add_stock_to_room

urlpatterns = [
    path('rsp/', play_rps),
    path('stocks/top-volume/', get_top_volume_stocks, name='top_volume_stocks'),
    path('stocks/add-to-room/', add_stock_to_room, name='add_stock_to_room'),
]
