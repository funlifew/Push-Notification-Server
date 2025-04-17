from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name='register'),
    path("login/", views.LoginView.as_view(), name='login'),
    path("logout/", views.LogoutView.as_view(), name='logout'),
    path('password/change/', views.ChangePasswordView.as_view(), name="change_password"),
    path("password/reset/request/", views.ResetPasswordRequestView.as_view(), name="reset_password_request"),
    path("password/reset/verify/", views.ResetPasswordVerifyView.as_view(), name="reset_password_verify"),
    path("password/reset/", views.ResetPasswordView.as_view(), name='reset_password'),
    path("profile/", views.ProfileView.as_view(), name='profile'),
    path("otp/verify/", views.VerifyOTPView.as_view(), name='otp_verify'),
    path('otp/refresh/', views.RefreshTokenView.as_view(), name='otp_refresh'),
    
    # تغییر این مسیر به یک ویو سفارشی برای خواندن توکن از کوکی
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("number/change/", views.ChangePhoneNumberView.as_view(), name="change_number"),
    path("number/edit/", views.EditPhoneNumberView.as_view(), name="edit_number"),
]
