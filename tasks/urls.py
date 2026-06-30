from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('board/', views.task_board, name='task_board'),
    path('task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:pk>/status/', views.task_update_status, name='task_update_status'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]
