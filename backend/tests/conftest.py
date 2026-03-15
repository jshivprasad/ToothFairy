import pytest
import requests
import os

# Use the public backend URL for testing
BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')

if not BASE_URL:
    raise ValueError("EXPO_PUBLIC_BACKEND_URL environment variable not set")

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API"""
    return BASE_URL

@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="session")
def seed_database(base_url, api_client):
    """Seed the database with test data"""
    response = api_client.post(f"{base_url}/api/seed")
    assert response.status_code == 200, "Failed to seed database"
    return response.json()

@pytest.fixture(scope="session")
def auth_token(base_url, api_client, seed_database):
    """Get auth token for Dr. Sharma"""
    response = api_client.post(
        f"{base_url}/api/auth/login",
        json={"email": "dr.sharma@dental.com", "password": "password123"}
    )
    assert response.status_code == 200, "Failed to login"
    data = response.json()
    return data["token"]

@pytest.fixture(scope="function")
def authenticated_client(api_client, auth_token):
    """Client with authentication header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session
