import pytest

class TestClinicHours:
    """Test clinic hours endpoints"""

    def test_get_clinic_hours(self, base_url, authenticated_client):
        """Test get clinic hours"""
        response = authenticated_client.get(f"{base_url}/api/clinic/hours")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7, "Should have 7 days"
        
        # Verify day order and structure
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day_data in enumerate(data):
            assert day_data["day"] == days[i], f"Day order incorrect at index {i}"
            assert "is_open" in day_data
            assert "open_time" in day_data
            assert "close_time" in day_data
            assert "break_start" in day_data
            assert "break_end" in day_data
        
        print("✅ Get clinic hours test passed - 7 days configured")

    def test_update_clinic_hours_and_verify(self, base_url, authenticated_client):
        """Test update clinic hours and verify changes"""
        # Get current hours
        get_response = authenticated_client.get(f"{base_url}/api/clinic/hours")
        assert get_response.status_code == 200
        current_hours = get_response.json()
        
        # Modify Monday's hours
        current_hours[0]["open_time"] = "08:00"
        current_hours[0]["close_time"] = "20:00"
        current_hours[0]["is_open"] = True
        
        # Update hours
        update_response = authenticated_client.put(
            f"{base_url}/api/clinic/hours",
            json={"hours": current_hours}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        # Find Monday in response
        monday = next(d for d in updated if d["day"] == "Monday")
        assert monday["open_time"] == "08:00"
        assert monday["close_time"] == "20:00"
        
        # Verify changes persisted - GET to verify
        verify_response = authenticated_client.get(f"{base_url}/api/clinic/hours")
        assert verify_response.status_code == 200
        verified = verify_response.json()
        monday_verified = next(d for d in verified if d["day"] == "Monday")
        assert monday_verified["open_time"] == "08:00"
        assert monday_verified["close_time"] == "20:00"
        
        print("✅ Update and verify clinic hours test passed")
