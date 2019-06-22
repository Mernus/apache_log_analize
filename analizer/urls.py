from django.urls import path
from . import views

app_name = 'analizer'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('stats/<int:pk_log>/', views.collect_stats, name='logstats'),
    path('<int:pk>/', views.LogDetailView.as_view(), name='logdetail'),
    path('data/<int:pk>/', views.LogDataDetailView.as_view(), name='logdatadetail'),
    path('<int:log_pk>/download', views.xlsx_downloader, name='download'),
]
