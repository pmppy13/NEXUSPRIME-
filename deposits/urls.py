from django.urls import path
from . import views

urlpatterns = [
    path('', views.deposit_view, name='deposit'),
]