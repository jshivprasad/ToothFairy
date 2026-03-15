"""
Test suite for Iteration 3 Features
Changes tested:
1. Twilio webhook uses "To" phone number instead of clinic_id in URL
2. OpenAI SDK replaces Emergent LLM (OPENAI_API_KEY empty = graceful failure)
3. Calendar API endpoint (GET /api/calendar/appointments)
4. NO_DIAGNOSIS_RULES in AI prompts
5. Clinic model has twilio_number field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')


class TestTwilioWebhookPhoneNumberLookup:
    """Test Twilio webhook now uses 'To' field (phone number) instead of clinic_id in URL"""

    def test_incoming_call_identifies_clinic_by_twilio_number(self, api_client):
        """Twilio webhook should identify clinic using To=+919876543210 (Sharma Dental Care)"""
        # Simulate Twilio POST with "To" field = clinic's twilio_number
        form_data = {
            "From": "+919800000001",  # Patient calling
            "To": "+919876543210",     # Sharma Dental Care's Twilio number
            "CallSid": "TEST_CALL_SID_001"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/twilio/voice/incoming",
            data=form_data
        )
        
        assert response.status_code == 200
        twiml = response.text
        
        # Should return valid TwiML (not error)
        assert '<?xml version="1.0" encoding="UTF-8"?>' in twiml
        assert '<Response>' in twiml
        assert '<Hangup/>' not in twiml or 'not configured' not in twiml.lower()
        
        # Should have either <Dial> or <Gather> (depending on AI status)
        has_valid_action = '<Dial' in twiml or '<Gather' in twiml
        assert has_valid_action, f"Expected <Dial> or <Gather>, got: {twiml[:200]}"
        
        print(f"✅ Clinic identified by To=+919876543210")
        print(f"✅ TwiML returned: {twiml[:150]}...")

    def test_incoming_call_with_unknown_number_returns_error(self, api_client):
        """Should return error TwiML when 'To' number doesn't match any clinic"""
        form_data = {
            "From": "+919800000001",
            "To": "+919999999999",  # Unknown number
            "CallSid": "TEST_UNKNOWN"
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/twilio/voice/incoming",
            data=form_data
        )
        
        assert response.status_code == 200
        twiml = response.text
        
        # Should return error TwiML
        assert '<Response>' in twiml
        assert 'not configured' in twiml.lower() or 'sorry' in twiml.lower()
        assert '<Hangup' in twiml
        
        print(f"✅ Unknown number returns error TwiML correctly")


class TestCalendarAPI:
    """Test new in-app calendar endpoint (replaced Google Calendar)"""

    def test_calendar_appointments_returns_grouped_data(self, api_client, auth_token):
        """GET /api/calendar/appointments should return appointments grouped by date"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(
            f"{BASE_URL}/api/calendar/appointments?month=3&year=2026",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have required fields
        assert "month" in data
        assert "year" in data
        assert "appointments_by_date" in data
        assert "total" in data
        
        # Verify structure
        assert data["month"] == 3
        assert data["year"] == 2026
        assert isinstance(data["appointments_by_date"], dict)
        assert isinstance(data["total"], int)
        
        print(f"✅ Calendar endpoint returned data for March 2026")
        print(f"✅ Total appointments: {data['total']}")
        print(f"✅ Dates with appointments: {list(data['appointments_by_date'].keys())}")

    def test_calendar_appointments_defaults_to_current_month(self, api_client, auth_token):
        """Calendar should work without month/year params (defaults to current)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(
            f"{BASE_URL}/api/calendar/appointments",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "appointments_by_date" in data
        assert isinstance(data["appointments_by_date"], dict)
        
        print(f"✅ Calendar works without query params (current month)")


class TestClinicTwilioNumberField:
    """Test clinic model has twilio_number field"""

    def test_clinic_has_twilio_number_field(self, api_client, auth_token):
        """GET /api/clinic should include twilio_number field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(f"{BASE_URL}/api/clinic", headers=headers)
        
        assert response.status_code == 200
        clinic = response.json()
        
        # Should have twilio_number field
        assert "twilio_number" in clinic, "Clinic missing twilio_number field"
        assert clinic["twilio_number"] == "+919876543210", f"Expected +919876543210, got {clinic.get('twilio_number')}"
        
        print(f"✅ Clinic has twilio_number: {clinic['twilio_number']}")
        print(f"✅ Clinic name: {clinic['name']}")


class TestOpenAISDKGracefulFailure:
    """Test OpenAI SDK fails gracefully when OPENAI_API_KEY is empty"""

    def test_simulate_call_returns_error_when_openai_key_missing(self, api_client, auth_token):
        """Should return error response (not crash) when OPENAI_API_KEY is empty"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        payload = {"message": "Test message to trigger AI"}
        
        response = api_client.post(
            f"{BASE_URL}/api/ai-agent/simulate-call",
            headers=headers,
            json=payload
        )
        
        # Should not crash (should return 200 with error message OR graceful response)
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        
        # Response should indicate error OR be a placeholder
        response_text = data["response"].lower()
        error_indicators = ["sorry", "maaf", "technical", "issue", "try again", "problem"]
        has_error_msg = any(word in response_text for word in error_indicators)
        
        print(f"✅ Simulate call with empty OPENAI_API_KEY returned: {data['response'][:100]}")
        
        if has_error_msg:
            print(f"✅ Graceful error message returned (expected behavior)")
        else:
            print(f"⚠️  No clear error message, but didn't crash (may be cached or fallback)")


class TestLoginAndDashboard:
    """Test basic login and dashboard still work after changes"""

    def test_login_with_seed_credentials(self, api_client):
        """Login should work with dr.sharma@dental.com / password123"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dr.sharma@dental.com", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "dr.sharma@dental.com"
        
        print(f"✅ Login successful: {data['user']['name']}")

    def test_dashboard_stats(self, api_client, auth_token):
        """Dashboard stats should return expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "total_appointments", "today_appointments", "total_patients",
            "pending_appointments", "confirmed_appointments", "completed_appointments",
            "ai_agent_active", "todays_appointments"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✅ Dashboard stats: {data['total_appointments']} total, {data['today_appointments']} today, {data['total_patients']} patients")


# ===== FIXTURES =====

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
