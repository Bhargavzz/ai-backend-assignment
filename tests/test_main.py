import pytest
from fastapi import status


# ========== USER TESTS ==========

def test_create_user_success(client):
    """Test successful user creation"""
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data


def test_create_user_duplicate_email(client):
    """Test that duplicate email is rejected"""
    # Create first user
    client.post("/users/", json={"username": "user1", "email": "test@example.com"})
    
    # Try to create second user with same email
    response = client.post(
        "/users/",
        json={"username": "user2", "email": "test@example.com"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()["detail"].lower()


def test_create_user_duplicate_username(client):
    """Test that duplicate username is rejected"""
    # Create first user
    client.post("/users/", json={"username": "testuser", "email": "test1@example.com"})
    
    # Try to create second user with same username
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test2@example.com"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.json()["detail"].lower()


def test_create_user_invalid_email(client):
    """Test that invalid email format is rejected"""
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "not-an-email"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_short_username(client):
    """Test that username shorter than 3 chars is rejected"""
    response = client.post(
        "/users/",
        json={"username": "ab", "email": "test@example.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_long_username(client):
    """Test that username longer than 50 chars is rejected"""
    response = client.post(
        "/users/",
        json={"username": "a" * 51, "email": "test@example.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_invalid_username_pattern(client):
    """Test that username with special chars is rejected"""
    response = client.post(
        "/users/",
        json={"username": "test@user!", "email": "test@example.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_missing_fields(client):
    """Test that missing required fields are rejected"""
    response = client.post("/users/", json={"username": "testuser"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ========== DOCUMENT TESTS ==========

def test_create_document_success(client):
    """Test successful document creation"""
    # First create a user
    user_response = client.post(
        "/users/",
        json={"username": "docowner", "email": "owner@example.com"}
    )
    user_id = user_response.json()["id"]
    
    # Create document
    response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "This is test content",
            "user_id": user_id
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["content"] == "This is test content"
    assert "id" in data
    assert "created_at" in data


def test_create_document_without_content(client):
    """Test creating document with no content (should be allowed)"""
    # Create user
    user_response = client.post(
        "/users/",
        json={"username": "user1", "email": "user1@example.com"}
    )
    user_id = user_response.json()["id"]
    
    # Create document without content
    response = client.post(
        "/documents/",
        json={"title": "Empty Document", "user_id": user_id}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["content"] is None


def test_create_document_invalid_user_id(client):
    """Test that document creation fails with non-existent user_id"""
    response = client.post(
        "/documents/",
        json={
            "title": "Test Document",
            "content": "Content",
            "user_id": 99999  # Non-existent user
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "user not found" in response.json()["detail"].lower()


def test_create_document_empty_title(client):
    """Test that empty title is rejected"""
    user_response = client.post(
        "/users/",
        json={"username": "user1", "email": "user1@example.com"}
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
        "/documents/",
        json={"title": "", "user_id": user_id}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_document_long_title(client):
    """Test that title longer than 200 chars is rejected"""
    user_response = client.post(
        "/users/",
        json={"username": "user1", "email": "user1@example.com"}
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
        "/documents/",
        json={"title": "a" * 201, "user_id": user_id}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_document_huge_content(client):
    """Test that content larger than 50KB is rejected"""
    user_response = client.post(
        "/users/",
        json={"username": "user1", "email": "user1@example.com"}
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
        "/documents/",
        json={
            "title": "Huge Doc",
            "content": "a" * 50001,  # Over 50KB limit
            "user_id": user_id
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_document_missing_user_id(client):
    """Test that missing user_id is rejected"""
    response = client.post(
        "/documents/",
        json={"title": "Test Document", "content": "Content"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ========== GET USER DOCUMENTS TESTS ==========

def test_get_user_documents_success(client):
    """Test fetching documents for a user"""
    # Create user
    user_response = client.post(
        "/users/",
        json={"username": "docowner", "email": "owner@example.com"}
    )
    user_id = user_response.json()["id"]
    
    # Create multiple documents
    client.post(
        "/documents/",
        json={"title": "Doc 1", "content": "Content 1", "user_id": user_id}
    )
    client.post(
        "/documents/",
        json={"title": "Doc 2", "content": "Content 2", "user_id": user_id}
    )
    
    # Fetch user documents
    response = client.get(f"/users/{user_id}/documents")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Doc 1"
    assert data[1]["title"] == "Doc 2"


def test_get_user_documents_empty_list(client):
    """Test fetching documents for user with no documents"""
    # Create user
    user_response = client.post(
        "/users/",
        json={"username": "nocdocs", "email": "nodocs@example.com"}
    )
    user_id = user_response.json()["id"]
    
    # Fetch documents (should be empty)
    response = client.get(f"/users/{user_id}/documents")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_user_documents_nonexistent_user(client):
    """Test fetching documents for non-existent user"""
    response = client.get("/users/99999/documents")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "user not found" in response.json()["detail"].lower()


def test_get_user_documents_isolation(client):
    """Test that users only see their own documents"""
    # Create two users
    user1_response = client.post(
        "/users/",
        json={"username": "user1", "email": "user1@example.com"}
    )
    user2_response = client.post(
        "/users/",
        json={"username": "user2", "email": "user2@example.com"}
    )
    user1_id = user1_response.json()["id"]
    user2_id = user2_response.json()["id"]
    
    # Create documents for both users
    client.post(
        "/documents/",
        json={"title": "User1 Doc", "user_id": user1_id}
    )
    client.post(
        "/documents/",
        json={"title": "User2 Doc", "user_id": user2_id}
    )
    
    # User1 should only see their document
    response = client.get(f"/users/{user1_id}/documents")
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "User1 Doc"
    
    # User2 should only see their document
    response = client.get(f"/users/{user2_id}/documents")
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "User2 Doc"


# ========== ROOT ENDPOINT TEST ==========

def test_root_endpoint(client):
    """Test the root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    assert "Document Management API" in response.json()["message"]
