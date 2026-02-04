# OBD InsightBot

**Conversational Vehicle Diagnostics Powered by IBM Granite**

A desktop app that helps you understand your vehicle's OBD-II diagnostic data through simple conversations.

---

## Quick Start

### Windows (PowerShell)

```powershell
# 1. Clone the repo
git clone https://github.com/glebschkv/testcecw.git
cd testcecw

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Upgrade pip (recommended)
python -m pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
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

## How the AI Works

The app supports multiple modes:

### 1. Local AI Mode (Recommended)
Runs IBM Granite models **directly on your machine** using `llama-cpp-python`. No external server, no API keys needed.

- On first launch, the **Granite 4.0 Tiny Preview** model (~4 GB) downloads from HuggingFace
- Works offline after the initial download

### 2. Demo Mode (Default on Windows)
If `llama-cpp-python` isn't installed (requires C++ compiler), the app runs in **demo mode**:
- Parses and displays your actual OBD-II data
- Shows real metrics, fault codes, and warnings from your uploaded file
- Provides context-aware responses based on your vehicle's data

### 3. Cloud Mode (Optional)
Connect to IBM watsonx.ai for cloud-based AI. Requires API credentials.

---

## Installing Local AI on Windows

The `llama-cpp-python` package requires a C++ compiler to build. You have two options:

### Option A: Use Pre-built Wheels (Easiest)

```powershell
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install huggingface-hub
```

### Option B: Install Build Tools

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install "Desktop development with C++" workload
3. Then run:
```powershell
pip install llama-cpp-python huggingface-hub
```

### Pre-download the Model (Optional)

```bash
pip install huggingface-hub
huggingface-cli download ibm-granite/granite-4.0-tiny-preview-GGUF granite-4.0-tiny-preview.Q4_K_M.gguf --local-dir models
```

---

## What You Can Do

1. **Create Account** - Register and log in
2. **Upload OBD-II Log** - Click "New Chat" and select your CSV file
3. **Ask Questions** - Examples:
   - "What's wrong with my vehicle?"
   - "Give me a health summary"
   - "Explain fault code P0300"
   - "Is my engine temperature normal?"
   - "Show me all issues"

---

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- ~4GB disk space for AI model (optional, not needed for demo mode)

---

## Optional Packages

These are commented out in `requirements.txt` but can be installed separately:

| Package | Purpose | Install Command |
|---------|---------|-----------------|
| llama-cpp-python | Local AI inference | See "Installing Local AI" above |
| ibm-watsonx-ai | Cloud AI (watsonx) | `pip install ibm-watsonx-ai langchain-ibm ibm-watson` |
| pyaudio | Voice input | `pip install pyaudio` |

---

## Troubleshooting

### "python is not recognized"
Download Python from https://www.python.org/downloads/ and check "Add to PATH" during install.

### "No module named PyQt6"
```bash
pip install PyQt6
```

### "ERROR: Failed building wheel for llama-cpp-python"
This is expected on Windows without a C++ compiler. The app will run in demo mode, or you can install pre-built wheels:
```powershell
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### "ibm-watsonx-ai not found"
This package is optional and only needed for cloud deployment. The app works without it.

### Model download fails
Download manually:
```bash
pip install huggingface-hub
huggingface-cli download ibm-granite/granite-4.0-tiny-preview-GGUF granite-4.0-tiny-preview.Q4_K_M.gguf --local-dir models
```

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
| AI | IBM Granite 4.0 (local) or Demo Mode |
| Database | SQLite |
| Vector Store | ChromaDB |

---

## License

University software engineering course project - Group 18
