import pytest
import json
import uuid
from django.contrib.auth.models import User
from .models import Post, Comment


@pytest.fixture
def client():
    """
    Django 테스트용 HTTP 클라이언트를 생성하여 반환합니다.
    
    테스트에서 HTTP 요청을 시뮬레이션하기 위한 django.test.Client 인스턴스를 반환합니다. 이 클라이언트는 CSRF 검사를 비활성화(enforce_csrf_checks=False)하여 테스트 편의성을 제공합니다.
    
    Returns:
        django.test.Client: CSRF 검사 비활성화된 테스트 클라이언트 인스턴스
    """
    from django.test import Client

    return Client(enforce_csrf_checks=False)


@pytest.fixture
def user():
    """
    테스트용 Django User 인스턴스를 생성하여 반환합니다.
    
    임의의 고유한 사용자명("testuser_<8hex>")과 고정 비밀번호("testpass123")로 데이터베이스에 사용자를 생성합니다. 주로 테스트 픽스처에서 인증/소유권 검증용으로 사용됩니다.
    
    Returns:
        django.contrib.auth.models.User: 생성된 사용자 객체(데이터베이스에 저장됨).
    """
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password="testpass123")


@pytest.fixture
def another_user():
    """
    다른 테스트 사용자를 생성하여 반환합니다.
    
    고유한 사용자명을 UUID 일부로 생성하고 비밀번호 "testpass123"으로 User 인스턴스를 생성합니다.
    테스트에서 인증이 필요한 경우 소유권/권한 분기를 검증하기 위해 사용하세요.
    
    Returns:
        django.contrib.auth.models.User: 생성된 활성 사용자 객체
    """
    username = f"anotheruser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password="testpass123")


@pytest.fixture
def post(user):
    """
    지정된 사용자(user)를 작성자(author)로 하여 테스트용 Post 객체를 생성하고 반환합니다.
    
    Parameters:
        user (django.contrib.auth.models.User): 새 게시물의 작성자 계정.
    
    Returns:
        Post: 데이터베이스에 저장된 생성된 Post 인스턴스(타이틀은 "Test Post", 내용은 "Test content for the post").
    """
    return Post.objects.create(
        title="Test Post", content="Test content for the post", author=user
    )


@pytest.fixture
def comment(post, user):
    """
    지정된 게시글(post)과 사용자(user)를 사용해 고정된 본문("Test comment")의 Comment 객체를 생성하여 반환합니다.
    
    post: 댓글을 달 대상인 Post 모델 인스턴스.
    user: 댓글 작성자(User 모델 인스턴스).
    
    Returns:
        생성된 Comment 모델 인스턴스.
    """
    return Comment.objects.create(post=post, content="Test comment", author=user)


@pytest.mark.django_db
class TestPostAPI:

    def test_get_post_list(self, client):
        """게시글 목록 조회 테스트"""
        response = client.get("/api/posts/")
        assert response.status_code == 200

    def test_get_post_list_with_data(self, client, post):
        """데이터가 있는 게시글 목록 조회 테스트"""
        response = client.get("/api/posts/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) >= 1
        # 해당 포스트가 포함되어 있는지 확인
        post_ids = [p["id"] for p in data]
        assert post.id in post_ids

    def test_get_post_detail(self, client, post):
        """게시글 상세 조회 테스트"""
        response = client.get(f"/api/posts/{post.id}/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["title"] == "Test Post"
        assert data["content"] == "Test content for the post"

    def test_get_nonexistent_post(self, client):
        """존재하지 않는 게시글 조회 테스트"""
        response = client.get("/api/posts/999/")
        assert response.status_code == 404

    def test_create_post_unauthenticated(self, client):
        """인증되지 않은 사용자 게시글 작성 시도"""
        post_data = {"title": "New Post", "content": "New post content"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 403

    def test_create_post_authenticated(self, client, user):
        """인증된 사용자 게시글 작성"""
        client.login(username=user.username, password="testpass123")

        initial_count = Post.objects.count()
        post_data = {"title": "New Post", "content": "New post content"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 201
        assert Post.objects.count() == initial_count + 1

        created_post = Post.objects.filter(title="New Post").first()
        assert created_post is not None
        assert created_post.title == "New Post"
        assert created_post.author == user

    def test_create_post_invalid_data(self, client, user):
        """유효하지 않은 데이터로 게시글 작성"""
        client.login(username=user.username, password="testpass123")

        # 제목이 너무 짧은 경우
        post_data = {"title": "A", "content": "Valid content"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 400

    def test_update_post_by_author(self, client, post, user):
        """작성자가 게시글 수정"""
        client.login(username=user.username, password="testpass123")

        updated_data = {"title": "Updated Post", "content": "Updated content"}
        response = client.put(
            f"/api/posts/{post.id}/",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        post.refresh_from_db()
        assert post.title == "Updated Post"
        assert post.content == "Updated content"

    def test_update_post_by_non_author(self, client, post, another_user):
        """
        작성자가 아닌 사용자가 게시글 수정 요청을 보낼 때 서버가 403 Forbidden을 반환하는지 검증하는 테스트입니다.
        """
        client.login(username=another_user.username, password="testpass123")

        updated_data = {"title": "Updated Post", "content": "Updated content"}
        response = client.put(
            f"/api/posts/{post.id}/",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_post_by_author(self, client, post, user):
        """작성자가 게시글 삭제"""
        client.login(username=user.username, password="testpass123")

        initial_count = Post.objects.count()
        response = client.delete(f"/api/posts/{post.id}/")
        assert response.status_code == 204
        assert Post.objects.count() == initial_count - 1
        # 해당 포스트가 삭제되었는지 확인
        assert not Post.objects.filter(id=post.id).exists()

    def test_delete_post_by_non_author(self, client, post, another_user):
        """다른 사용자가 게시글 삭제 시도"""
        client.login(username=another_user.username, password="testpass123")

        response = client.delete(f"/api/posts/{post.id}/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestCommentAPI:

    def test_get_comments(self, client, user):
        """댓글 목록 조회 테스트"""
        # 테스트용 포스트와 댓글 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        comment = Comment.objects.create(post=post, content="Test comment", author=user)

        response = client.get(f"/api/posts/{post.id}/comments/")
        assert response.status_code == 200
        data = json.loads(response.content)
        # 적어도 하나의 댓글이 있어야 함
        assert len(data) >= 1
        # 우리가 만든 댓글이 포함되어 있는지 확인
        comment_contents = [c["content"] for c in data]
        assert "Test comment" in comment_contents

    def test_get_comments_empty_post(self, client, user):
        """댓글이 없는 게시글의 댓글 조회"""
        # 테스트용 포스트 생성 (댓글 없음)
        post = Post.objects.create(
            title="Empty Post", content="Test content", author=user
        )

        response = client.get(f"/api/posts/{post.id}/comments/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 0

    def test_create_comment_authenticated(self, client, user):
        """
        인증된 사용자가 특정 게시물에 댓글을 생성하고 생성 성공(HTTP 201), 데이터베이스 카운트 증가 및 작성자 연결을 검증합니다.
        
        설명:
        - 같은 사용자로 작성된 테스트용 게시물을 만들고 해당 사용자로 로그인한 뒤 댓글 생성 엔드포인트에 요청을 보냅니다.
        - 응답이 201이며 Comment 테이블의 레코드 수가 1 증가했는지, 생성된 댓글의 내용과 작성자가 기대값과 일치하는지를 확인합니다.
        """
        # 테스트용 포스트 생성 (같은 user로)
        post = Post.objects.create(
            title="Test Post for Comment", content="Test content", author=user
        )

        client.login(username=user.username, password="testpass123")

        initial_count = Comment.objects.count()
        # 고유한 댓글 내용 생성
        unique_content = f"New comment content by {user.username}"
        comment_data = {"content": unique_content}
        response = client.post(
            f"/api/posts/{post.id}/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert Comment.objects.count() == initial_count + 1

        # 방금 생성된 댓글 찾기
        created_comment = Comment.objects.filter(content=unique_content).first()
        assert created_comment is not None
        assert created_comment.content == unique_content
        assert created_comment.author == user

    def test_create_comment_unauthenticated(self, client, user):
        """인증되지 않은 사용자 댓글 작성 시도"""
        # 테스트용 포스트 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )

        comment_data = {"content": "New comment content"}
        response = client.post(
            f"/api/posts/{post.id}/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_comment_invalid_data(self, client, user):
        """유효하지 않은 데이터로 댓글 작성"""
        # 테스트용 포스트 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )

        client.login(username=user.username, password="testpass123")

        # 내용이 너무 짧은 경우
        comment_data = {"content": "A"}
        response = client.post(
            f"/api/posts/{post.id}/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_comment_by_author(self, client, user):
        """댓글 작성자가 댓글 수정"""
        # 테스트용 포스트와 댓글 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        comment = Comment.objects.create(
            post=post, content="Original comment", author=user
        )

        client.login(username=user.username, password="testpass123")

        updated_data = {"content": "Updated comment"}
        response = client.put(
            f"/api/comments/{comment.id}/",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        comment.refresh_from_db()
        assert comment.content == "Updated comment"

    def test_update_comment_by_non_author(self, client, user, another_user):
        """다른 사용자가 댓글 수정 시도"""
        # 테스트용 포스트와 댓글 생성 (user 가 작성)
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        comment = Comment.objects.create(
            post=post, content="Original comment", author=user
        )

        client.login(username=another_user.username, password="testpass123")

        updated_data = {"content": "Updated comment"}
        response = client.put(
            f"/api/comments/{comment.id}/",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_comment_by_author(self, client, user):
        """댓글 작성자가 댓글 삭제"""
        # 테스트용 포스트와 댓글 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        comment = Comment.objects.create(
            post=post, content="Test comment to delete", author=user
        )

        client.login(username=user.username, password="testpass123")

        initial_count = Comment.objects.count()
        response = client.delete(f"/api/comments/{comment.id}/")
        assert response.status_code == 204
        assert Comment.objects.count() == initial_count - 1
        # 해당 댓글이 삭제되었는지 확인
        assert not Comment.objects.filter(id=comment.id).exists()

    def test_delete_comment_by_non_author(self, client, user, another_user):
        """다른 사용자가 댓글 삭제 시도"""
        # 테스트용 포스트와 댓글 생성 (user 가 작성)
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        comment = Comment.objects.create(post=post, content="Test comment", author=user)

        client.login(username=another_user.username, password="testpass123")

        response = client.delete(f"/api/comments/{comment.id}/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestValidation:

    def test_post_title_too_short(self, client, user):
        """게시글 제목이 너무 짧은 경우"""
        client.login(username=user.username, password="testpass123")

        post_data = {"title": "A", "content": "Valid content here"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 400
        if response.content:
            data = json.loads(response.content)
            assert "title" in data

    def test_post_content_too_short(self, client, user):
        """게시글 내용이 너무 짧은 경우"""
        client.login(username=user.username, password="testpass123")

        post_data = {"title": "Valid Title", "content": "A"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 400
        if response.content:
            data = json.loads(response.content)
            assert "content" in data

    def test_comment_content_too_short(self, client, post, user):
        """댓글 내용이 너무 짧은 경우"""
        client.login(username=user.username, password="testpass123")

        comment_data = {"content": "A"}
        response = client.post(
            f"/api/posts/{post.id}/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
        )
        assert response.status_code == 400
        if response.content:
            data = json.loads(response.content)
            assert "content" in data
