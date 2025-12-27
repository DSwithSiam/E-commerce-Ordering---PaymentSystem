from django.urls import path
from users.views import (
    RegisterView,
    login_view,
    logout_view,
    profile_view,
    update_profile_view,
    change_password_view
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/update/', update_profile_view, name='update-profile'),
    path('change-password/', change_password_view, name='change-password'),
]
