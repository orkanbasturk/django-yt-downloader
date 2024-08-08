from django.contrib import admin
from django.urls import path
from downloader import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('fetch_info/', views.fetch_info, name='fetch_info'),
]
