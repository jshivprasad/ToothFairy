import pytest

class TestDashboard:
    """Test dashboard endpoints"""

    def test_get_dashboard_stats(self, base_url, authenticated_client):
        """Test dashboard stats endpoint"""
        response = authenticated_client.get(f"{base_url}/api/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all required fields are present
        assert "total_appointments" in data
        assert "today_appointments" in data
        assert "total_patients" in data
        assert "pending_appointments" in data
        assert "confirmed_appointments" in data
        assert "completed_appointments" in data
        assert "ai_agent_active" in data
        assert "todays_appointments" in data
        
        # Verify data types
        assert isinstance(data["total_appointments"], int)
        assert isinstance(data["today_appointments"], int)
        assert isinstance(data["total_patients"], int)
        assert isinstance(data["ai_agent_active"], bool)
        assert isinstance(data["todays_appointments"], list)
        
        print(f"✅ Dashboard stats test passed - Total appointments: {data['total_appointments']}, Patients: {data['total_patients']}")
