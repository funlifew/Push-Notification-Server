from django.urls import path
from . import views

urlpatterns = [
    path("token/generate/", views.GenerateAdminTokenView.as_view(), name="generate_token"),
    path("send/single/", views.SendSingleNotificationView.as_view(), name="send_single"),
    path("send/group/", views.SendGroupNotificationView.as_view(), name="send_group"),
]
