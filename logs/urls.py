from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='record/', permanent=False)),
    path('record/', views.record_quest, name='record_quest'),
    path('stats/', views.stats, name='stats'),
]