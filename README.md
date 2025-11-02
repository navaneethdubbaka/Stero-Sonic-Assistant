# Stereo Sonic Assistant

A modern AI voice assistant built with FastAPI, React, Langchain + Gemini, and pywebview for a standalone desktop application.

## Features

- 🎤 **Voice Recognition**: Real-time speech recognition using browser Web Speech API
- 🤖 **AI Chatbot**: Powered by Langchain + Google Gemini for natural conversations
- 📧 **Email**: Send emails with attachments
- 📱 **WhatsApp**: Send WhatsApp messages to contacts
- 📸 **Camera & Screenshots**: Capture images and screenshots
- 🔍 **Google Lens**: Upload images for visual search
- 💾 **Data Storage**: Store and retrieve key-value data
- 🌐 **Web Search**: Search Wikipedia, YouTube, Google
- 🎵 **Media Control**: Play music, control system
- 📊 **Data Analysis**: Analyze DataFrames with AI assistance

## Architecture

```
├── backend/              # FastAPI backend
│   ├── api/             # API endpoints
│   ├── core/           # Core functionality (chatbot, intent parser, TTS)
│   ├── services/       # Service modules (email, WhatsApp, camera, etc.)
│   └── main.py         # FastAPI application
├── frontend/           # React frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   └── App.js      # Main app component
│   └── public/
├── app.py              # pywebview standalone app launcher
└── requirements.txt    # Python dependencies
```

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Chrome/Chromium (for Selenium WebDriver)
- Microphone access
- Camera access (optional)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd "Stero Sonic Assistant"
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install spaCy language model

```bash
python -m spacy download en_core_web_sm
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Set up environment variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
CONTACTS_FILE_PATH=./data/contacts.txt
STORED_DATA_PATH=./data/stored_data.txt
SCREENSHOT_PATH=./screenshots/screenshot.png
CAMERA_IMAGE_PATH=./screenshots/camera_image.png
```

**Note**: For Gmail, you'll need to generate an App Password:
1. Go to your Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"

### 6. Create required directories

```bash
mkdir -p data screenshots assets
```

### 7. Create contacts file (optional)

Create `data/contacts.txt` with format:
```
name1,phone_number1
name2,phone_number2
```

## Usage

### Development Mode

#### Option 1: Run backend and frontend separately

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

The frontend will open at `http://localhost:3000` and backend at `http://localhost:8000`

#### Option 2: Run as standalone app

```bash
# Build frontend first
cd frontend
npm run build
cd ..

# Run standalone app
python app.py
```

### Production Mode

1. Build the React frontend:
```bash
cd frontend
npm run build
cd ..
```

2. Run the standalone app:
```bash
python app.py
```

## API Endpoints

### Voice Recognition
- `POST /api/voice/recognize` - Recognize speech from audio
- `POST /api/voice/check-command` - Check if wake word detected

### Commands
- `POST /api/commands/execute` - Execute voice command
- `POST /api/commands/email/send` - Send email
- `POST /api/commands/whatsapp/send` - Send WhatsApp message
- `GET /api/commands/camera/capture` - Capture camera image
- `GET /api/commands/screenshot/capture` - Take screenshot
- And more...

### Chatbot
- `POST /api/chatbot/chat` - Chat with assistant
- `POST /api/chatbot/chat/tts` - Chat with TTS response
- `POST /api/chatbot/reset` - Reset conversation

### System
- `POST /api/system/analyze-dataframe` - Analyze DataFrame with AI

See full API documentation at `http://localhost:8000/docs` when backend is running.

## Voice Commands

Say **"Sonic"** to activate the assistant, then say:

- "Search Wikipedia [topic]" - Search Wikipedia
- "Search YouTube [query]" - Search YouTube
- "Search Google [query]" - Google search
- "Play music" - Play music from music directory
- "What time is it" - Get current time
- "Open [app name]" - Open Windows application
- "Take selfie" - Capture camera image
- "Send email" - Send email (will prompt for details)
- "Send message [name]" - Send WhatsApp message
- "Store data [key] [value]" - Store data
- "Retrieve data [key]" - Retrieve stored data
- "Activate chatbot" - Switch to chatbot mode
- "Analyze data" - Analyze DataFrame with AI
- And many more...

## Project Structure

```
.
├── app.py                  # Standalone app launcher
├── backend/
│   ├── main.py            # FastAPI app
│   ├── api/
│   │   ├── voice.py       # Voice recognition endpoints
│   │   ├── commands.py    # Command execution endpoints
│   │   ├── chatbot.py     # Chatbot endpoints
│   │   └── system.py      # System endpoints
│   ├── core/
│   │   ├── chatbot.py     # Langchain + Gemini chatbot
│   │   ├── intent_parser.py # NLP intent parsing
│   │   └── speech.py      # Text-to-speech
│   └── services/
│       ├── email_service.py
│       ├── whatsapp_service.py
│       ├── camera_service.py
│       ├── screenshot_service.py
│       ├── system_service.py
│       ├── data_service.py
│       └── lens_service.py
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── VoiceInterface.js
│   │   │   ├── CommandHistory.js
│   │   │   ├── ChatInterface.js
│   │   │   └── StatusBar.js
│   │   └── index.js
│   └── public/
└── requirements.txt
```

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **Langchain**: LLM framework for AI interactions
- **Google Gemini**: AI model for chatbot and data analysis
- **SpeechRecognition**: Speech-to-text
- **pyttsx3**: Text-to-speech
- **spaCy**: NLP for intent parsing
- **Selenium**: Web automation for Google Lens
- **OpenCV**: Camera operations
- **PyAutoGUI**: System automation

### Frontend
- **React**: UI framework
- **Web Speech API**: Browser-based speech recognition
- **Axios**: HTTP client (if needed)

### Standalone App
- **pywebview**: Desktop app framework

## Troubleshooting

### Speech Recognition Not Working
- Ensure microphone permissions are granted
- Use Chrome/Edge for best Web Speech API support
- Check browser console for errors

### API Key Errors
- Verify `GEMINI_API_KEY` is set in `.env`
- Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Email Not Sending
- Use Gmail App Password, not regular password
- Enable 2-Step Verification on Google Account
- Check email credentials in `.env`

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python path includes backend directory
- Check that spaCy model is downloaded: `python -m spacy download en_core_web_sm`

## License

This project is created by Navaneeth.

## Contributing

Feel free to submit issues and enhancement requests!

## Acknowledgments

- Created by Navaneeth
- Uses Langchain + Google Gemini for AI capabilities
- Built with modern Python and React stack

