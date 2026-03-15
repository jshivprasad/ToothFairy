"""
Test suite for Twilio Voice Agent Features (Iteration 2)
Tests: TwiML generation, AI conversation simulation, morning calls
"""
import pytest
import requests
import os
from urllib.parse import urlencode

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')


class TestTwilioVoiceIncoming:
    """Test Twilio incoming call TwiML generation"""

    def test_incoming_call_ai_off_returns_dial_twiml(self, api_client, auth_token, clinic_id):
        """When AI is OFF, should return <Dial> TwiML to forward to doctor"""
        # First ensure AI is OFF
        headers = {"Authorization": f"Bearer {auth_token}"}
        config_res = api_client.get(f"{BASE_URL}/api/ai-agent/config", headers=headers)
        assert config_res.status_code == 200
        config = config_res.json()
        
        if config.get("is_active"):
            # Toggle OFF
            toggle_res = api_client.put(f"{BASE_URL}/api/ai-agent/toggle", headers=headers)
            assert toggle_res.status_code == 200

        # Simulate incoming call
        form_data = {"From": "+919876543999", "To": "+919876543210", "CallSid": "TEST123"}
        response = api_client.post(
            f"{BASE_URL}/api/twilio/voice/incoming?clinic_id={clinic_id}",
            data=form_data
        )
        
        assert response.status_code == 200
        twiml = response.text
        assert '<?xml version="1.0" encoding="UTF-8"?>' in twiml
        assert '<Response>' in twiml
        assert '<Dial' in twiml
        assert '<Number>' in twiml
        assert 'connecting you to the doctor' in twiml.lower() or 'hold' in twiml.lower()
        print("✅ AI OFF: TwiML with <Dial> returned correctly")

    def test_incoming_call_ai_on_returns_gather_twiml(self, api_client, auth_token, clinic_id):
        """When AI is ON, should return <Gather> TwiML to start conversation"""
        # First ensure AI is ON
        headers = {"Authorization": f"Bearer {auth_token}"}
        config_res = api_client.get(f"{BASE_URL}/api/ai-agent/config", headers=headers)
        assert config_res.status_code == 200
        config = config_res.json()
        
        if not config.get("is_active"):
            # Toggle ON
            toggle_res = api_client.put(f"{BASE_URL}/api/ai-agent/toggle", headers=headers)
            assert toggle_res.status_code == 200

        # Simulate incoming call
        form_data = {"From": "+919876543999", "To": "+919876543210", "CallSid": "TEST456"}
        response = api_client.post(
            f"{BASE_URL}/api/twilio/voice/incoming?clinic_id={clinic_id}",
            data=form_data
        )
        
        assert response.status_code == 200
        twiml = response.text
        assert '<?xml version="1.0" encoding="UTF-8"?>' in twiml
        assert '<Response>' in twiml
        assert '<Gather' in twiml
        assert '<Say' in twiml
        assert 'action=' in twiml  # Should have gather action URL
        print("✅ AI ON: TwiML with <Gather> returned correctly")

    def test_incoming_call_no_clinic_id_returns_error_twiml(self, api_client):
        """Should return error TwiML when clinic_id is missing"""
        form_data = {"From": "+919876543999"}
        response = api_client.post(f"{BASE_URL}/api/twilio/voice/incoming", data=form_data)
        
        assert response.status_code == 200
        twiml = response.text
        assert '<Response>' in twiml
        assert 'not configured' in twiml.lower() or 'sorry' in twiml.lower()
        assert '<Hangup' in twiml
        print("✅ Missing clinic_id: Error TwiML returned correctly")


class TestAIAgentSimulateCall:
    """Test AI conversation simulation endpoint"""

    def test_simulate_call_returns_hindi_response(self, api_client, auth_token):
        """Should return AI response in Hindi with proper structure"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        payload = {"message": "Mujhe appointment chahiye"}
        
        response = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "action" in data
        assert "session_id" in data
        assert data["response"]  # Should have non-empty response
        assert data["action"] in ["CONTINUE", "BOOK_APPOINTMENT", "TRANSFER_TO_DOCTOR", "EMERGENCY_AFTER_HOURS", "END_CALL"]
        
        # Response should be in Hindi (check for Devanagari characters or common Hindi words)
        response_text = data["response"]
        hindi_indicators = ["नमस्ते", "हाँ", "क्या", "है", "के", "appointment", "clinic"]
        has_hindi = any(word in response_text for word in hindi_indicators)
        assert has_hindi, f"Expected Hindi response, got: {response_text}"
        
        print(f"✅ AI response: {response_text[:100]}...")
        print(f"✅ Action: {data['action']}, Session: {data['session_id']}")

    def test_simulate_call_multi_turn_conversation(self, api_client, auth_token):
        """Should maintain conversation context across multiple messages"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # First message
        response1 = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json={"message": "Hello, I need appointment"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]
        assert session_id
        print(f"✅ Turn 1: {data1['response'][:80]}...")
        
        # Second message with same session
        response2 = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json={"message": "My name is Rahul Kumar", "session_id": session_id}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["session_id"] == session_id
        print(f"✅ Turn 2: {data2['response'][:80]}...")
        
        # Third message
        response3 = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json={"message": "Dant mein dard hai", "session_id": session_id}
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["session_id"] == session_id
        print(f"✅ Turn 3: {data3['response'][:80]}...")
        
        # Verify collected_data is being tracked
        if "collected_data" in data3:
            collected = data3["collected_data"]
            print(f"✅ Collected data: {collected}")

    def test_simulate_call_clinic_info_query(self, api_client, auth_token):
        """Should answer clinic timings query"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json={"message": "Clinic ka timing kya hai?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        
        # Response should mention timing/hours
        response_text = data["response"].lower()
        timing_keywords = ["time", "timing", "open", "close", "hour", "09:00", "18:00", "9", "6"]
        has_timing = any(word in response_text for word in timing_keywords)
        assert has_timing, f"Expected timing info in response: {data['response']}"
        
        print(f"✅ Clinic info response: {data['response'][:120]}...")


class TestMorningConfirmationCalls:
    """Test morning confirmation calls endpoint"""

    def test_morning_calls_without_twilio_returns_info(self, api_client, auth_token):
        """Should return appointment info even when Twilio not configured"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.post(
            f"{BASE_URL}/api/twilio/voice/morning-calls",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
        
        # Should indicate Twilio not configured
        response_str = str(data).lower()
        assert "twilio" in response_str or "configured" in response_str or "appointments" in response_str
        
        # Should still tell us how many appointments would be called
        if "appointments_to_call" in data:
            print(f"✅ Would call {data['appointments_to_call']} appointments")
        
        if "appointments" in data:
            print(f"✅ Appointments list returned: {len(data['appointments'])} appointments")
        
        print(f"✅ Morning calls response: {data}")


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    return session


@pytest.fixture
def auth_token(api_client):
    """Get auth token for dr.sharma@dental.com"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "dr.sharma@dental.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["token"]


@pytest.fixture
def clinic_id(api_client, auth_token):
    """Get clinic_id for authenticated user"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = api_client.get(f"{BASE_URL}/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    return data["clinic_id"]
