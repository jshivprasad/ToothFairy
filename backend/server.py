from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, Request, Form
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
import json
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'dental_saas')]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'dental-saas-jwt-secret-key-2024-secure')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create the main app
app = FastAPI(title="DentalAI SaaS API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== PYDANTIC MODELS ==============

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: str = "doctor"

class UserLogin(BaseModel):
    email: str
    password: str

class ClinicInfo(BaseModel):
    name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    phone: str = ""
    email: str = ""
    description: str = ""
    fees_min: int = 0
    fees_max: int = 0
    specializations: List[str] = []

class ClinicHoursDay(BaseModel):
    day: str
    is_open: bool = True
    open_time: str = "09:00"
    close_time: str = "18:00"
    break_start: str = "13:00"
    break_end: str = "14:00"

class ClinicHoursUpdate(BaseModel):
    hours: List[ClinicHoursDay]

class AIAgentConfig(BaseModel):
    is_active: bool = False
    greeting_message: str = "Hello! Thank you for calling. How can I help you today?"
    language_preference: str = "hindi"
    forward_to_doctor: bool = True
    collect_patient_info: bool = True
    book_appointments: bool = True
    emergency_handling: bool = True
    doctor_whatsapp: str = ""
    staff_whatsapp: str = ""

class AppointmentCreate(BaseModel):
    patient_name: str
    patient_phone: str
    patient_email: str = ""
    problem_description: str = ""
    preferred_date: str
    preferred_time: str
    notes: str = ""

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None

class PatientCreate(BaseModel):
    name: str
    phone: str
    email: str = ""
    age: int = 0
    gender: str = ""
    address: str = ""
    medical_history: str = ""

# ============== AUTH HELPERS ==============

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    clinic_id = str(uuid.uuid4())

    hashed_password = pwd_context.hash(data.password)

    user_doc = {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "password": hashed_password,
        "phone": data.phone,
        "role": data.role,
        "clinic_id": clinic_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)

    # Create default clinic
    clinic_doc = {
        "id": clinic_id,
        "owner_id": user_id,
        "name": f"Dr. {data.name}'s Dental Clinic",
        "address": "",
        "city": "",
        "state": "",
        "pincode": "",
        "phone": data.phone,
        "email": data.email,
        "description": "",
        "fees_min": 500,
        "fees_max": 5000,
        "specializations": ["General Dentistry"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.clinics.insert_one(clinic_doc)

    # Create default clinic hours
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_docs = []
    for day in days:
        hours_docs.append({
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "day": day,
            "is_open": day != "Sunday",
            "open_time": "09:00",
            "close_time": "18:00",
            "break_start": "13:00",
            "break_end": "14:00"
        })
    await db.clinic_hours.insert_many(hours_docs)

    # Create default AI agent config
    ai_config = {
        "id": str(uuid.uuid4()),
        "clinic_id": clinic_id,
        "is_active": False,
        "greeting_message": "Hello! Thank you for calling. How can I help you today?",
        "language_preference": "hindi",
        "forward_to_doctor": True,
        "collect_patient_info": True,
        "book_appointments": True,
        "emergency_handling": True,
        "doctor_whatsapp": data.phone,
        "staff_whatsapp": "",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ai_agent_config.insert_one(ai_config)

    token = create_access_token({"user_id": user_id, "clinic_id": clinic_id})

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email,
            "phone": data.phone,
            "role": data.role,
            "clinic_id": clinic_id
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user["id"], "clinic_id": user["clinic_id"]})

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
            "clinic_id": user["clinic_id"]
        }
    }

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "clinic_id": user["clinic_id"]
    }

# ============== CLINIC ROUTES ==============

@api_router.get("/clinic")
async def get_clinic(user=Depends(get_current_user)):
    clinic = await db.clinics.find_one({"id": user["clinic_id"]}, {"_id": 0})
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic

@api_router.put("/clinic")
async def update_clinic(data: ClinicInfo, user=Depends(get_current_user)):
    update_data = data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.clinics.update_one(
        {"id": user["clinic_id"]},
        {"$set": update_data}
    )
    clinic = await db.clinics.find_one({"id": user["clinic_id"]}, {"_id": 0})
    return clinic

# ============== CLINIC HOURS ROUTES ==============

@api_router.get("/clinic/hours")
async def get_clinic_hours(user=Depends(get_current_user)):
    hours = await db.clinic_hours.find({"clinic_id": user["clinic_id"]}, {"_id": 0}).to_list(7)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours.sort(key=lambda x: day_order.index(x["day"]) if x["day"] in day_order else 7)
    return hours

@api_router.put("/clinic/hours")
async def update_clinic_hours(data: ClinicHoursUpdate, user=Depends(get_current_user)):
    for day_hours in data.hours:
        await db.clinic_hours.update_one(
            {"clinic_id": user["clinic_id"], "day": day_hours.day},
            {"$set": {
                "is_open": day_hours.is_open,
                "open_time": day_hours.open_time,
                "close_time": day_hours.close_time,
                "break_start": day_hours.break_start,
                "break_end": day_hours.break_end
            }}
        )
    hours = await db.clinic_hours.find({"clinic_id": user["clinic_id"]}, {"_id": 0}).to_list(7)
    return hours

# ============== AI AGENT CONFIG ROUTES ==============

@api_router.get("/ai-agent/config")
async def get_ai_agent_config(user=Depends(get_current_user)):
    config = await db.ai_agent_config.find_one({"clinic_id": user["clinic_id"]}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="AI agent config not found")
    return config

@api_router.put("/ai-agent/config")
async def update_ai_agent_config(data: AIAgentConfig, user=Depends(get_current_user)):
    update_data = data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_agent_config.update_one(
        {"clinic_id": user["clinic_id"]},
        {"$set": update_data}
    )
    config = await db.ai_agent_config.find_one({"clinic_id": user["clinic_id"]}, {"_id": 0})
    return config

@api_router.put("/ai-agent/toggle")
async def toggle_ai_agent(user=Depends(get_current_user)):
    config = await db.ai_agent_config.find_one({"clinic_id": user["clinic_id"]}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="AI agent config not found")

    new_status = not config.get("is_active", False)
    await db.ai_agent_config.update_one(
        {"clinic_id": user["clinic_id"]},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"is_active": new_status}

# ============== APPOINTMENT ROUTES ==============

@api_router.get("/appointments")
async def get_appointments(
    status: Optional[str] = None,
    date: Optional[str] = None,
    user=Depends(get_current_user)
):
    query = {"clinic_id": user["clinic_id"]}
    if status:
        query["status"] = status
    if date:
        query["preferred_date"] = date

    appointments = await db.appointments.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return appointments

@api_router.post("/appointments")
async def create_appointment(data: AppointmentCreate, user=Depends(get_current_user)):
    appointment_id = str(uuid.uuid4())

    # Check if patient exists, create if not
    patient = await db.patients.find_one(
        {"clinic_id": user["clinic_id"], "phone": data.patient_phone},
        {"_id": 0}
    )
    if not patient:
        patient_id = str(uuid.uuid4())
        patient_doc = {
            "id": patient_id,
            "clinic_id": user["clinic_id"],
            "name": data.patient_name,
            "phone": data.patient_phone,
            "email": data.patient_email,
            "age": 0,
            "gender": "",
            "address": "",
            "medical_history": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.patients.insert_one(patient_doc)
    else:
        patient_id = patient["id"]

    appointment_doc = {
        "id": appointment_id,
        "clinic_id": user["clinic_id"],
        "patient_id": patient_id,
        "patient_name": data.patient_name,
        "patient_phone": data.patient_phone,
        "patient_email": data.patient_email,
        "problem_description": data.problem_description,
        "preferred_date": data.preferred_date,
        "preferred_time": data.preferred_time,
        "status": "scheduled",
        "notes": data.notes,
        "source": "app",
        "confirmation_sent": False,
        "reminder_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.appointments.insert_one(appointment_doc)
    del appointment_doc["_id"]
    return appointment_doc

@api_router.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: str, user=Depends(get_current_user)):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]},
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@api_router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, data: AppointmentUpdate, user=Depends(get_current_user)):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = await db.appointments.update_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment = await db.appointments.find_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]},
        {"_id": 0}
    )
    return appointment

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, user=Depends(get_current_user)):
    result = await db.appointments.delete_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted"}

# ============== PATIENT ROUTES ==============

@api_router.get("/patients")
async def get_patients(user=Depends(get_current_user)):
    patients = await db.patients.find({"clinic_id": user["clinic_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return patients

@api_router.post("/patients")
async def create_patient(data: PatientCreate, user=Depends(get_current_user)):
    patient_id = str(uuid.uuid4())
    patient_doc = {
        "id": patient_id,
        "clinic_id": user["clinic_id"],
        "name": data.name,
        "phone": data.phone,
        "email": data.email,
        "age": data.age,
        "gender": data.gender,
        "address": data.address,
        "medical_history": data.medical_history,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.patients.insert_one(patient_doc)
    del patient_doc["_id"]
    return patient_doc

@api_router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, user=Depends(get_current_user)):
    patient = await db.patients.find_one(
        {"id": patient_id, "clinic_id": user["clinic_id"]},
        {"_id": 0}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# ============== DASHBOARD ROUTES ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    clinic_id = user["clinic_id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    total_appointments = await db.appointments.count_documents({"clinic_id": clinic_id})
    today_appointments = await db.appointments.count_documents({"clinic_id": clinic_id, "preferred_date": today})
    total_patients = await db.patients.count_documents({"clinic_id": clinic_id})
    pending_appointments = await db.appointments.count_documents({"clinic_id": clinic_id, "status": "scheduled"})
    confirmed_appointments = await db.appointments.count_documents({"clinic_id": clinic_id, "status": "confirmed"})
    completed_appointments = await db.appointments.count_documents({"clinic_id": clinic_id, "status": "completed"})

    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    ai_active = ai_config.get("is_active", False) if ai_config else False

    # Get today's appointments
    todays_list = await db.appointments.find(
        {"clinic_id": clinic_id, "preferred_date": today},
        {"_id": 0}
    ).sort("preferred_time", 1).to_list(20)

    return {
        "total_appointments": total_appointments,
        "today_appointments": today_appointments,
        "total_patients": total_patients,
        "pending_appointments": pending_appointments,
        "confirmed_appointments": confirmed_appointments,
        "completed_appointments": completed_appointments,
        "ai_agent_active": ai_active,
        "todays_appointments": todays_list
    }

# ============== AI VOICE AGENT CONVERSATION ==============

@api_router.post("/ai-agent/chat")
async def ai_agent_chat(request_data: dict, user=Depends(get_current_user)):
    """Simulate AI agent conversation for testing"""
    clinic_id = user["clinic_id"]
    message = request_data.get("message", "")
    session_id = request_data.get("session_id", str(uuid.uuid4()))

    clinic = await db.clinics.find_one({"clinic_id": clinic_id}, {"_id": 0})
    if not clinic:
        clinic = await db.clinics.find_one({"id": clinic_id}, {"_id": 0})
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    hours = await db.clinic_hours.find({"clinic_id": clinic_id}, {"_id": 0}).to_list(7)

    clinic_name = clinic.get("name", "Dental Clinic") if clinic else "Dental Clinic"
    clinic_address = clinic.get("address", "Not specified") if clinic else "Not specified"
    fees_min = clinic.get("fees_min", 500) if clinic else 500
    fees_max = clinic.get("fees_max", 5000) if clinic else 5000

    hours_text = ""
    for h in hours:
        if h.get("is_open"):
            hours_text += f"{h['day']}: {h.get('open_time', '09:00')} - {h.get('close_time', '18:00')}\n"
        else:
            hours_text += f"{h['day']}: Closed\n"

    system_prompt = f"""You are an AI receptionist for {clinic_name}, a dental clinic in India.
You speak English, Hindi, and Marathi. Default to Hindi as it's the mediatory language for Indian people.

Clinic Information:
- Name: {clinic_name}
- Address: {clinic_address}
- Fees Range: ₹{fees_min} - ₹{fees_max}
- Clinic Hours:
{hours_text}

Your tasks:
1. Greet patients warmly and ask their preferred language
2. Answer questions about clinic timings, address, and fees
3. Collect patient details: name, problem, mobile number, preferred time
4. Book appointments
5. Handle emergencies - if clinic is open, connect to doctor; if closed, take details and send to doctor
6. Be professional, empathetic, and helpful

Always respond in the patient's preferred language. If unsure, use Hindi."""

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        emergent_key = os.environ.get('EMERGENT_LLM_KEY', '')
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")

        user_message = UserMessage(text=message)
        response = await chat.send_message(user_message)

        # Save chat history
        chat_doc = {
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "session_id": session_id,
            "role": "user",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_history.insert_one(chat_doc)

        ai_doc = {
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "session_id": session_id,
            "role": "assistant",
            "message": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_history.insert_one(ai_doc)

        return {"response": response, "session_id": session_id}
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return {"response": "I'm sorry, I'm having trouble right now. Please try again.", "session_id": session_id}

# ============================================================================
# TWILIO VOICE CALL FLOW — COMPLETE IMPLEMENTATION
# ============================================================================
#
# HOW IT WORKS (end-to-end):
#
# 1. Clinic registers → gets a Twilio phone number assigned
# 2. Twilio number webhook URL is set to: {APP_DOMAIN}/api/twilio/voice/incoming?clinic_id=xxx
# 3. Patient calls the clinic number
# 4. Twilio hits our webhook → we return TwiML (XML instructions for the call)
# 5. TwiML flow:
#    a. Check if AI agent is ON for this clinic
#       - OFF → <Dial> forward call directly to doctor's phone number
#       - ON  → <Gather> start AI conversation
#    b. AI conversation uses <Say> (text-to-speech) + <Gather> (wait for patient speech/input)
#    c. Each patient response → sent to our /api/twilio/voice/gather endpoint
#    d. We pass patient's speech to GPT-5.2 which decides what to do:
#       - Answer query (timings, fees, address) → <Say> response back
#       - Collect details (name, phone, problem) → <Say> ask next question
#       - Book appointment → save to DB, send WhatsApp to doctor
#       - Emergency + clinic open → <Dial> transfer to doctor
#       - Emergency + clinic closed → take info, WhatsApp doctor
#    e. Conversation loops until complete or patient hangs up
#
# 6. Morning confirmation calls:
#    - Cron job triggers /api/twilio/voice/morning-calls
#    - For each today's appointment → Twilio makes outbound call to patient
#    - Patient presses 1 to confirm, 2 to cancel → updates appointment status
#
# NOTE: Without real TWILIO_ACCOUNT_SID/AUTH_TOKEN in .env, Twilio calls won't work.
#       But the FULL LOGIC is here and ready. You can test via the simulation chat.
# ============================================================================

def generate_twiml_say(text: str, language: str = "en-IN") -> str:
    """Generate TwiML <Say> element with appropriate voice"""
    voice_map = {
        "en-IN": "Google.en-IN-Neural2-A",
        "hi-IN": "Google.hi-IN-Neural2-A",
        "mr-IN": "Google.mr-IN-Standard-A",
    }
    voice = voice_map.get(language, "Google.en-IN-Neural2-A")
    return f'<Say voice="{voice}" language="{language}">{text}</Say>'


def is_clinic_open_now(hours_list: list) -> bool:
    """Check if clinic is currently open based on its hours"""
    now = datetime.now(timezone.utc)
    # Get IST time (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = now + ist_offset
    day_name = ist_now.strftime("%A")
    current_time = ist_now.strftime("%H:%M")

    for h in hours_list:
        if h.get("day") == day_name:
            if not h.get("is_open", False):
                return False
            open_time = h.get("open_time", "09:00")
            close_time = h.get("close_time", "18:00")
            return open_time <= current_time <= close_time
    return False


@api_router.post("/twilio/voice/incoming")
async def twilio_voice_incoming(request: Request, clinic_id: str = None):
    """
    MAIN ENTRY POINT: Twilio calls this when a patient dials the clinic number.

    Flow:
    1. Look up the clinic by clinic_id (passed as query param in Twilio webhook URL)
    2. Check if AI agent is ON
       - OFF → Forward call to doctor's phone
       - ON  → Greet patient and start AI conversation with <Gather>
    """
    # Extract form data (Twilio sends POST with form data)
    form = {}
    try:
        form = dict(await request.form())
    except:
        pass

    caller_number = form.get("From", "Unknown")
    logger.info(f"📞 Incoming call from {caller_number} for clinic {clinic_id}")

    if not clinic_id:
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'
        twiml += '<Say>Sorry, this number is not configured. Goodbye.</Say><Hangup/></Response>'
        return Response(content=twiml, media_type="application/xml")

    # Look up clinic and AI config
    clinic = await db.clinics.find_one({"id": clinic_id}, {"_id": 0})
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    hours = await db.clinic_hours.find({"clinic_id": clinic_id}, {"_id": 0}).to_list(7)

    if not clinic:
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'
        twiml += '<Say>Sorry, this clinic is not registered. Goodbye.</Say><Hangup/></Response>'
        return Response(content=twiml, media_type="application/xml")

    ai_active = ai_config.get("is_active", False) if ai_config else False
    clinic_phone = clinic.get("phone", "")

    # Create a call session to track this conversation
    session_id = str(uuid.uuid4())
    await db.call_sessions.insert_one({
        "id": session_id,
        "clinic_id": clinic_id,
        "caller_number": caller_number,
        "status": "in_progress",
        "conversation": [],
        "collected_data": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # DECISION: Is AI agent ON?
    if not ai_active:
        # AI is OFF → Forward call directly to doctor
        logger.info(f"AI agent OFF for clinic {clinic_id}, forwarding to {clinic_phone}")
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'
        twiml += f'<Say voice="Google.en-IN-Neural2-A">Please hold, connecting you to the doctor.</Say>'
        twiml += f'<Dial callerId="{caller_number}" timeout="30">'
        twiml += f'<Number>{clinic_phone}</Number>'
        twiml += '</Dial>'
        twiml += '<Say>The doctor is unavailable. Please try again later. Goodbye.</Say>'
        twiml += '<Hangup/></Response>'
        return Response(content=twiml, media_type="application/xml")

    # AI is ON → Start AI conversation
    clinic_name = clinic.get("name", "Dental Clinic")
    lang_pref = ai_config.get("language_preference", "hindi") if ai_config else "hindi"
    greeting = ai_config.get("greeting_message", "") if ai_config else ""

    if not greeting:
        if lang_pref == "hindi":
            greeting = f"नमस्ते! {clinic_name} में आपका स्वागत है। मैं AI रिसेप्शनिस्ट हूँ। आपकी क्या सहायता कर सकती हूँ? अपॉइंटमेंट बुक करने के लिए 1 दबाएं, क्लिनिक की जानकारी के लिए 2 दबाएं, या अपनी बात बोलें।"
        else:
            greeting = f"Hello! Welcome to {clinic_name}. I am the AI receptionist. How can I help you? Press 1 to book an appointment, press 2 for clinic information, or simply speak your query."

    app_domain = os.environ.get("APP_DOMAIN", "")
    gather_url = f"{app_domain}/api/twilio/voice/gather?clinic_id={clinic_id}&session_id={session_id}"

    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'
    twiml += f'<Gather input="speech dtmf" timeout="5" speechTimeout="auto" action="{gather_url}" method="POST">'
    twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{greeting}</Say>'
    twiml += '</Gather>'
    # If no input, repeat
    twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Koi response nahi mila. Kripya dobara try karein.</Say>'
    twiml += f'<Redirect method="POST">{app_domain}/api/twilio/voice/incoming?clinic_id={clinic_id}</Redirect>'
    twiml += '</Response>'

    logger.info(f"AI agent started conversation for clinic {clinic_id}, session {session_id}")
    return Response(content=twiml, media_type="application/xml")


@api_router.post("/twilio/voice/gather")
async def twilio_voice_gather(request: Request, clinic_id: str = None, session_id: str = None):
    """
    CONVERSATION HANDLER: Called each time patient speaks or presses a key.

    Twilio sends us what the patient said (SpeechResult) or pressed (Digits).
    We pass it to GPT-5.2 to decide the response and next action.
    """
    form = {}
    try:
        form = dict(await request.form())
    except:
        pass

    speech_result = form.get("SpeechResult", "")
    digits = form.get("Digits", "")
    patient_input = speech_result or f"Pressed {digits}" if digits else ""

    logger.info(f"🗣️ Patient said: '{patient_input}' | Session: {session_id}")

    # Load clinic context
    clinic = await db.clinics.find_one({"id": clinic_id}, {"_id": 0})
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    hours = await db.clinic_hours.find({"clinic_id": clinic_id}, {"_id": 0}).to_list(7)
    session = await db.call_sessions.find_one({"id": session_id}, {"_id": 0})

    clinic_name = clinic.get("name", "Dental Clinic") if clinic else "Dental Clinic"
    clinic_address = clinic.get("address", "") if clinic else ""
    fees_min = clinic.get("fees_min", 500) if clinic else 500
    fees_max = clinic.get("fees_max", 5000) if clinic else 5000
    clinic_phone = clinic.get("phone", "") if clinic else ""
    clinic_open = is_clinic_open_now(hours)

    hours_text = ""
    for h in hours:
        if h.get("is_open"):
            hours_text += f"{h['day']}: {h.get('open_time', '09:00')} - {h.get('close_time', '18:00')}\n"
        else:
            hours_text += f"{h['day']}: Closed\n"

    # Build conversation history
    conversation = session.get("conversation", []) if session else []
    collected = session.get("collected_data", {}) if session else {}
    conversation.append({"role": "patient", "text": patient_input})

    # Build the AI system prompt with all context
    system_prompt = f"""You are an AI voice receptionist for {clinic_name}, a dental clinic in India.
You speak Hindi, English, and Marathi. Default to Hindi.

CLINIC INFO:
- Name: {clinic_name}
- Address: {clinic_address}
- Fees: ₹{fees_min} - ₹{fees_max}
- Clinic currently: {"OPEN" if clinic_open else "CLOSED"}
- Hours:
{hours_text}

COLLECTED DATA SO FAR:
{json.dumps(collected, ensure_ascii=False)}

CONVERSATION SO FAR:
{json.dumps(conversation, ensure_ascii=False)}

YOUR INSTRUCTIONS:
1. Respond naturally in Hindi (or patient's preferred language).
2. If patient asks clinic info → tell timings, address, fees.
3. If patient wants appointment → collect: name, phone, problem, preferred date/time.
4. If patient says EMERGENCY and clinic is {"OPEN" if clinic_open else "CLOSED"}:
   {"→ Say you'll transfer to doctor. Add ACTION:TRANSFER_TO_DOCTOR" if clinic_open else "→ Collect name, phone, issue details. Say doctor will call back. Add ACTION:EMERGENCY_AFTER_HOURS"}
5. Once all appointment details collected → Add ACTION:BOOK_APPOINTMENT
6. Keep responses SHORT (2-3 sentences max, this is a phone call).

RESPOND IN THIS JSON FORMAT:
{{
  "response_text": "Your spoken response in Hindi/English",
  "action": "CONTINUE|BOOK_APPOINTMENT|TRANSFER_TO_DOCTOR|EMERGENCY_AFTER_HOURS|END_CALL",
  "collected_data": {{"name": "...", "phone": "...", "problem": "...", "preferred_date": "...", "preferred_time": "..."}}
}}"""

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        emergent_key = os.environ.get('EMERGENT_LLM_KEY', '')

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"voice_{session_id}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")

        user_msg = UserMessage(text=f"Patient said: {patient_input}")
        ai_response_raw = await chat.send_message(user_msg)

        # Parse AI response
        try:
            # Try to extract JSON from the response
            json_start = ai_response_raw.find('{')
            json_end = ai_response_raw.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                ai_data = json.loads(ai_response_raw[json_start:json_end])
            else:
                ai_data = {"response_text": ai_response_raw, "action": "CONTINUE", "collected_data": {}}
        except json.JSONDecodeError:
            ai_data = {"response_text": ai_response_raw, "action": "CONTINUE", "collected_data": {}}

        response_text = ai_data.get("response_text", "Sorry, please repeat.")
        action = ai_data.get("action", "CONTINUE")
        new_collected = ai_data.get("collected_data", {})

        # Merge collected data
        for k, v in new_collected.items():
            if v and v != "...":
                collected[k] = v

        # Save conversation state
        conversation.append({"role": "ai", "text": response_text, "action": action})
        await db.call_sessions.update_one(
            {"id": session_id},
            {"$set": {"conversation": conversation, "collected_data": collected}}
        )

    except Exception as e:
        logger.error(f"AI error in voice gather: {e}")
        response_text = "Maaf kijiye, technical issue hai. Kripya thodi der baad call karein."
        action = "END_CALL"

    app_domain = os.environ.get("APP_DOMAIN", "")
    gather_url = f"{app_domain}/api/twilio/voice/gather?clinic_id={clinic_id}&session_id={session_id}"

    # Generate TwiML based on AI's decision
    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'

    if action == "TRANSFER_TO_DOCTOR":
        # Transfer call to doctor's phone
        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{response_text}</Say>'
        twiml += '<Pause length="1"/>'
        twiml += f'<Dial callerId="{form.get("From", "")}" timeout="30"><Number>{clinic_phone}</Number></Dial>'
        twiml += '<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Doctor se connect nahi ho paya. Kripya baad mein try karein.</Say>'
        twiml += '<Hangup/>'
        await db.call_sessions.update_one({"id": session_id}, {"$set": {"status": "transferred"}})

    elif action == "BOOK_APPOINTMENT":
        # Book the appointment and confirm
        try:
            appt_id = str(uuid.uuid4())
            patient_name = collected.get("name", "Unknown Patient")
            patient_phone = collected.get("phone", form.get("From", ""))
            problem = collected.get("problem", "General Check-up")
            pref_date = collected.get("preferred_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            pref_time = collected.get("preferred_time", "10:00")

            # Create patient if doesn't exist
            existing_patient = await db.patients.find_one({"clinic_id": clinic_id, "phone": patient_phone})
            if not existing_patient:
                await db.patients.insert_one({
                    "id": str(uuid.uuid4()), "clinic_id": clinic_id,
                    "name": patient_name, "phone": patient_phone,
                    "email": "", "age": 0, "gender": "", "address": "", "medical_history": "",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

            # Create appointment
            await db.appointments.insert_one({
                "id": appt_id, "clinic_id": clinic_id,
                "patient_id": "", "patient_name": patient_name,
                "patient_phone": patient_phone, "patient_email": "",
                "problem_description": problem,
                "preferred_date": pref_date, "preferred_time": pref_time,
                "status": "scheduled", "notes": "Booked by AI Agent via phone call",
                "source": "ai_agent", "confirmation_sent": False, "reminder_sent": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # Send WhatsApp to doctor (if configured)
            await send_whatsapp_to_doctor(clinic_id, patient_name, patient_phone, problem, pref_date, pref_time)

            logger.info(f"✅ AI booked appointment {appt_id} for {patient_name}")
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")

        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{response_text}</Say>'
        twiml += '<Hangup/>'
        await db.call_sessions.update_one({"id": session_id}, {"$set": {"status": "appointment_booked"}})

    elif action == "EMERGENCY_AFTER_HOURS":
        # Take emergency info and notify doctor via WhatsApp
        await send_whatsapp_emergency(clinic_id, collected, form.get("From", ""))
        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{response_text}</Say>'
        twiml += '<Hangup/>'
        await db.call_sessions.update_one({"id": session_id}, {"$set": {"status": "emergency_notified"}})

    elif action == "END_CALL":
        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{response_text}</Say>'
        twiml += '<Hangup/>'
        await db.call_sessions.update_one({"id": session_id}, {"$set": {"status": "completed"}})

    else:
        # CONTINUE conversation - ask next question
        twiml += f'<Gather input="speech dtmf" timeout="5" speechTimeout="auto" action="{gather_url}" method="POST">'
        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">{response_text}</Say>'
        twiml += '</Gather>'
        twiml += f'<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Koi jawab nahi mila. Dhanyavaad, goodbye.</Say>'
        twiml += '<Hangup/>'

    twiml += '</Response>'
    return Response(content=twiml, media_type="application/xml")


@api_router.post("/twilio/voice/status")
async def twilio_voice_status(request: Request):
    """Called by Twilio when call status changes (ringing, in-progress, completed, etc.)"""
    form = {}
    try:
        form = dict(await request.form())
    except:
        pass
    call_status = form.get("CallStatus", "unknown")
    call_sid = form.get("CallSid", "")
    logger.info(f"📱 Call status update: {call_status} (SID: {call_sid})")
    return {"status": "received"}


# ============================================================================
# MORNING CONFIRMATION CALLS — Calls patients to confirm today's appointments
# ============================================================================

@api_router.post("/twilio/voice/morning-calls")
async def trigger_morning_calls(user=Depends(get_current_user)):
    """
    Trigger morning confirmation calls for all today's appointments.

    Flow:
    1. Get all appointments for today that are not yet confirmed
    2. For each → Twilio makes outbound call to patient's phone
    3. Patient hears: "You have an appointment at {time}. Press 1 to confirm, 2 to cancel."
    4. Their response updates the appointment status
    """
    clinic_id = user["clinic_id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    appointments = await db.appointments.find({
        "clinic_id": clinic_id,
        "preferred_date": today,
        "status": {"$in": ["scheduled"]},
        "confirmation_sent": False
    }, {"_id": 0}).to_list(50)

    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER", "")

    if not twilio_sid or not twilio_token or not twilio_number:
        return {
            "message": "Morning calls ready but Twilio not configured. Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env",
            "status": "twilio_not_configured",
            "appointments_to_call": len(appointments),
            "appointments": appointments
        }

    # Make calls via Twilio
    from twilio.rest import Client as TwilioClient
    twilio_client = TwilioClient(twilio_sid, twilio_token)
    app_domain = os.environ.get("APP_DOMAIN", "")

    calls_made = []
    for appt in appointments:
        try:
            confirm_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Gather numDigits="1" action="{app_domain}/api/twilio/voice/confirm-response?appointment_id={appt['id']}&clinic_id={clinic_id}" method="POST" timeout="10">
<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">
Namaste {appt['patient_name']}! Aapka aaj {appt['preferred_time']} baje dental appointment hai. Confirm karne ke liye 1 dabayein, cancel karne ke liye 2 dabayein.
</Say>
</Gather>
<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Koi input nahi mila. Appointment abhi bhi scheduled hai.</Say>
</Response>"""

            call = twilio_client.calls.create(
                from_=twilio_number,
                to=appt["patient_phone"],
                twiml=confirm_twiml,
                status_callback=f"{app_domain}/api/twilio/voice/status"
            )

            await db.appointments.update_one(
                {"id": appt["id"]}, {"$set": {"confirmation_sent": True}}
            )
            calls_made.append({"appointment_id": appt["id"], "patient": appt["patient_name"], "call_sid": call.sid})
            logger.info(f"☎️ Morning call made to {appt['patient_name']} ({appt['patient_phone']})")

        except Exception as e:
            logger.error(f"Error calling {appt['patient_name']}: {e}")
            calls_made.append({"appointment_id": appt["id"], "patient": appt["patient_name"], "error": str(e)})

    return {"calls_made": len(calls_made), "details": calls_made}


@api_router.post("/twilio/voice/confirm-response")
async def handle_confirm_response(request: Request, appointment_id: str = None, clinic_id: str = None):
    """
    Handle patient's response to morning confirmation call.
    Press 1 → Confirm appointment
    Press 2 → Cancel appointment
    """
    form = {}
    try:
        form = dict(await request.form())
    except:
        pass

    digits = form.get("Digits", "")
    logger.info(f"📲 Confirmation response: {digits} for appointment {appointment_id}")

    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response>'

    if digits == "1":
        await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": {"status": "confirmed", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        twiml += '<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Dhanyavaad! Aapka appointment confirm ho gaya hai. Hum aapka intezaar karenge.</Say>'
        logger.info(f"✅ Appointment {appointment_id} confirmed by patient")

    elif digits == "2":
        await db.appointments.update_one(
            {"id": appointment_id},
            {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        twiml += '<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Aapka appointment cancel kar diya gaya hai. Dobara book karne ke liye hamein call karein. Dhanyavaad.</Say>'
        logger.info(f"❌ Appointment {appointment_id} cancelled by patient")

    else:
        twiml += '<Say voice="Google.hi-IN-Neural2-A" language="hi-IN">Maaf kijiye, samajh nahi aaya. Aapka appointment abhi bhi scheduled hai.</Say>'

    twiml += '<Hangup/></Response>'
    return Response(content=twiml, media_type="application/xml")


# ============================================================================
# WHATSAPP NOTIFICATIONS — Send to doctor/staff and patients
# ============================================================================

async def send_whatsapp_to_doctor(clinic_id: str, patient_name: str, patient_phone: str, problem: str, date: str, time: str):
    """Send WhatsApp notification to doctor about new AI-booked appointment"""
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    doctor_whatsapp = ai_config.get("doctor_whatsapp", "") if ai_config else ""

    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_wa = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

    if not all([twilio_sid, twilio_token, twilio_wa, doctor_whatsapp]):
        logger.info(f"WhatsApp skipped (not configured): New appointment for {patient_name}")
        # Log to DB for tracking
        await db.notification_log.insert_one({
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "type": "whatsapp_doctor",
            "status": "skipped_not_configured",
            "message": f"New appointment: {patient_name} ({patient_phone}) - {problem} on {date} at {time}",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return

    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(twilio_sid, twilio_token)

        message_body = (
            f"🦷 *New AI Appointment Booked*\n\n"
            f"*Patient:* {patient_name}\n"
            f"*Phone:* {patient_phone}\n"
            f"*Problem:* {problem}\n"
            f"*Date:* {date}\n"
            f"*Time:* {time}\n\n"
            f"_Booked by AI Receptionist_"
        )

        twilio_client.messages.create(
            from_=f"whatsapp:{twilio_wa}",
            to=f"whatsapp:{doctor_whatsapp}",
            body=message_body
        )
        logger.info(f"✅ WhatsApp sent to doctor: {doctor_whatsapp}")

        await db.notification_log.insert_one({
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "type": "whatsapp_doctor",
            "status": "sent",
            "message": message_body,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")


async def send_whatsapp_emergency(clinic_id: str, collected_data: dict, caller_number: str):
    """Send emergency WhatsApp to doctor when clinic is closed"""
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    doctor_whatsapp = ai_config.get("doctor_whatsapp", "") if ai_config else ""

    patient_name = collected_data.get("name", "Unknown")
    problem = collected_data.get("problem", "Emergency - details not provided")

    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_wa = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

    message_body = (
        f"🚨 *EMERGENCY - After Hours*\n\n"
        f"*Patient:* {patient_name}\n"
        f"*Phone:* {caller_number}\n"
        f"*Issue:* {problem}\n\n"
        f"_Patient needs callback. Received by AI Receptionist after clinic hours._"
    )

    if not all([twilio_sid, twilio_token, twilio_wa, doctor_whatsapp]):
        logger.info(f"Emergency WhatsApp skipped (not configured): {message_body}")
        await db.notification_log.insert_one({
            "id": str(uuid.uuid4()), "clinic_id": clinic_id,
            "type": "whatsapp_emergency", "status": "skipped_not_configured",
            "message": message_body, "created_at": datetime.now(timezone.utc).isoformat()
        })
        return

    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(twilio_sid, twilio_token)
        twilio_client.messages.create(
            from_=f"whatsapp:{twilio_wa}", to=f"whatsapp:{doctor_whatsapp}", body=message_body
        )
        logger.info(f"🚨 Emergency WhatsApp sent to doctor: {doctor_whatsapp}")
    except Exception as e:
        logger.error(f"Emergency WhatsApp error: {e}")


@api_router.post("/twilio/whatsapp/incoming")
async def twilio_whatsapp_incoming(request: Request):
    """Handle incoming WhatsApp messages from patients"""
    form = {}
    try:
        form = dict(await request.form())
    except:
        pass

    from_number = form.get("From", "").replace("whatsapp:", "")
    message_body = form.get("Body", "")
    logger.info(f"💬 WhatsApp from {from_number}: {message_body}")

    # Simple auto-responses
    body_lower = message_body.lower()
    if "confirm" in body_lower or "yes" in body_lower or "haan" in body_lower:
        response = "Dhanyavaad! Aapka appointment confirm ho gaya hai. ✅"
    elif "cancel" in body_lower or "nahi" in body_lower:
        response = "Aapka appointment cancel kar diya gaya hai. Dobara book karne ke liye call karein."
    elif "help" in body_lower or "madad" in body_lower:
        response = "Namaste! Aap 'CONFIRM' likh kar appointment confirm kar sakte hain ya 'CANCEL' likh kar cancel kar sakte hain."
    else:
        response = "Dhanyavaad aapke message ke liye. Kripya appointment ke liye clinic number par call karein."

    # Respond via TwiML
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response}</Message></Response>'
    return Response(content=twiml, media_type="application/xml")


@api_router.post("/notifications/whatsapp/appointment")
async def send_whatsapp_appointment(request_data: dict, user=Depends(get_current_user)):
    """Send appointment notification via WhatsApp"""
    appointment_id = request_data.get("appointment_id", "")
    recipient = request_data.get("recipient", "doctor")

    appointment = await db.appointments.find_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]}, {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    if not twilio_sid:
        return {
            "message": "WhatsApp notification ready but Twilio not configured. Add TWILIO_ACCOUNT_SID to .env",
            "status": "twilio_not_configured",
            "appointment": appointment
        }

    await send_whatsapp_to_doctor(
        user["clinic_id"],
        appointment["patient_name"],
        appointment["patient_phone"],
        appointment.get("problem_description", ""),
        appointment["preferred_date"],
        appointment["preferred_time"]
    )
    return {"message": f"WhatsApp notification sent to {recipient}", "status": "sent"}


# ============================================================================
# SIMULATION CHAT — Test AI agent conversation without real Twilio calls
# ============================================================================

@api_router.post("/ai-agent/simulate-call")
async def simulate_call(request_data: dict, user=Depends(get_current_user)):
    """
    Simulate a patient call to test the AI agent conversation.
    This uses the SAME AI logic as real Twilio calls, but via text.

    Send: {"message": "patient's text", "session_id": "optional"}
    Returns: {"response": "AI response", "action": "CONTINUE|BOOK_APPOINTMENT|...", "session_id": "..."}
    """
    clinic_id = user["clinic_id"]
    message = request_data.get("message", "")
    session_id = request_data.get("session_id", str(uuid.uuid4()))

    # Load context
    clinic = await db.clinics.find_one({"id": clinic_id}, {"_id": 0})
    ai_config = await db.ai_agent_config.find_one({"clinic_id": clinic_id}, {"_id": 0})
    hours = await db.clinic_hours.find({"clinic_id": clinic_id}, {"_id": 0}).to_list(7)

    # Get or create session
    session = await db.call_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        session = {
            "id": session_id, "clinic_id": clinic_id,
            "caller_number": "simulation", "status": "in_progress",
            "conversation": [], "collected_data": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.call_sessions.insert_one({**session})

    clinic_name = clinic.get("name", "Dental Clinic") if clinic else "Dental Clinic"
    clinic_address = clinic.get("address", "") if clinic else ""
    fees_min = clinic.get("fees_min", 500) if clinic else 500
    fees_max = clinic.get("fees_max", 5000) if clinic else 5000
    clinic_open = is_clinic_open_now(hours)

    hours_text = ""
    for h in hours:
        if h.get("is_open"):
            hours_text += f"{h['day']}: {h.get('open_time', '09:00')} - {h.get('close_time', '18:00')}\n"
        else:
            hours_text += f"{h['day']}: Closed\n"

    conversation = session.get("conversation", [])
    collected = session.get("collected_data", {})
    conversation.append({"role": "patient", "text": message})

    system_prompt = f"""You are an AI voice receptionist for {clinic_name}, a dental clinic in India.
You speak Hindi, English, and Marathi. Default to Hindi as it's the mediatory language for Indian people.

CLINIC INFO:
- Name: {clinic_name}
- Address: {clinic_address}
- Fees: ₹{fees_min} - ₹{fees_max}
- Clinic currently: {"OPEN" if clinic_open else "CLOSED"}
- Hours:
{hours_text}

COLLECTED DATA SO FAR: {json.dumps(collected, ensure_ascii=False)}
CONVERSATION SO FAR: {json.dumps(conversation[-6:], ensure_ascii=False)}

YOUR INSTRUCTIONS:
1. Talk naturally in Hindi (or patient's preferred language). Be warm and human-like.
2. If patient asks clinic info → tell timings, address, fees.
3. If patient wants appointment → collect: name, phone number, problem/treatment, preferred date and time.
4. If patient has EMERGENCY and clinic is {"OPEN" if clinic_open else "CLOSED"}:
   {"→ Say you'll transfer to doctor. Use ACTION:TRANSFER_TO_DOCTOR" if clinic_open else "→ Collect name, phone, issue. Say doctor will call back. Use ACTION:EMERGENCY_AFTER_HOURS"}
5. Once ALL appointment details (name, phone, problem, date, time) collected → Use ACTION:BOOK_APPOINTMENT
6. Keep responses SHORT (2-3 sentences, like a real phone call).

RESPOND AS JSON:
{{"response_text": "...", "action": "CONTINUE|BOOK_APPOINTMENT|TRANSFER_TO_DOCTOR|EMERGENCY_AFTER_HOURS|END_CALL", "collected_data": {{"name": "", "phone": "", "problem": "", "preferred_date": "", "preferred_time": ""}}}}"""

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        emergent_key = os.environ.get('EMERGENT_LLM_KEY', '')

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"sim_{session_id}",
            system_message=system_prompt
        )
        chat.with_model("openai", "gpt-5.2")

        user_msg = UserMessage(text=f"Patient: {message}")
        ai_response_raw = await chat.send_message(user_msg)

        try:
            json_start = ai_response_raw.find('{')
            json_end = ai_response_raw.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                ai_data = json.loads(ai_response_raw[json_start:json_end])
            else:
                ai_data = {"response_text": ai_response_raw, "action": "CONTINUE", "collected_data": {}}
        except json.JSONDecodeError:
            ai_data = {"response_text": ai_response_raw, "action": "CONTINUE", "collected_data": {}}

        response_text = ai_data.get("response_text", "")
        action = ai_data.get("action", "CONTINUE")
        new_collected = ai_data.get("collected_data", {})

        for k, v in new_collected.items():
            if v and v != "" and v != "...":
                collected[k] = v

        conversation.append({"role": "ai", "text": response_text, "action": action})
        await db.call_sessions.update_one(
            {"id": session_id},
            {"$set": {"conversation": conversation, "collected_data": collected}}
        )

        # If appointment should be booked
        if action == "BOOK_APPOINTMENT":
            appt_id = str(uuid.uuid4())
            await db.appointments.insert_one({
                "id": appt_id, "clinic_id": clinic_id,
                "patient_id": "", "patient_name": collected.get("name", "Patient"),
                "patient_phone": collected.get("phone", ""),
                "patient_email": "", "problem_description": collected.get("problem", ""),
                "preferred_date": collected.get("preferred_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "preferred_time": collected.get("preferred_time", "10:00"),
                "status": "scheduled", "notes": "Booked by AI Agent (simulation)",
                "source": "ai_agent", "confirmation_sent": False, "reminder_sent": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            await send_whatsapp_to_doctor(
                clinic_id, collected.get("name", ""), collected.get("phone", ""),
                collected.get("problem", ""), collected.get("preferred_date", ""), collected.get("preferred_time", "")
            )
            await db.call_sessions.update_one({"id": session_id}, {"$set": {"status": "appointment_booked"}})

        return {
            "response": response_text,
            "action": action,
            "collected_data": collected,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Simulation chat error: {e}")
        return {
            "response": "Maaf kijiye, abhi technical issue hai. Kripya thodi der baad try karein.",
            "action": "CONTINUE",
            "session_id": session_id
        }

# ============== GOOGLE CALENDAR ROUTES (PLACEHOLDER) ==============

@api_router.get("/google/calendar/auth-url")
async def get_google_auth_url(user=Depends(get_current_user)):
    """Get Google Calendar OAuth URL"""
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not google_client_id:
        return {
            "message": "Google Calendar integration placeholder - configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
            "status": "placeholder",
            "auth_url": ""
        }
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "")
    scope = "https://www.googleapis.com/auth/calendar"
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={google_client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"
    return {"auth_url": auth_url, "status": "active"}

@api_router.get("/google/calendar/status")
async def get_google_calendar_status(user=Depends(get_current_user)):
    """Check if Google Calendar is connected"""
    tokens = await db.google_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    return {"connected": tokens is not None}

# ============== SEED DATA ==============

@api_router.post("/seed")
async def seed_data():
    """Seed sample data for testing"""
    # Clear existing data
    await db.users.delete_many({})
    await db.clinics.delete_many({})
    await db.clinic_hours.delete_many({})
    await db.ai_agent_config.delete_many({})
    await db.appointments.delete_many({})
    await db.patients.delete_many({})

    # Create sample clinics
    clinics_data = [
        {
            "user": {"name": "Dr. Rajesh Sharma", "email": "dr.sharma@dental.com", "phone": "+919876543210"},
            "clinic": {"name": "Sharma Dental Care", "address": "45, MG Road, Andheri West", "city": "Mumbai", "state": "Maharashtra", "pincode": "400058", "fees_min": 500, "fees_max": 5000, "specializations": ["General Dentistry", "Orthodontics", "Root Canal"]},
        },
        {
            "user": {"name": "Dr. Priya Patel", "email": "dr.patel@dental.com", "phone": "+919876543211"},
            "clinic": {"name": "Patel Dental Clinic", "address": "12, Linking Road, Bandra", "city": "Mumbai", "state": "Maharashtra", "pincode": "400050", "fees_min": 800, "fees_max": 8000, "specializations": ["Cosmetic Dentistry", "Implants", "Periodontics"]},
        },
        {
            "user": {"name": "Dr. Amit Deshmukh", "email": "dr.deshmukh@dental.com", "phone": "+919876543212"},
            "clinic": {"name": "Deshmukh Dental Hospital", "address": "78, FC Road, Shivajinagar", "city": "Pune", "state": "Maharashtra", "pincode": "411004", "fees_min": 300, "fees_max": 3000, "specializations": ["Pediatric Dentistry", "General Dentistry"]},
        }
    ]

    created_clinics = []
    for clinic_data in clinics_data:
        user_id = str(uuid.uuid4())
        clinic_id = str(uuid.uuid4())

        hashed_password = pwd_context.hash("password123")

        user_doc = {
            "id": user_id,
            "name": clinic_data["user"]["name"],
            "email": clinic_data["user"]["email"],
            "password": hashed_password,
            "phone": clinic_data["user"]["phone"],
            "role": "doctor",
            "clinic_id": clinic_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)

        clinic_doc = {
            "id": clinic_id,
            "owner_id": user_id,
            **clinic_data["clinic"],
            "email": clinic_data["user"]["email"],
            "phone": clinic_data["user"]["phone"],
            "description": f"Leading dental clinic with experienced doctors providing quality dental care.",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.clinics.insert_one(clinic_doc)

        # Clinic hours
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            await db.clinic_hours.insert_one({
                "id": str(uuid.uuid4()),
                "clinic_id": clinic_id,
                "day": day,
                "is_open": day != "Sunday",
                "open_time": "09:00",
                "close_time": "18:00",
                "break_start": "13:00",
                "break_end": "14:00"
            })

        # AI config
        await db.ai_agent_config.insert_one({
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "is_active": True,
            "greeting_message": "Namaste! Thank you for calling. How can I help you today?",
            "language_preference": "hindi",
            "forward_to_doctor": True,
            "collect_patient_info": True,
            "book_appointments": True,
            "emergency_handling": True,
            "doctor_whatsapp": clinic_data["user"]["phone"],
            "staff_whatsapp": "",
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        # Sample patients
        patients_data = [
            {"name": "Aarav Patel", "phone": "+919800000001", "age": 32, "gender": "male"},
            {"name": "Ananya Singh", "phone": "+919800000002", "age": 28, "gender": "female"},
            {"name": "Vikram Reddy", "phone": "+919800000003", "age": 45, "gender": "male"},
            {"name": "Meera Joshi", "phone": "+919800000004", "age": 35, "gender": "female"},
            {"name": "Rahul Kumar", "phone": "+919800000005", "age": 50, "gender": "male"},
        ]

        for p in patients_data:
            patient_id = str(uuid.uuid4())
            await db.patients.insert_one({
                "id": patient_id,
                "clinic_id": clinic_id,
                "name": p["name"],
                "phone": p["phone"],
                "email": "",
                "age": p["age"],
                "gender": p["gender"],
                "address": "",
                "medical_history": "",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            # Sample appointments
            problems = ["Root Canal Treatment", "Teeth Cleaning", "Cavity Filling", "Dental Check-up", "Tooth Extraction"]
            statuses = ["scheduled", "confirmed", "completed", "scheduled", "confirmed"]
            today = datetime.now(timezone.utc)
            for i, (problem, status) in enumerate(zip(problems, statuses)):
                appt_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                await db.appointments.insert_one({
                    "id": str(uuid.uuid4()),
                    "clinic_id": clinic_id,
                    "patient_id": patient_id,
                    "patient_name": p["name"],
                    "patient_phone": p["phone"],
                    "patient_email": "",
                    "problem_description": problem,
                    "preferred_date": appt_date,
                    "preferred_time": f"{9 + i}:00",
                    "status": status,
                    "notes": "",
                    "source": "ai_agent" if i % 2 == 0 else "app",
                    "confirmation_sent": status == "confirmed",
                    "reminder_sent": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

        created_clinics.append({"clinic_id": clinic_id, "name": clinic_data["clinic"]["name"], "email": clinic_data["user"]["email"]})

    return {
        "message": "Seed data created successfully",
        "clinics": created_clinics,
        "credentials": "All users have password: password123"
    }

# ============== HEALTH CHECK ==============

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "DentalAI SaaS API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
