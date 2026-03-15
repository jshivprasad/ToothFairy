import pytest

class TestAIAgent:
    """Test AI agent configuration endpoints"""

    def test_get_ai_agent_config(self, base_url, authenticated_client):
        """Test get AI agent configuration"""
        response = authenticated_client.get(f"{base_url}/api/ai-agent/config")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "clinic_id" in data
        assert "is_active" in data
        assert "greeting_message" in data
        assert "language_preference" in data
        assert "forward_to_doctor" in data
        assert "collect_patient_info" in data
        assert "book_appointments" in data
        assert "emergency_handling" in data
        
        # Verify data types
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["forward_to_doctor"], bool)
        
        print(f"✅ Get AI agent config test passed - Active: {data['is_active']}")

    def test_toggle_ai_agent(self, base_url, authenticated_client):
        """Test toggle AI agent on/off"""
        # Get current state
        get_response = authenticated_client.get(f"{base_url}/api/ai-agent/config")
        assert get_response.status_code == 200
        initial_state = get_response.json()["is_active"]
        
        # Toggle AI agent
        toggle_response = authenticated_client.put(f"{base_url}/api/ai-agent/toggle")
        assert toggle_response.status_code == 200
        toggled = toggle_response.json()
        
        assert "is_active" in toggled
        assert toggled["is_active"] == (not initial_state), "State should be toggled"
        
        # Verify state changed - GET to verify
        verify_response = authenticated_client.get(f"{base_url}/api/ai-agent/config")
        assert verify_response.status_code == 200
        verified = verify_response.json()
        assert verified["is_active"] == toggled["is_active"]
        
        # Toggle back
        toggle_back_response = authenticated_client.put(f"{base_url}/api/ai-agent/toggle")
        assert toggle_back_response.status_code == 200
        toggled_back = toggle_back_response.json()
        assert toggled_back["is_active"] == initial_state
        
        print(f"✅ Toggle AI agent test passed - Initial: {initial_state}, Toggled: {not initial_state}, Back: {initial_state}")

    def test_update_ai_agent_config_and_verify(self, base_url, authenticated_client):
        """Test update AI agent configuration and verify changes"""
        # Get current config
        get_response = authenticated_client.get(f"{base_url}/api/ai-agent/config")
        assert get_response.status_code == 200
        current = get_response.json()
        
        # Update config
        update_payload = {
            "is_active": current["is_active"],
            "greeting_message": "TEST_Hello! Welcome to our clinic. How may I help you?",
            "language_preference": "english",
            "forward_to_doctor": True,
            "collect_patient_info": True,
            "book_appointments": True,
            "emergency_handling": True,
            "doctor_whatsapp": "+919876543210",
            "staff_whatsapp": "+919876543211"
        }
        
        update_response = authenticated_client.put(
            f"{base_url}/api/ai-agent/config",
            json=update_payload
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        assert updated["greeting_message"] == update_payload["greeting_message"]
        assert updated["language_preference"] == "english"
        
        # Verify changes persisted - GET to verify
        verify_response = authenticated_client.get(f"{base_url}/api/ai-agent/config")
        assert verify_response.status_code == 200
        verified = verify_response.json()
        assert verified["greeting_message"] == update_payload["greeting_message"]
        assert verified["language_preference"] == "english"
        
        print("✅ Update and verify AI agent config test passed")
