# How to Set Gemini API Key

## 🔑 Step-by-Step Guide

### Step 1: Get Your Gemini API Key

1. **Go to Google AI Studio**:
   - Visit: https://makersuite.google.com/app/apikey
   - Or visit: https://aistudio.google.com/app/apikey
   
2. **Sign in** with your Google account

3. **Create API Key**:
   - Click "Create API Key" button
   - Select your Google Cloud project (or create a new one)
   - Copy the generated API key
   - ⚠️ **Important**: Save this key securely - you won't be able to see it again!

### Step 2: Create `.env` File

Create a file named `.env` in the **root directory** of the project:

**Location**: `E:\Stero Sonic Assistant\.env`

### Step 3: Add API Key to `.env` File

Open the `.env` file and add your API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

**Example:**
```env
GEMINI_API_KEY=AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz
```

### Step 4: Add Other Optional Variables (Recommended)

While you're at it, add other configuration variables:

```env
# Required for AI functionality
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Email functionality
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password_here

# Optional - File paths
CONTACTS_FILE_PATH=./data/contacts.txt
STORED_DATA_PATH=./data/stored_data.txt
SCREENSHOT_PATH=./screenshots/screenshot.png
CAMERA_IMAGE_PATH=./screenshots/camera_image.png
MUSIC_DIR=E:\Music
LENS_BUTTON_IMAGE=./assets/lens_button.png
```

## 📝 Quick Commands (Windows PowerShell)

### Create `.env` File with API Key

```powershell
# Navigate to project root
cd "E:\Stero Sonic Assistant"

# Create .env file
@"
GEMINI_API_KEY=your_gemini_api_key_here
"@ | Out-File -FilePath .env -Encoding utf8
```

### Edit `.env` File

```powershell
# Using Notepad
notepad .env

# Using PowerShell ISE
ise .env
```

### Verify API Key is Set

```powershell
# Check if .env file exists
Test-Path .env

# Read .env file (don't share this!)
Get-Content .env

# Test in Python
.\venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key Set!' if os.getenv('GEMINI_API_KEY') else 'API Key NOT Set!')"
```

## ✅ Verify It's Working

### Test API Key in Python

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('GEMINI_API_KEY'); print('✅ API Key is set!' if key else '❌ API Key NOT set!'); print(f'Key length: {len(key) if key else 0}')"
```

### Test with Backend Server

1. Start the backend server:
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

2. Test chatbot endpoint:
```powershell
$body = @{
    message = "Hello"
    use_tools = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri http://127.0.0.1:8000/api/chatbot/chat `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body `
    -UseBasicParsing
```

If you get a response, the API key is working! ✅

## 🚨 Troubleshooting

### Error: "GEMINI_API_KEY not found in environment variables"

**Solution:**
1. Make sure `.env` file exists in the root directory
2. Check the file is named exactly `.env` (not `.env.txt`)
3. Verify the API key line starts with `GEMINI_API_KEY=` (no spaces)
4. Make sure there are no quotes around the API key value
5. Restart the backend server after creating/editing `.env`

### Error: "Invalid API Key"

**Solution:**
1. Verify you copied the complete API key
2. Check for extra spaces or characters
3. Make sure the API key is active in Google AI Studio
4. Try generating a new API key

### Error: "API Key not loading"

**Solution:**
1. Make sure `python-dotenv` is installed:
   ```powershell
   .\venv\Scripts\python.exe -m pip install python-dotenv
   ```

2. Verify the `.env` file is in the project root (same folder as `app.py`)

3. Check file encoding (should be UTF-8)

### Test Environment Variable Loading

```powershell
.\venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GEMINI_API_KEY:', os.getenv('GEMINI_API_KEY', 'NOT FOUND'))"
```

## 🔒 Security Best Practices

1. **Never commit `.env` to Git**:
   - The `.env` file is already in `.gitignore`
   - Never share your API key publicly

2. **Keep API Key Secret**:
   - Don't share it in screenshots or code
   - Don't post it in chat or forums

3. **Rotate Keys if Compromised**:
   - If you suspect your key is exposed, generate a new one in Google AI Studio
   - Revoke the old key

4. **Use Environment Variables in Production**:
   - For production deployments, use system environment variables
   - Or use secure secret management services

## 📚 Additional Resources

- **Google AI Studio**: https://aistudio.google.com/
- **Gemini API Documentation**: https://ai.google.dev/docs
- **API Key Management**: https://aistudio.google.com/app/apikey

## 🎯 Quick Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ **Required** | Your Google Gemini API key |
| `EMAIL_ADDRESS` | Optional | Gmail address for email features |
| `EMAIL_PASSWORD` | Optional | Gmail app password |
| `CONTACTS_FILE_PATH` | Optional | Path to contacts file |
| `STORED_DATA_PATH` | Optional | Path to stored data file |
| `SCREENSHOT_PATH` | Optional | Path for screenshots |
| `CAMERA_IMAGE_PATH` | Optional | Path for camera images |

## ✨ After Setting Up

Once you've set the API key:

1. **Restart the backend server** (if running)
2. **Test the chatbot** to verify it works
3. **Try voice commands** - say "Sonic" and ask questions!

Your Stereo Sonic Assistant is now ready to use AI features! 🚀

