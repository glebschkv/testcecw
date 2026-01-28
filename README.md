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

# 4. Run the app (model downloads automatically on first run)
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

# 4. Run the app (model downloads automatically on first run)
python src/main.py
```

---

## How the AI Works

The app runs IBM Granite models **directly on your machine** using `llama-cpp-python`. No external server, no API keys, no Ollama needed.

- On first launch, the Granite model (~1.5 GB) is automatically downloaded from HuggingFace
- The model runs locally in your Python process
- Works offline after the initial download
- Falls back to demo mode if the model can't be loaded

### Pre-download the Model (Optional)

If you want to download the model before running the app:

```bash
pip install huggingface-hub
huggingface-cli download ibm-granite/granite-3.3-2b-instruct-GGUF granite-3.3-2b-instruct.Q4_K_M.gguf --local-dir models
```

### Use a Larger Model

For better quality responses (requires ~5 GB disk + more RAM):

```bash
# Download the 8B model
huggingface-cli download ibm-granite/granite-3.3-8b-instruct-GGUF granite-3.3-8b-instruct.Q4_K_M.gguf --local-dir models
```

Then set in your `.env` file:
```
GRANITE_MODEL_REPO=ibm-granite/granite-3.3-8b-instruct-GGUF
GRANITE_MODEL_FILE=granite-3.3-8b-instruct.Q4_K_M.gguf
```

### Verify Setup

```bash
python scripts/test_granite.py
```

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
- ~2GB disk space for AI model

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

### Model download fails
Download the model manually:
```bash
pip install huggingface-hub
huggingface-cli download ibm-granite/granite-3.3-2b-instruct-GGUF granite-3.3-2b-instruct.Q4_K_M.gguf --local-dir models
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
| AI | IBM Granite (via llama-cpp-python) |
| Database | SQLite |

---

## License

University software engineering course project - Group 18
