from django.urls import path
from . import views

urlpatterns = [
    path('me/',        views.user_me,     name='user_me'),
    path('me/update/', views.user_update, name='user_update'),
    path('me/delete/', views.user_delete, name='user_delete'),
]
