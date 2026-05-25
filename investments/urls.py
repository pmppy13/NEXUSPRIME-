from django.urls import path
from . import views

urlpatterns = [
    path('', views.investments_view, name='investments'),
]