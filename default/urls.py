from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/comments/', views.post_comments, name='post-comments'),
    path('comments/<int:comment_id>/', views.comment_detail, name='comment-detail'),
]