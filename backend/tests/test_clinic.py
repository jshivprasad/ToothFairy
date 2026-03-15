import pytest

class TestClinic:
    """Test clinic endpoints"""

    def test_get_clinic_info(self, base_url, authenticated_client):
        """Test get clinic information"""
        response = authenticated_client.get(f"{base_url}/api/clinic")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "name" in data
        assert "address" in data
        assert "city" in data
        assert "state" in data
        assert "phone" in data
        assert "email" in data
        assert "fees_min" in data
        assert "fees_max" in data
        
        print(f"✅ Get clinic info test passed - Clinic: {data['name']}")

    def test_update_clinic_and_verify(self, base_url, authenticated_client):
        """Test update clinic information and verify changes"""
        # Get current clinic info
        get_response = authenticated_client.get(f"{base_url}/api/clinic")
        assert get_response.status_code == 200
        current = get_response.json()
        
        # Update clinic
        update_payload = {
            "name": current["name"],
            "address": "TEST_Updated Address 123",
            "city": current.get("city", "Mumbai"),
            "state": current.get("state", "Maharashtra"),
            "pincode": current.get("pincode", "400001"),
            "phone": current.get("phone", "+919876543210"),
            "email": current.get("email", "test@clinic.com"),
            "description": "TEST_Updated description",
            "fees_min": 600,
            "fees_max": 6000,
            "specializations": ["General Dentistry", "Orthodontics"]
        }
        
        update_response = authenticated_client.put(
            f"{base_url}/api/clinic",
            json=update_payload
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        assert updated["address"] == "TEST_Updated Address 123"
        assert updated["description"] == "TEST_Updated description"
        assert updated["fees_min"] == 600
        
        # Verify changes persisted - GET to verify
        verify_response = authenticated_client.get(f"{base_url}/api/clinic")
        assert verify_response.status_code == 200
        verified = verify_response.json()
        assert verified["address"] == "TEST_Updated Address 123"
        assert verified["fees_min"] == 600
        
        print("✅ Update and verify clinic info test passed")
