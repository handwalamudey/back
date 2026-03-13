from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PollingStationViewSet, VoterViewSet, SendMessageView, SMSWebhookView, WhatsAppWebhookView
from .auth_views import RegisterAPI, LoginAPI, UserAPI

router = DefaultRouter()
router.register(r'stations', PollingStationViewSet)
router.register(r'voters', VoterViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('messages/send/', SendMessageView.as_view(), name='send_message'),
    path('webhooks/sms/', SMSWebhookView.as_view(), name='sms_webhook'),
    path('webhooks/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('auth/register/', RegisterAPI.as_view(), name='register'),
    path('auth/login/', LoginAPI.as_view(), name='login'),
    path('auth/user/', UserAPI.as_view(), name='user'),
]
