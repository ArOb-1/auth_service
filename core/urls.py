from django.urls import path, include

urlpatterns = [
    path('auth/', include('auth_core.urls')),
    path('users/', include('users.urls')),
    path('',      include('business.urls')),
]
