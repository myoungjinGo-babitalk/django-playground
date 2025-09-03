from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']
        read_only_fields = ['created_at']


class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'created_at', 'updated_at', 'comments_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class PostDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'comments']
        read_only_fields = ['created_at', 'updated_at']


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content']
    
    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 최소 2글자 이상이어야 합니다.")
        return value
    
    def validate_content(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("내용은 최소 5글자 이상이어야 합니다.")
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']
    
    def validate_content(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("댓글 내용은 최소 2글자 이상이어야 합니다.")
        return value