from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        """
        게시물의 문자열 표현을 반환합니다.
        
        게시물 인스턴스를 문자열로 표현할 때 제목(title)을 반환합니다.
        
        Returns:
            str: 게시물의 제목
        """
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        """댓글 객체의 사람이 읽을 수 있는 문자열 표현을 반환합니다.
        
        형식: "Comment by <작성자 사용자명> on <게시물 제목>"
        
        Returns:
            str: 댓글을 설명하는 한 줄 문자열.
        """
        return f'Comment by {self.author.username} on {self.post.title}'
