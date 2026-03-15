# DentalAI SaaS - Product Requirements Document

## Overview
DentalAI is a multi-tenant SaaS mobile application with an AI voice agent system for dental clinics in India. The platform enables dental clinics to automate patient call handling with an AI receptionist that speaks English, Hindi, and Marathi, while providing doctors/staff with a mobile app to manage clinic operations.

## Tech Stack
- **Frontend**: React Native (Expo SDK 54) with expo-router
- **Backend**: FastAPI (Python) with MongoDB (Motor async driver)
- **AI Engine**: OpenAI GPT-5.2 via Emergent LLM Key
- **Voice/SMS**: Twilio Voice + WhatsApp API (placeholder credentials)
- **Calendar**: Google Calendar API (placeholder credentials)
- **Auth**: JWT-based custom authentication

## Features Implemented

### 1. Authentication
- JWT-based login/register for doctors/clinic staff
- Secure token storage with AsyncStorage
- Auto-redirect based on auth state

### 2. Dashboard
- AI Agent ON/OFF toggle (prominent, one-tap)
- Stats: Today's appointments, Pending, Confirmed, Total Patients
- Quick actions: New Appointment, Patients, Hours, AI Config
- Today's appointment list with status badges

### 3. Clinic Management
- Edit clinic info (name, address, city, state, pincode, phone, email)
- Fees range (min/max in INR)
- Specializations management
- Clinic hours per day (open/close times, break times)
- Sunday closed by default

### 4. AI Agent Configuration
- ON/OFF toggle reflecting in AI call handling
- Greeting message customization
- Language preference (Hindi/English/Marathi)
- Capability toggles: Forward to doctor, Collect patient info, Book appointments, Emergency handling
- WhatsApp numbers for doctor/staff notifications

### 5. Appointment Management
- Full CRUD for appointments
- Status workflow: scheduled → confirmed → completed/cancelled
- Filter by status
- Source tracking (app vs AI agent)
- Patient auto-creation on appointment booking

### 6. Patient Management
- Patient list with contact info
- Auto-created from appointments
- Age, gender, medical history tracking

### 7. AI Voice Agent (Backend Logic)
- GPT-5.2 powered conversation engine
- Multi-language support (English/Hindi/Marathi)
- Clinic context injection (hours, fees, address)
- Session-based chat history in MongoDB
- Emergency routing logic framework

### 8. Integration Placeholders
- **Twilio Voice**: Incoming/outgoing call webhook endpoints
- **Twilio WhatsApp**: Message sending and receiving endpoints
- **Google Calendar**: OAuth flow and event management endpoints
- **Morning Confirmation Calls**: Workflow endpoint ready

## Database Schema (MongoDB Collections)
- `users` - Doctor/staff accounts with clinic_id
- `clinics` - Clinic profiles with fees, specializations
- `clinic_hours` - Per-day open/close/break times
- `ai_agent_config` - AI toggle, language, capabilities per clinic
- `appointments` - Full appointment records with status tracking
- `patients` - Patient records per clinic
- `chat_history` - AI conversation logs
- `google_tokens` - OAuth tokens for Calendar

## Seed Data
3 clinics pre-loaded:
- Sharma Dental Care (Mumbai) - dr.sharma@dental.com
- Patel Dental Clinic (Mumbai) - dr.patel@dental.com
- Deshmukh Dental Hospital (Pune) - dr.deshmukh@dental.com
All passwords: password123

## Environment Variables
### Backend (.env)
- MONGO_URL, DB_NAME
- JWT_SECRET, JWT_ALGORITHM
- EMERGENT_LLM_KEY
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TWILIO_WHATSAPP_NUMBER
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

### Frontend (.env)
- EXPO_PUBLIC_BACKEND_URL

## API Endpoints
- POST /api/auth/register, /api/auth/login, GET /api/auth/me
- GET/PUT /api/clinic, GET/PUT /api/clinic/hours
- GET/PUT /api/ai-agent/config, PUT /api/ai-agent/toggle
- GET/POST /api/appointments, GET/PUT/DELETE /api/appointments/:id
- GET/POST /api/patients, GET /api/patients/:id
- GET /api/dashboard/stats
- POST /api/ai-agent/chat
- POST /api/seed
- Twilio webhooks, WhatsApp endpoints, Google Calendar endpoints

## MOCKED Integrations
- Twilio Voice/WhatsApp: Returns placeholder status when credentials not configured
- Google Calendar: Returns placeholder status when credentials not configured
- AI Chat: Uses real OpenAI GPT-5.2 via Emergent LLM Key

## Next Steps
- Configure real Twilio credentials for live call handling
- Configure Google Calendar OAuth for appointment sync
- Implement morning confirmation call scheduler (cron job)
- Add push notifications for appointment reminders
- Multi-clinic dashboard for admin/franchise management
