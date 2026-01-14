# OBD InsightBot

**Conversational Vehicle Diagnostics Powered by IBM Granite**

A desktop app that helps you understand your vehicle's OBD-II diagnostic data through simple conversations.

---

## Quick Start (Copy & Paste)

### Windows

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

## Optional: Set Up AI (IBM Granite via Ollama)

The app works in demo mode without AI setup. For full AI features:

### Windows

```powershell
# Download and install Ollama from https://ollama.com/download
# Then run:
ollama pull granite3.3:2b
```

### macOS / Linux

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull granite3.3:2b
```

The app auto-detects Ollama when running. No config needed!

---

## What You Can Do

1. **Create Account** - Register and log in
2. **Upload OBD-II Log** - Click "New Chat" and select your CSV file
3. **Ask Questions** - Examples:
   - "What is wrong with my vehicle?"
   - "Explain fault code P0300"
   - "Is my engine temperature normal?"

---

## Screenshots

The app features a modern, sophisticated UI with:
- Dark sidebar with chat history
- Color-coded severity indicators (Critical/Warning/Normal)
- Clean message bubbles
- Indigo accent theme

---

## Requirements

- Python 3.8+
- pip (Python package manager)

---

## Troubleshooting

### "No module named PyQt6"
```bash
pip install PyQt6
```

### "No module named X"
```bash
pip install -r requirements.txt
```

### App won't start
Make sure you're in the project directory and virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

---

## Project Structure

```
testcecw/
├── src/
│   ├── ui/           # User interface (PyQt6)
│   ├── services/     # Business logic
│   ├── models/       # Database models
│   └── main.py       # Entry point
├── requirements.txt  # Dependencies
└── README.md
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

---

## Need Help?

Open an issue on GitHub or check the troubleshooting section above.
