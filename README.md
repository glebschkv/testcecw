# OBD InsightBot

**Conversational Vehicle Diagnostics Powered by IBM Granite**

A desktop app that helps you understand your vehicle's OBD-II diagnostic data through simple conversations.

---

## Quick Start (Copy & Paste)

### Windows (PowerShell)

```powershell
# 1. Clone the repo
git clone https://github.com/glebschkv/testcecw.git
cd testcecw

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python src/main.py
```

### macOS / Linux

```bash
# 1. Clone the repo
git clone https://github.com/glebschkv/testcecw.git
cd testcecw

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python src/main.py
```

---

## Install Ollama + IBM Granite AI (Optional but Recommended)

The app works in demo mode without AI. For full AI-powered responses:

### Windows (PowerShell - Run as Administrator)

```powershell
# 1. Download Ollama installer
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"

# 2. Install Ollama (follow the installer)
Start-Process "$env:TEMP\OllamaSetup.exe" -Wait

# 3. Close and reopen PowerShell, then pull the AI model
ollama pull granite3.3:2b

# 4. Verify it works
ollama run granite3.3:2b "Hello"
```

### macOS

```bash
# 1. Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the IBM Granite model
ollama pull granite3.3:2b

# 3. Verify it works
ollama run granite3.3:2b "Hello"
```

### Linux (Ubuntu/Debian)

```bash
# 1. Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama service
sudo systemctl start ollama

# 3. Pull the IBM Granite model
ollama pull granite3.3:2b

# 4. Verify it works
ollama run granite3.3:2b "Hello"
```

**That's it!** The app auto-detects Ollama when running. No configuration needed.

---

## What You Can Do

1. **Create Account** - Register and log in
2. **Upload OBD-II Log** - Click "New Chat" and select your CSV file
3. **Ask Questions** - Examples:
   - "What is wrong with my vehicle?"
   - "Explain fault code P0300"
   - "Is my engine temperature normal?"

---

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- ~2GB disk space for AI model (optional)

---

## Troubleshooting

### "python is not recognized"
Download Python from https://www.python.org/downloads/ and check "Add to PATH" during install.

### "No module named PyQt6"
```bash
pip install PyQt6
```

### "No module named X"
```bash
pip install -r requirements.txt
```

### "ollama is not recognized" (Windows)
Close and reopen PowerShell after installing Ollama.

### App won't start
Make sure virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| GUI | PyQt6 |
| AI | IBM Granite (via Ollama) |
| Database | SQLite |

---

## License

University software engineering course project - Group 18
