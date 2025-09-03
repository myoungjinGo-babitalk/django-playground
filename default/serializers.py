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
        """
        Post 인스턴스에 연결된 댓글 수를 반환합니다.
        
        Parameters:
        	obj (Post): 댓글 수를 계산할 대상 Post 모델 인스턴스.
        
        Returns:
        	int: 해당 Post에 연결된 댓글의 개수.
        """
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
        """
        제목 문자열의 최소 길이를 검증합니다.
        
        value의 앞뒤 공백을 제거한 길이가 2자 미만이면 ValidationError를 발생시킵니다.
        
        Parameters:
            value (str): 검증할 제목 문자열
        
        Returns:
            str: 검증을 통과한 원본 문자열
        
        Raises:
            serializers.ValidationError: 제목이 최소 2글자 미만일 때 ("제목은 최소 2글자 이상이어야 합니다.")
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 최소 2글자 이상이어야 합니다.")
        return value
    
    def validate_content(self, value):
        """
        게시글 내용의 길이를 검증합니다.
        
        trim()된 입력 문자열의 길이가 5자 미만이면 serializers.ValidationError를 발생시키고, 그렇지 않으면 원본 값을 그대로 반환합니다.
        
        Parameters:
            value (str): 검증할 게시글 내용 문자열
        
        Returns:
            str: 검증을 통과한 원본 문자열
        
        Raises:
            serializers.ValidationError: "내용은 최소 5글자 이상이어야 합니다." — 길이가 5미만인 경우
        """
        if len(value.strip()) < 5:
            raise serializers.ValidationError("내용은 최소 5글자 이상이어야 합니다.")
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']
    
    def validate_content(self, value):
        """
        댓글 생성/수정 시 전달된 `content` 값이 최소 2글자 이상인지 검증합니다.
        
        공백을 양쪽에서 제거한 후 길이가 2 미만이면 serializers.ValidationError를 발생시킵니다 (메시지: "댓글 내용은 최소 2글자 이상이어야 합니다."). 검증을 통과하면 원래의 `value` 문자열을 반환합니다.
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError("댓글 내용은 최소 2글자 이상이어야 합니다.")
        return value