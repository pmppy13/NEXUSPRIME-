from django.urls import path
from . import views

urlpatterns = [
    path('', views.withdrawal_view, name='withdrawal'),
]