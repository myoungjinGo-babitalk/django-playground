from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Post, Comment
from .serializers import (
    PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer,
    CommentSerializer, CommentCreateSerializer
)


class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """
        요청 HTTP 메서드에 따라 적절한 시리얼라이저 클래스를 반환합니다.
        
        POST 요청일 경우 생성/갱신용 PostCreateUpdateSerializer를, 그 외(주로 GET)에는 목록 반환용 PostListSerializer를 반환합니다.
        """
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer
    
    def perform_create(self, serializer):
        """
        새 게시물 생성 시 직렬화기(serializer)에 현재 요청 사용자(request.user)를 작성자(author)로 설정하여 저장한다.
        
        Parameters:
            serializer: 저장할 모델 인스턴스를 생성하는 DRF serializer. 호출 시 serializer.save(author=self.request.user)를 실행하여 인스턴스를 DB에 저장한다.
        """
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """
        PostDetailView에서 요청 메서드에 따라 사용할 시리얼라이저 클래스를 반환합니다.
        
        PUT 또는 PATCH 요청인 경우 수정/생성용 PostCreateUpdateSerializer를 반환하고, 그 외(예: GET)는 상세 조회용 PostDetailSerializer를 반환합니다.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    
    def get_permissions(self):
        """
        뷰 요청 메서드에 따라 적절한 DRF 권한 검사 객체 목록을 반환합니다.
        
        PUT, PATCH, DELETE(수정/삭제) 요청에는 인증된 사용자이면서 리소스의 작성자여야 하는 검사(IsAuthenticated, IsAuthorOrReadOnly)를 사용합니다. 그 외의 요청에는 인증되지 않은 사용자도 읽기 접근을 허용하는 IsAuthenticatedOrReadOnly를 사용합니다.
        
        Returns:
            list: 요청에 사용할 권한 인스턴스들의 리스트.
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsAuthorOrReadOnly()]
        return [permissions.IsAuthenticatedOrReadOnly()]


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def post_comments(request, post_id):
    """
    지정된 게시물(post_id)에 대한 댓글 목록을 반환하거나 새 댓글을 생성합니다.
    
    GET 요청: 해당 게시물의 모든 댓글을 직렬화하여 200 응답으로 반환합니다.
    POST 요청: 요청 데이터를 CommentCreateSerializer로 검증한 후 유효하면 author를 request.user, post를 해당 게시물로 설정하여 새 댓글을 생성하고 생성된 댓글을 직렬화해 201 응답으로 반환합니다. 검증 오류는 400 응답으로 반환됩니다.
    
    Parameters:
        post_id (int): 대상 Post의 기본 키(ID). 해당 객체가 존재하지 않으면 404 응답(Http404)이 발생합니다.
    """
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'GET':
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            comment_serializer = CommentSerializer(serializer.instance)
            return Response(comment_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def comment_detail(request, comment_id):
    """
    지정한 댓글(comment_id)에 대해 작성자만 수정(PUT)하거나 삭제(DELETE)할 수 있도록 처리하는 엔드포인트입니다.
    
    - 상세:
      요청 사용자가 댓글의 작성자와 일치하지 않으면 403 응답을 반환합니다.
      PUT 요청: 요청 데이터로 댓글을 검증하여 저장하고, 저장된 댓글을 CommentSerializer로 직렬화해 반환합니다. 유효성 오류 시 400 상태와 함께 오류 내용을 반환합니다.
      DELETE 요청: 댓글을 삭제하고 204 No Content를 반환합니다.
    
    응답 상태:
    - 200: 수정 성공 (수정된 댓글 데이터)
    - 204: 삭제 성공
    - 400: 유효성 검사 실패
    - 403: 요청 사용자가 댓글 작성자가 아님
    - 404: comment_id에 해당하는 댓글을 찾지 못함 (get_object_or_404에 의해 처리)
    """
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author != request.user:
        return Response(
            {'error': '댓글 작성자만 수정/삭제할 수 있습니다.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'PUT':
        serializer = CommentCreateSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            comment_serializer = CommentSerializer(serializer.instance)
            return Response(comment_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        요청이 객체에 대해 허용되는지 판별합니다.
        
        안전한 HTTP 메서드(GET, HEAD, OPTIONS 등)인 경우 항상 허용하고, 그 외의 경우에는 요청 사용자가 객체의 작성자(obj.author)인 경우에만 허용합니다.
        
        Parameters:
            request: Django REST framework Request 객체.
            view: 호출된 뷰 인스턴스(사용되지 않음).
            obj: 권한 검사를 수행할 대상 객체(반드시 `author` 속성을 가져야 함).
        
        Returns:
            bool: 요청을 허용하면 True, 그렇지 않으면 False.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
