from django.urls import path
from .views import (
    RegisterUserView,
    LoginUserView,
    LogoutUserView,
    CurrentUserView,
    DatasetListCreateView,
    DatasetDetailView,
    DatasetRecordsView,
    DatasetStatisticsView,
    DatasetHistogramView,
    DatasetStatusView
)

urlpatterns = [
    path('auth/register', RegisterUserView.as_view(), name='register'),
    path('auth/login', LoginUserView.as_view(), name='login'),
    path('auth/logout', LogoutUserView.as_view(), name='logout'),
    path('auth/me', CurrentUserView.as_view(), name='current_user'),
    path('datasets', DatasetListCreateView.as_view(), name='datasets'),
    path('datasets/<int:datasetId>', DatasetDetailView.as_view(), name='dataset_detail'),
    path('datasets/<int:datasetId>/records', DatasetRecordsView.as_view(), name='dataset_records'),
    path('datasets/<int:datasetId>/statistics', DatasetStatisticsView.as_view(), name='dataset_statistics'),
    path('datasets/<int:datasetId>/histogram', DatasetHistogramView.as_view(), name='dataset_histogram'),
    path('datasets/<int:datasetId>/status', DatasetStatusView.as_view(), name='dataset_status'),
]