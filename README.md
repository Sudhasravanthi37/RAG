# Production RAG System — Angular Frontend + FastAPI Backend

## Structure
```
final_project/
├── backend/          ← FastAPI + FAISS + Groq
└── frontend_angular/ ← Angular 17 (identical UI to original HTML)
```

## Backend Setup
```powershell
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env from example
copy .env.example .env
# Edit .env — set GROQ_API_KEY

# Build static knowledge DBs (medical + resume)
python -m app.static_dbs.static_db_builder

# Start server
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup
```powershell
cd frontend_angular
npm install
npm start
# Opens at http://localhost:4200
```

## .env (backend)
```
GROQ_API_KEY=gsk_your_key_here
DATABASE_URL=sqlite:///./rag_system.db
JWT_SECRET_KEY=supersecretkey123456789abcdefgh
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
FRONTEND_VERIFY_URL=http://localhost:4200
VECTOR_DB_PATH=data/vector_dbs
STATIC_VECTOR_DB_PATH=data/static/vector_dbs
UPLOAD_BASE=data/uploads
PROFILE_PICS_PATH=data/profile_pics
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## API Mapping (Angular → Backend)
| Feature              | Angular Service         | Backend Endpoint                   |
|----------------------|-------------------------|------------------------------------|
| Login                | AuthService.login()     | POST /auth/login                   |
| Signup               | AuthService.signup()    | POST /auth/signup                  |
| Verify OTP           | AuthService.verifyOtp() | POST /auth/verify-otp              |
| Resend OTP           | AuthService.resendOtp() | POST /auth/confirm-email           |
| Forgot password      | AuthService.sendResetOtp() | POST /auth/reset-password       |
| Reset password       | AuthService.resetPasswordConfirm() | POST /auth/reset-password/confirm |
| Get profile          | AuthService.fetchProfile() | GET /auth/profile               |
| Logout               | AuthService.logout()    | POST /auth/logout                  |
| Change username      | AuthService.changeUsername() | PATCH /profile/username        |
| Change password      | AuthService.changePassword() | PATCH /profile/password        |
| Upload profile pic   | AuthService.uploadProfilePic() | POST /profile/picture        |
| List chats           | ChatService.loadChats() | GET /chats                         |
| Create chat          | ChatService.createChat() | POST /chat/new                    |
| Load messages        | ChatService.loadMessages() | GET /chats/:id/messages          |
| Delete chat          | ChatService.deleteChat() | DELETE /chats/:id                 |
| Send message         | ChatService.sendMessage() | POST /chat                        |
| Upload document      | ChatService.uploadFile() | POST /upload                      |

## Modes
| Mode           | Key              |
|----------------|------------------|
| Q&A            | qa               |
| Translator     | translator       |
| Resume Analyzer| resume           |
| Question Paper | question_paper   |
| Legal Simplifier| legal           |
| Medical Report | medical          |
