# How to Access the Frontend

## 🎯 Overview

The Stereo Sonic Assistant has a React frontend that provides a beautiful UI for interacting with the voice assistant. There are **three ways** to access it:

## 📋 Prerequisites

### Option 1: Install Node.js (Recommended for Development)

1. **Download Node.js**: https://nodejs.org/
   - Download the LTS version (recommended)
   - Run the installer
   - Make sure to check "Add to PATH" during installation

2. **Verify Installation**:
   ```powershell
   node --version
   npm --version
   ```

## 🚀 Method 1: React Development Server (Best for Development)

This runs the React app in development mode with hot reload.

### Steps:

1. **Install Node.js** (if not already installed)
2. **Navigate to frontend directory**:
   ```powershell
   cd frontend
   ```

3. **Install dependencies**:
   ```powershell
   npm install
   ```
   This will install React and all dependencies (takes 2-5 minutes)

4. **Start the development server**:
   ```powershell
   npm start
   ```

5. **Access the frontend**:
   - The app will automatically open in your browser at: **http://localhost:3000**
   - If it doesn't open automatically, manually navigate to: http://localhost:3000
   - The frontend will automatically connect to the backend at http://127.0.0.1:8000

### Features:
- ✅ Hot reload (changes reflect immediately)
- ✅ Development tools
- ✅ Easy debugging
- ✅ Best developer experience

### Note:
- The backend must be running at http://127.0.0.1:8000
- If backend is on a different port, update `frontend/src/App.js`:
  ```javascript
  const API_BASE_URL = 'http://127.0.0.1:YOUR_PORT';
  ```

## 🏗️ Method 2: Build and Run Standalone App (Best for Production)

This builds the React app and runs it via pywebview as a standalone desktop application.

### Steps:

1. **Install Node.js** (if not already installed)

2. **Build the React app**:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```
   This creates an optimized production build in `frontend/build/`

3. **Run the standalone app**:
   ```powershell
   .\venv\Scripts\python.exe app.py
   ```
   
   Or use the batch file:
   ```powershell
   .\run_app.bat
   ```

4. **Access**:
   - A desktop window will open automatically
   - The app runs as a standalone desktop application
   - No browser needed!

### Features:
- ✅ Standalone desktop app
- ✅ No browser needed
- ✅ Optimized production build
- ✅ Better performance

## 🌐 Method 3: Direct HTML Access (Quick Test)

If you just want to quickly test without building:

1. **Build the React app** (one time):
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Serve the build folder**:
   ```powershell
   # Using Python's built-in server
   cd frontend\build
   ..\..\venv\Scripts\python.exe -m http.server 3000
   ```

3. **Access**:
   - Open browser to: http://localhost:3000

## 📝 Quick Start Commands

### Development Mode:
```powershell
# Terminal 1 - Backend
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm start
```

### Production Mode (Standalone):
```powershell
# Build frontend
cd frontend
npm install
npm run build
cd ..

# Run standalone app
.\venv\Scripts\python.exe app.py
```

## 🔧 Configuration

### API Base URL

If your backend is running on a different port, update the frontend configuration:

**File**: `frontend/src/App.js`

```javascript
// Change this line:
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

// To your backend URL, e.g.:
const API_BASE_URL = 'http://127.0.0.1:8000';
```

### Environment Variables (Optional)

Create `frontend/.env`:
```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

## 🐛 Troubleshooting

### Node.js Not Found

**Error**: `'node' is not recognized`

**Solution**: 
1. Install Node.js from https://nodejs.org/
2. Restart PowerShell/terminal
3. Verify: `node --version`

### npm install Fails

**Solutions**:
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall
- Check internet connection

### Port 3000 Already in Use

**Error**: `EADDRINUSE: address already in use :::3000`

**Solution**:
```powershell
# Kill process on port 3000
netstat -ano | findstr :3000
# Note the PID, then:
taskkill /PID <PID> /F

# Or use a different port:
# In package.json, change the start script or use:
PORT=3001 npm start
```

### Backend Not Connecting

**Error**: Cannot connect to backend API

**Solutions**:
1. Verify backend is running: http://127.0.0.1:8000/health
2. Check API_BASE_URL in `frontend/src/App.js`
3. Verify CORS is enabled (should be by default)
4. Check browser console for errors (F12)

### Build Fails

**Error**: Build errors during `npm run build`

**Solutions**:
- Clear build folder: `rm -rf frontend/build` (or delete manually)
- Clear node_modules: `rm -rf frontend/node_modules`
- Reinstall: `cd frontend && npm install`
- Check for syntax errors in React components

## 📚 Frontend Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── App.js              # Main app component
│   ├── App.css             # Main styles
│   ├── components/
│   │   ├── VoiceInterface.js    # Voice control UI
│   │   ├── CommandHistory.js    # Command history
│   │   ├── ChatInterface.js     # Chatbot UI
│   │   └── StatusBar.js         # Status indicator
│   └── index.js            # React entry point
└── package.json            # Dependencies
```

## ✨ Features Available in Frontend

- 🎤 **Voice Interface**: Click to speak or say "Sonic" to activate
- 💬 **Chat Mode**: Chat with Stereo Sonic AI
- 📝 **Command Mode**: Execute voice commands
- 📊 **Command History**: See your command history
- 🎨 **Beautiful UI**: Modern, responsive design
- 📡 **Real-time Status**: See connection and listening status

## 🎯 Recommended Approach

### For Development:
Use **Method 1** (React Dev Server) - Best for development and testing

### For End Users:
Use **Method 2** (Standalone App) - Best user experience

## 📞 Need Help?

- Check `README.md` for full documentation
- Check `SETUP_COMPLETE.md` for setup details
- Verify backend is running: http://127.0.0.1:8000/health
- Check browser console (F12) for errors

