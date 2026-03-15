import pytest
import requests

class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self, base_url, api_client):
        """Test API health check"""
        response = api_client.get(f"{base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        print("✅ Health check passed")

class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self, base_url, api_client, seed_database):
        """Test successful login with seed credentials"""
        response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": "dr.sharma@dental.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "dr.sharma@dental.com"
        assert data["user"]["name"] == "Dr. Rajesh Sharma"
        print("✅ Login success test passed")

    def test_login_invalid_credentials(self, base_url, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": "dr.sharma@dental.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✅ Login invalid credentials test passed")

    def test_get_current_user(self, base_url, authenticated_client):
        """Test get current user endpoint"""
        response = authenticated_client.get(f"{base_url}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "clinic_id" in data
        print("✅ Get current user test passed")

    def test_register_new_user(self, base_url, api_client):
        """Test user registration"""
        import uuid
        unique_email = f"TEST_doctor_{uuid.uuid4().hex[:8]}@test.com"
        
        response = api_client.post(
            f"{base_url}/api/auth/register",
            json={
                "name": "Test Doctor",
                "email": unique_email,
                "password": "testpass123",
                "phone": "+919999999999",
                "role": "doctor"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
        
        # Verify user can login
        login_response = api_client.post(
            f"{base_url}/api/auth/login",
            json={"email": unique_email, "password": "testpass123"}
        )
        assert login_response.status_code == 200
        print("✅ Register new user test passed")
