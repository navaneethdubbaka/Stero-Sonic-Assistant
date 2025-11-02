# Quick Start Guide

## Prerequisites Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 4. Setup Gmail App Password (for email features)
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification (enable if not enabled)
3. App passwords → Generate new app password for "Mail"
4. Copy the generated password

### 5. Create .env File
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password_here
CONTACTS_FILE_PATH=./data/contacts.txt
STORED_DATA_PATH=./data/stored_data.txt
SCREENSHOT_PATH=./screenshots/screenshot.png
CAMERA_IMAGE_PATH=./screenshots/camera_image.png
```

### 6. Create Required Directories
```bash
mkdir data screenshots assets
```

### 7. Create Contacts File (Optional)
Create `data/contacts.txt`:
```
john,+1234567890
jane,+0987654321
```

## Running the Application

### Option 1: Development Mode (Backend + Frontend Separately)

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Standalone App

1. Build the frontend first:
```bash
cd frontend
npm run build
cd ..
```

2. Run the app:
```bash
python app.py
```

Or use the batch file (Windows):
```bash
run_app.bat
```

### Option 3: Quick Start Script
```bash
python start.py
```

## Testing Voice Commands

1. Click the microphone button or say "Sonic" to activate
2. Try these commands:
   - "What time is it"
   - "Search Wikipedia Python"
   - "Play music"
   - "Take selfie"
   - "Open Notepad"
   - "Activate chatbot" (then ask general questions)

## Troubleshooting

### Speech Recognition Not Working
- Use Chrome/Edge browser
- Grant microphone permissions
- Check browser console for errors

### Import Errors
- Ensure you're in the correct directory
- Run: `pip install -r requirements.txt`
- Verify Python 3.8+

### API Errors
- Check `.env` file exists and has correct values
- Verify Gemini API key is valid
- Check backend is running on port 8000

### Frontend Not Loading
- Build frontend: `cd frontend && npm run build`
- Check that `frontend/build/index.html` exists
- Verify backend is running

## Next Steps

- Customize voice commands in `backend/core/intent_parser.py`
- Add new features in `backend/services/`
- Customize UI in `frontend/src/components/`
- Configure paths in `.env` file

