import pytest
import uuid

class TestPatients:
    """Test patient endpoints"""

    def test_get_patients(self, base_url, authenticated_client):
        """Test get all patients"""
        response = authenticated_client.get(f"{base_url}/api/patients")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get patients test passed - Found {len(data)} patients")

    def test_create_patient_and_verify(self, base_url, authenticated_client):
        """Test create patient and verify persistence"""
        unique_phone = f"+9198765432{uuid.uuid4().hex[:2]}"
        
        create_payload = {
            "name": "TEST_Jane Smith",
            "phone": unique_phone,
            "email": "test_patient@example.com",
            "age": 35,
            "gender": "female",
            "address": "TEST_123 Test Street",
            "medical_history": "No major issues"
        }
        
        # Create patient
        create_response = authenticated_client.post(
            f"{base_url}/api/patients",
            json=create_payload
        )
        assert create_response.status_code == 200
        created = create_response.json()
        
        assert created["name"] == create_payload["name"]
        assert created["phone"] == unique_phone
        assert created["age"] == 35
        assert "id" in created
        
        patient_id = created["id"]
        
        # Verify patient was actually persisted - GET to verify
        get_response = authenticated_client.get(f"{base_url}/api/patients/{patient_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == patient_id
        assert retrieved["name"] == create_payload["name"]
        assert retrieved["phone"] == unique_phone
        
        print(f"✅ Create and verify patient test passed - ID: {patient_id}")
