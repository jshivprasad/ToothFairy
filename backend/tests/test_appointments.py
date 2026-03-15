import pytest
from datetime import datetime, timedelta

class TestAppointments:
    """Test appointment CRUD operations"""

    def test_get_appointments(self, base_url, authenticated_client):
        """Test get all appointments"""
        response = authenticated_client.get(f"{base_url}/api/appointments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get appointments test passed - Found {len(data)} appointments")

    def test_get_appointments_with_status_filter(self, base_url, authenticated_client):
        """Test get appointments with status filter"""
        response = authenticated_client.get(f"{base_url}/api/appointments?status=scheduled")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned appointments have scheduled status
        for appt in data:
            assert appt["status"] == "scheduled"
        print(f"✅ Get appointments with filter test passed - Found {len(data)} scheduled appointments")

    def test_create_appointment_and_verify(self, base_url, authenticated_client):
        """Test create appointment and verify persistence"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        create_payload = {
            "patient_name": "TEST_John Doe",
            "patient_phone": "+919876543299",
            "patient_email": "test@example.com",
            "problem_description": "Dental checkup",
            "preferred_date": tomorrow,
            "preferred_time": "14:00",
            "notes": "Test appointment"
        }
        
        # Create appointment
        create_response = authenticated_client.post(
            f"{base_url}/api/appointments",
            json=create_payload
        )
        assert create_response.status_code == 200
        created = create_response.json()
        
        assert created["patient_name"] == create_payload["patient_name"]
        assert created["patient_phone"] == create_payload["patient_phone"]
        assert created["preferred_date"] == create_payload["preferred_date"]
        assert created["status"] == "scheduled"
        assert "id" in created
        
        appointment_id = created["id"]
        
        # Verify appointment was actually persisted - GET to verify
        get_response = authenticated_client.get(f"{base_url}/api/appointments/{appointment_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == appointment_id
        assert retrieved["patient_name"] == create_payload["patient_name"]
        
        print(f"✅ Create and verify appointment test passed - ID: {appointment_id}")
        return appointment_id

    def test_update_appointment_and_verify(self, base_url, authenticated_client):
        """Test update appointment and verify changes"""
        # First create an appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        create_response = authenticated_client.post(
            f"{base_url}/api/appointments",
            json={
                "patient_name": "TEST_Update Test",
                "patient_phone": "+919876543298",
                "patient_email": "",
                "problem_description": "Initial problem",
                "preferred_date": tomorrow,
                "preferred_time": "10:00",
                "notes": ""
            }
        )
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Update appointment
        update_payload = {
            "status": "confirmed",
            "notes": "Updated notes"
        }
        update_response = authenticated_client.put(
            f"{base_url}/api/appointments/{appointment_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["status"] == "confirmed"
        assert updated["notes"] == "Updated notes"
        
        # Verify changes persisted - GET to verify
        get_response = authenticated_client.get(f"{base_url}/api/appointments/{appointment_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["status"] == "confirmed"
        assert retrieved["notes"] == "Updated notes"
        
        print(f"✅ Update and verify appointment test passed - ID: {appointment_id}")

    def test_delete_appointment_and_verify(self, base_url, authenticated_client):
        """Test delete appointment and verify removal"""
        # First create an appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        create_response = authenticated_client.post(
            f"{base_url}/api/appointments",
            json={
                "patient_name": "TEST_Delete Test",
                "patient_phone": "+919876543297",
                "patient_email": "",
                "problem_description": "To be deleted",
                "preferred_date": tomorrow,
                "preferred_time": "11:00",
                "notes": ""
            }
        )
        assert create_response.status_code == 200
        appointment_id = create_response.json()["id"]
        
        # Delete appointment
        delete_response = authenticated_client.delete(f"{base_url}/api/appointments/{appointment_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion - GET should return 404
        get_response = authenticated_client.get(f"{base_url}/api/appointments/{appointment_id}")
        assert get_response.status_code == 404
        
        print(f"✅ Delete and verify appointment test passed - ID: {appointment_id}")
