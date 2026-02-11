from django.urls import path
from . import views

urlpatterns = [
    path('record/', views.record_quest, name='record_quest'),
]