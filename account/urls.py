from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('api/auth/register/', views.register_api, name='api_register'),
    path('api/auth/login/', views.login_api, name='api_login'),
    path('api/auth/logout/', views.logout_api, name='api_logout'),
    
    # Email verification
    path('api/auth/email-verify/', views.email_verification_api, name='api_email_verification'),
    
    # Password reset
    path('api/auth/password-reset/', views.password_reset_request_api, name='api_password_reset_request'),
    path('api/auth/password-reset-confirm/', views.password_reset_confirm_api, name='api_password_reset_confirm'),
    
    # User profile endpoints
    path('api/user/profile/', views.user_profile_api, name='api_user_profile'),
    path('api/user/dashboard/', views.dashboard_api, name='api_dashboard'),
    path('api/user/profile-management/', views.profile_management_api, name='api_profile_management'),
    path('api/user/delete-account/', views.delete_account_api, name='api_delete_account'),
]