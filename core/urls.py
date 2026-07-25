from django.urls import path, include

urlpatterns = [
    path('auth/', include('auth_core.urls')),
    path('',      include('business.urls')),
]
