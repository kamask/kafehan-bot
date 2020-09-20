from django.urls import path
from .views import *
from config import WEBHOOK_TOKEN

urlpatterns = [
    path('yk/' + WEBHOOK_TOKEN + '/', yk),
    path('tg/' + WEBHOOK_TOKEN + '/', tg),
]
