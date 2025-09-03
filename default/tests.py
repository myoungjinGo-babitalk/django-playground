import pytest
import json
import os
import uuid
from django.contrib.auth.models import User
from .models import Post, Comment

TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "testpass123")

@pytest.fixture
def client():
    from django.test import Client

    return Client(enforce_csrf_checks=False)

@pytest.fixture
def user():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password=TEST_PASSWORD)

@pytest.fixture
def another_user():
    username = f"anotheruser_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password=TEST_PASSWORD)

@pytest.fixture
def post(user):
    return Post.objects.create(
        title="Test Post", content="Test content for the post", author=user
    )

@pytest.fixture
def comment(post, user):
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
        client.login(username=user.username, password=TEST_PASSWORD)

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
        client.login(username=user.username, password=TEST_PASSWORD)

        # 제목이 너무 짧은 경우
        post_data = {"title": "A", "content": "Valid content"}
        response = client.post(
            "/api/posts/", data=json.dumps(post_data), content_type="application/json"
        )
        assert response.status_code == 400

    def test_update_post_by_author(self, client, post, user):
        """작성자가 게시글 수정"""
        client.login(username=user.username, password=TEST_PASSWORD)

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
        """다른 사용자가 게시글 수정 시도"""
        client.login(username=another_user.username, password=TEST_PASSWORD)

        updated_data = {"title": "Updated Post", "content": "Updated content"}
        response = client.put(
            f"/api/posts/{post.id}/",
            data=json.dumps(updated_data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_post_by_author(self, client, post, user):
        """작성자가 게시글 삭제"""
        client.login(username=user.username, password=TEST_PASSWORD)

        initial_count = Post.objects.count()
        response = client.delete(f"/api/posts/{post.id}/")
        assert response.status_code == 204
        assert Post.objects.count() == initial_count - 1
        # 해당 포스트가 삭제되었는지 확인
        assert not Post.objects.filter(id=post.id).exists()

    def test_delete_post_by_non_author(self, client, post, another_user):
        """다른 사용자가 게시글 삭제 시도"""
        client.login(username=another_user.username, password=TEST_PASSWORD)

        response = client.delete(f"/api/posts/{post.id}/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestCommentAPI:

    def test_get_comments(self, client, user):
        """댓글 목록 조회 테스트"""
        # 테스트용 포스트 생성
        post = Post.objects.create(
            title="Test Post", content="Test content", author=user
        )
        Comment.objects.create(post=post, content="Test comment", author=user)

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
        """인증된 사용자 댓글 작성"""
        # 테스트용 포스트 생성 (같은 user로)
        post = Post.objects.create(
            title="Test Post for Comment", content="Test content", author=user
        )

        client.login(username=user.username, password=TEST_PASSWORD)

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

        client.login(username=user.username, password=TEST_PASSWORD)

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

        client.login(username=user.username, password=TEST_PASSWORD)

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

        client.login(username=another_user.username, password=TEST_PASSWORD)

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

        client.login(username=user.username, password=TEST_PASSWORD)

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

        client.login(username=another_user.username, password=TEST_PASSWORD)

        response = client.delete(f"/api/comments/{comment.id}/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestValidation:

    def test_post_title_too_short(self, client, user):
        """게시글 제목이 너무 짧은 경우"""
        client.login(username=user.username, password=TEST_PASSWORD)

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
        client.login(username=user.username, password=TEST_PASSWORD)

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
        client.login(username=user.username, password=TEST_PASSWORD)

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


# ---------------------------------------------------------------------------
# Additional tests appended to strengthen coverage for Posts and Comments APIs.
# Notes:
# - Test stack: pytest + pytest-django + Django Test Client (no new deps).
# - We focus on happy paths, edge cases, and failure conditions around payload
#   validation, permissions, and resource existence.
# - Routes exercised follow existing patterns in this file.
# ---------------------------------------------------------------------------

import pytest

@pytest.mark.django_db
class TestPostAPIExtra:
    def test_get_post_list_empty_when_no_posts(self, client):
        """Empty list is returned when no posts exist."""
        from .models import Post
        Post.objects.all().delete()

        response = client.get("/api/posts/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.parametrize("missing_field", ["title", "content"])
    def test_create_post_missing_required_fields(self, client, user, missing_field):
        """Creating a post without required fields should fail with 400 and field errors."""
        client.login(username=user.username, password=TEST_PASSWORD)
        payload = {"title": "Valid Title", "content": "Valid content"}
        payload.pop(missing_field)

        response = client.post(
            "/api/posts/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        if response.content:
            data = json.loads(response.content)
            assert missing_field in data

    def test_cannot_override_author_on_create(self, client, user, another_user):
        """Author field in request payload must be ignored; server uses authenticated user."""
        from .models import Post

        client.login(username=user.username, password=TEST_PASSWORD)
        payload = {
            "title": "New Post By User",
            "content": "Body",
            "author": another_user.id,  # attempt to spoof author
        }

        response = client.post(
            "/api/posts/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201

        created_post = Post.objects.filter(title="New Post By User").first()
        assert created_post is not None
        assert created_post.author == user

    def test_update_post_unauthenticated_forbidden(self, client, post):
        """Unauthenticated user cannot update a post."""
        updated = {"title": "Updated by anon", "content": "Updated by anon"}
        response = client.put(
            f"/api/posts/{post.id}/",
            data=json.dumps(updated),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_post_unauthenticated_forbidden(self, client, post):
        """Unauthenticated user cannot delete a post."""
        response = client.delete(f"/api/posts/{post.id}/")
        assert response.status_code == 403

    def test_create_post_invalid_json_returns_400(self, client, user):
        """Invalid JSON payload should yield 400 rather than creating a post."""
        client.login(username=user.username, password=TEST_PASSWORD)
        response = client.post(
            "/api/posts/",
            data="{invalid",  # malformed JSON
            content_type="application/json",
        )
        assert response.status_code == 400

@pytest.mark.django_db
class TestCommentAPIExtra:
    def test_create_comment_missing_content_returns_400(self, client, user, post):
        """Creating a comment without content should fail with 400 and 'content' error."""
        client.login(username=user.username, password=TEST_PASSWORD)
        payload = {}

        response = client.post(
            f"/api/posts/{post.id}/comments/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        if response.content:
            data = json.loads(response.content)
            assert "content" in data

    def test_create_comment_on_nonexistent_post_returns_404(self, client, user):
        """Posting a comment to a non-existent post should 404."""
        client.login(username=user.username, password=TEST_PASSWORD)
        response = client.post(
            "/api/posts/999999/comments/",
            data=json.dumps({"content": "Hello"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_comment_unauthenticated_forbidden(self, client, user, post):
        """Unauthenticated user cannot update a comment."""
        from .models import Comment

        c = Comment.objects.create(post=post, content="Original", author=user)

        updated = {"content": "Updated"}
        response = client.put(
            f"/api/comments/{c.id}/",
            data=json.dumps(updated),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_comment_unauthenticated_forbidden(self, client, user, post):
        """Unauthenticated user cannot delete a comment."""
        from .models import Comment

        c = Comment.objects.create(post=post, content="To delete", author=user)

        response = client.delete(f"/api/comments/{c.id}/")
        assert response.status_code == 403

    def test_get_comments_nonexistent_post_returns_404(self, client):
        """Fetching comments for a non-existent post should 404."""
        response = client.get("/api/posts/999999/comments/")
        assert response.status_code == 404

    def test_update_nonexistent_comment_returns_404(self, client, user):
        """Updating a non-existent comment should 404."""
        client.login(username=user.username, password=TEST_PASSWORD)
        response = client.put(
            "/api/comments/999999/",
            data=json.dumps({"content": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_delete_nonexistent_comment_returns_404(self, client, user):
        """Deleting a non-existent comment should 404."""
        client.login(username=user.username, password=TEST_PASSWORD)
        response = client.delete("/api/comments/999999/")
        assert response.status_code == 404