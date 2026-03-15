from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
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

# ============== TWILIO WEBHOOK ROUTES (PLACEHOLDER) ==============

@api_router.post("/twilio/voice/incoming")
async def twilio_voice_incoming(request_data: dict = {}):
    """Placeholder for Twilio incoming voice webhook"""
    logger.info("Twilio voice incoming webhook received")
    return {
        "message": "Voice webhook placeholder - configure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env",
        "status": "placeholder"
    }

@api_router.post("/twilio/voice/status")
async def twilio_voice_status(request_data: dict = {}):
    """Placeholder for Twilio voice status callback"""
    logger.info("Twilio voice status callback received")
    return {"status": "received"}

@api_router.post("/twilio/whatsapp/incoming")
async def twilio_whatsapp_incoming(request_data: dict = {}):
    """Placeholder for Twilio WhatsApp incoming webhook"""
    logger.info("Twilio WhatsApp incoming webhook received")
    return {"status": "received"}

# ============== WHATSAPP NOTIFICATION ROUTES ==============

@api_router.post("/notifications/whatsapp/appointment")
async def send_whatsapp_appointment(request_data: dict, user=Depends(get_current_user)):
    """Send appointment notification via WhatsApp (placeholder)"""
    appointment_id = request_data.get("appointment_id", "")
    recipient = request_data.get("recipient", "doctor")

    appointment = await db.appointments.find_one(
        {"id": appointment_id, "clinic_id": user["clinic_id"]},
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    if not twilio_sid:
        return {
            "message": "WhatsApp notification placeholder - configure Twilio credentials in .env",
            "status": "placeholder",
            "appointment": appointment
        }

    return {
        "message": f"WhatsApp notification sent to {recipient}",
        "status": "sent",
        "appointment": appointment
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
