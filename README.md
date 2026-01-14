# OBD InsightBot

**Conversational Vehicle Diagnostics Powered by IBM Granite**

OBD InsightBot is a desktop application that helps vehicle owners understand their OBD-II diagnostic data through natural language conversations. Using IBM Granite's large language models via watsonx.ai, it translates complex diagnostic codes and metrics into simple, actionable insights.

## Features

### Core Features (MUST HAVE)
- **BR1: Account Management** - User registration, login, logout, and account deletion
- **BR2: OBD-II Log Upload** - Upload and validate CSV log files from OBD-II scanners
- **BR3: Chat History** - View, rename, delete, and export chat conversations
- **BR4: Vehicle Status Queries** - Ask natural language questions about your vehicle
- **BR5: Fault Code Explanation** - Get plain-English explanations of diagnostic codes
- **BR8: Severity Indicators** - Color-coded responses (red/amber/green) for issue severity

### Additional Features (SHOULD HAVE)
- **BR6: Speech-to-Text** - Dictate questions using voice input
- **BR7: Voice Conversation Mode** - Full voice-based interaction (hands-free)

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| LLM | IBM Granite via watsonx.ai |
| GUI Framework | PyQt6 |
| Database | SQLite + SQLAlchemy |
| Vector Store | ChromaDB |
| Speech Services | IBM Watson STT/TTS |

## Installation

### Prerequisites
- Python 3.11 or higher
- **Option A (Recommended):** Ollama for local IBM Granite (no API key needed)
- **Option B:** IBM watsonx.ai account with API key (cloud)
- (Optional) IBM Watson Speech services for voice features

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-repo/obd-insightbot.git
cd obd-insightbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **Set up IBM Granite** (choose one option):

#### Option A: Local Ollama (Recommended - No API Key)

**Windows (PowerShell):**
```powershell
# Download and install Ollama
Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:USERPROFILE\Downloads\OllamaSetup.exe"
Start-Process "$env:USERPROFILE\Downloads\OllamaSetup.exe" -Wait

# Pull IBM Granite model (run in new terminal after install)
ollama pull granite3.3:2b

# Verify it's working
ollama run granite3.3:2b "Hello, test message"
```

**macOS/Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull IBM Granite model
ollama pull granite3.3:2b

# Verify it's working
ollama run granite3.3:2b "Hello, test message"
```

The app will auto-detect Ollama when it starts. No additional configuration needed!

#### Option B: IBM watsonx.ai (Cloud)

```bash
cp .env.example .env
# Edit .env with your IBM watsonx.ai credentials
```

5. Run the application:
```bash
python -m src.main
```

## Configuration

The app uses this priority order:
1. **Local Ollama** (auto-detected, no config needed)
2. **IBM watsonx.ai** (requires credentials in `.env`)
3. **Mock mode** (demo fallback)

### Environment Variables (`.env`)

```env
# LOCAL OLLAMA (Recommended - No API Key Needed)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=granite3.3:2b

# IBM watsonx.ai (Cloud - Optional, only if no Ollama)
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here

# IBM Watson Speech (Optional - for voice features)
WATSON_SPEECH_API_KEY=your_speech_api_key_here
WATSON_SPEECH_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
```

### Available Granite Models via Ollama

| Model | Size | Use Case |
|-------|------|----------|
| `granite3.3:2b` | ~1.5GB | Faster, lighter - good for testing |
| `granite3.3:8b` | ~5GB | More capable - better responses |

To switch models:
```bash
ollama pull granite3.3:8b
# Then set OLLAMA_MODEL=granite3.3:8b in .env
```

## Usage

1. **Create an Account**: Launch the app and register a new account
2. **Upload OBD-II Log**: Click "+ New Chat" and select your CSV log file
3. **Ask Questions**: Type or speak questions about your vehicle:
   - "What is the overall health of my vehicle?"
   - "Explain fault code P0300"
   - "Is my coolant temperature normal?"
   - "What maintenance do you recommend?"

## Project Structure

```
obd-insightbot/
├── src/
│   ├── config/          # Configuration and settings
│   ├── models/          # Database models
│   ├── services/        # Business logic services
│   ├── ui/              # PyQt6 user interface
│   ├── prompts/         # LLM prompt templates
│   ├── utils/           # Utility functions
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── docs/                # Documentation
└── requirements.txt     # Dependencies
```

## Running Tests

```bash
pytest tests/ -v --cov=src
```

## API Documentation

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed API specifications and architecture documentation.

## Severity Color Coding (BR8)

| Color | Severity | Meaning |
|-------|----------|---------|
| 🔴 Red | Critical | Immediate attention required - stop driving |
| 🟡 Amber | Warning | Should be addressed soon |
| 🟢 Green | Normal | No immediate concern |

## Supported OBD-II Metrics

- Engine RPM
- Coolant Temperature
- Vehicle Speed
- Throttle Position
- Engine Load
- Fuel Level
- Intake Air Temperature
- Battery Voltage
- And more...

## Supported Fault Codes

- Generic OBD-II codes (P0xxx, P2xxx, P3xxx)
- Chassis codes (C0xxx)
- Body codes (B0xxx)
- Network codes (U0xxx)

*Note: Manufacturer-specific codes (P1xxx) have limited support.*

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is developed as part of a university software engineering course.

## Acknowledgments

- IBM for watsonx.ai and Granite models
- John McNamara (IBM Product Owner) for project guidance
- Group 18 development team

## Contact

For questions or feedback, please open an issue on GitHub.
