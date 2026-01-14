# OBD InsightBot - Detailed Implementation Plan

## Project Overview

**Project Name:** OBD InsightBot: Conversational Vehicle Diagnostics
**Client:** IBM (John McNamara, Product Owner)
**Technology Stack:** Python, IBM Granite (via watsonx.ai), Desktop GUI Framework

---

## Table of Contents

1. [Technology Stack & Architecture](#1-technology-stack--architecture)
2. [IBM Granite API Integration](#2-ibm-granite-api-integration)
3. [Phase 1: Project Setup & Infrastructure](#3-phase-1-project-setup--infrastructure)
4. [Phase 2: Core Backend Services](#4-phase-2-core-backend-services)
5. [Phase 3: IBM Granite RAG Pipeline](#5-phase-3-ibm-granite-rag-pipeline)
6. [Phase 4: User Interface Development](#6-phase-4-user-interface-development)
7. [Phase 5: Voice Features Integration](#7-phase-5-voice-features-integration)
8. [Phase 6: Testing & Quality Assurance](#8-phase-6-testing--quality-assurance)
9. [Phase 7: Documentation & Deployment](#9-phase-7-documentation--deployment)
10. [File Structure](#10-file-structure)
11. [API Specifications](#11-api-specifications)
12. [Database Schema](#12-database-schema)

---

## 1. Technology Stack & Architecture

### 1.1 Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.11+ | Primary development language |
| **LLM Provider** | IBM Granite via watsonx.ai | Natural language generation, RAG |
| **GUI Framework** | PyQt6 / PySide6 | Cross-platform desktop application |
| **Database** | SQLite | Local user data & chat history storage |
| **ORM** | SQLAlchemy | Database abstraction layer |
| **Speech-to-Text** | IBM Watson Speech to Text | Voice dictation (BR6) |
| **Text-to-Speech** | IBM Watson Text to Speech | Voice responses (BR7) |
| **Vector Store** | ChromaDB / FAISS | RAG document embeddings |
| **Data Processing** | Pandas | OBD-II CSV log parsing |

### 1.2 IBM Granite Models

| Use Case | Model ID | Purpose |
|----------|----------|---------|
| **Chat/RAG** | `ibm/granite-3-8b-instruct` | Primary conversational AI |
| **Embeddings** | `ibm/granite-embedding-107m-multilingual` | Document vectorization for RAG |
| **Code Analysis** | `ibm/granite-34b-code-instruct` | Technical fault code analysis |

### 1.3 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      OBD InsightBot Application                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   PyQt6 GUI     │  │  Voice Module   │  │  File Handler   │  │
│  │  (Frontend)     │  │  (STT/TTS)      │  │  (CSV Parser)   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│  ┌─────────────────────────────┴─────────────────────────────┐  │
│  │                    Core Service Layer                      │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │ Auth Service│ │Chat Service │ │  OBD Parser Service │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
│                                │                                │
│  ┌─────────────────────────────┴─────────────────────────────┐  │
│  │                    RAG Pipeline Layer                      │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │  Retriever  │ │  Augmenter  │ │  Granite Generator  │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
│                                │                                │
│  ┌─────────────────────────────┴─────────────────────────────┐  │
│  │                    Data Layer                              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │   SQLite    │ │  ChromaDB   │ │  IBM watsonx.ai     │  │  │
│  │  │  (Users/    │ │  (Vector    │ │  (Granite API)      │  │  │
│  │  │   Chats)    │ │   Store)    │ │                     │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. IBM Granite API Integration

### 2.1 Prerequisites

```bash
# Required Python packages
pip install ibm-watsonx-ai langchain-ibm chromadb pandas PyQt6 SQLAlchemy bcrypt
```

### 2.2 Environment Configuration

```python
# config/settings.py
import os

# IBM watsonx.ai Configuration
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

# Model IDs
GRANITE_CHAT_MODEL = "ibm/granite-3-8b-instruct"
GRANITE_EMBEDDING_MODEL = "ibm/granite-embedding-107m-multilingual"

# Generation Parameters
GENERATION_PARAMS = {
    "decoding_method": "greedy",
    "max_new_tokens": 1024,
    "temperature": 0.7,
    "top_p": 0.9,
    "repetition_penalty": 1.1
}
```

### 2.3 Granite Client Initialization

```python
# services/granite_client.py
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_ibm import ChatWatsonx, WatsonxEmbeddings

class GraniteClient:
    def __init__(self):
        self.credentials = {
            "url": WATSONX_URL,
            "apikey": WATSONX_API_KEY
        }

        # Initialize Chat Model
        self.chat_model = ChatWatsonx(
            model_id=GRANITE_CHAT_MODEL,
            url=WATSONX_URL,
            apikey=WATSONX_API_KEY,
            project_id=WATSONX_PROJECT_ID,
            params=GENERATION_PARAMS
        )

        # Initialize Embeddings Model
        self.embeddings = WatsonxEmbeddings(
            model_id=GRANITE_EMBEDDING_MODEL,
            url=WATSONX_URL,
            apikey=WATSONX_API_KEY,
            project_id=WATSONX_PROJECT_ID
        )

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate a response using Granite model"""
        full_prompt = self._build_prompt(prompt, context)
        response = self.chat_model.invoke(full_prompt)
        return response.content

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for text chunks"""
        return self.embeddings.embed_documents(texts)
```

---

## 3. Phase 1: Project Setup & Infrastructure

### 3.1 Tasks

| Task ID | Task Description | Priority | Dependency |
|---------|------------------|----------|------------|
| P1.1 | Initialize Python project with Poetry/pip | High | None |
| P1.2 | Set up project directory structure | High | P1.1 |
| P1.3 | Configure IBM watsonx.ai credentials | High | P1.1 |
| P1.4 | Set up SQLite database with SQLAlchemy | High | P1.1 |
| P1.5 | Create configuration management system | Medium | P1.2 |
| P1.6 | Set up logging infrastructure | Medium | P1.2 |
| P1.7 | Create unit test framework (pytest) | Medium | P1.2 |

### 3.2 Deliverables

- `pyproject.toml` / `requirements.txt` with all dependencies
- Project folder structure (see Section 10)
- `.env.example` template for environment variables
- Database initialization scripts
- Logging configuration

---

## 4. Phase 2: Core Backend Services

### 4.1 User Authentication Service (BR1)

**Requirements Covered:** BR1.1, BR1.2, BR1.3, BR1.4

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P2.1 | Create User model with SQLAlchemy | High |
| P2.2 | Implement password hashing (bcrypt) | High |
| P2.3 | Create user registration service | High |
| P2.4 | Create user login/logout service | High |
| P2.5 | Implement session management | High |
| P2.6 | Create account deletion service | Medium |

**Implementation Details:**

```python
# models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import bcrypt

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
```

### 4.2 OBD-II Log Parser Service (BR2)

**Requirements Covered:** BR2.1, BR2.2, BR2.3

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P2.7 | Create CSV file validator | High |
| P2.8 | Implement OBD-II metrics parser | High |
| P2.9 | Create fault code extractor | High |
| P2.10 | Build metrics normalization service | High |
| P2.11 | Implement data validation rules | High |
| P2.12 | Create error handling for invalid files | Medium |

**Key OBD-II Metrics to Parse:**

| Metric | PID | Description | Normal Range |
|--------|-----|-------------|--------------|
| Engine RPM | 0x0C | Engine revolutions per minute | 600-7000 RPM |
| Vehicle Speed | 0x0D | Current speed | 0-255 km/h |
| Coolant Temp | 0x05 | Engine coolant temperature | 70-105°C |
| Intake Air Temp | 0x0F | Intake air temperature | -40 to 215°C |
| Throttle Position | 0x11 | Throttle position percentage | 0-100% |
| Fuel Level | 0x2F | Fuel tank level | 0-100% |
| Engine Load | 0x04 | Calculated engine load | 0-100% |
| Fuel Pressure | 0x0A | Fuel pressure | 0-765 kPa |
| MAF Rate | 0x10 | Mass air flow rate | 0-655.35 g/s |
| O2 Sensor | 0x14-1B | Oxygen sensor readings | 0-1.275V |

**Fault Code Categories:**

| Prefix | Category | Support Level |
|--------|----------|---------------|
| P0xxx | Generic Powertrain | Full Support |
| P1xxx | Manufacturer-Specific Powertrain | Limited |
| P2xxx | Generic Powertrain | Full Support |
| P3xxx | Generic Powertrain | Full Support |
| C0xxx | Generic Chassis | Full Support |
| B0xxx | Generic Body | Full Support |
| U0xxx | Generic Network | Full Support |

**Implementation:**

```python
# services/obd_parser.py
import pandas as pd
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class OBDMetric:
    name: str
    value: float
    unit: str
    status: str  # 'normal', 'warning', 'critical'
    timestamp: Optional[str] = None

@dataclass
class FaultCode:
    code: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    is_generic: bool

class OBDParser:
    # Normal ranges for metrics
    METRIC_RANGES = {
        'engine_rpm': {'min': 600, 'max': 7000, 'warning_low': 500, 'warning_high': 6500},
        'coolant_temp': {'min': 70, 'max': 105, 'warning_low': 60, 'warning_high': 110},
        'vehicle_speed': {'min': 0, 'max': 200, 'warning_low': 0, 'warning_high': 180},
        'throttle_position': {'min': 0, 'max': 100, 'warning_low': 0, 'warning_high': 95},
        'engine_load': {'min': 0, 'max': 100, 'warning_low': 0, 'warning_high': 90},
    }

    # Generic fault code definitions
    FAULT_CODES = {
        'P0100': ('Mass Air Flow Circuit Malfunction', 'warning'),
        'P0101': ('Mass Air Flow Circuit Range/Performance', 'warning'),
        'P0102': ('Mass Air Flow Circuit Low Input', 'warning'),
        'P0103': ('Mass Air Flow Circuit High Input', 'warning'),
        'P0115': ('Engine Coolant Temperature Circuit Malfunction', 'critical'),
        'P0116': ('Engine Coolant Temperature Circuit Range/Performance', 'warning'),
        'P0117': ('Engine Coolant Temperature Circuit Low Input', 'warning'),
        'P0118': ('Engine Coolant Temperature Circuit High Input', 'critical'),
        'P0120': ('Throttle Position Sensor Circuit Malfunction', 'critical'),
        'P0130': ('O2 Sensor Circuit Malfunction (Bank 1 Sensor 1)', 'warning'),
        'P0169': ('Incorrect Fuel Composition', 'warning'),
        'P0300': ('Random/Multiple Cylinder Misfire Detected', 'critical'),
        'P0301': ('Cylinder 1 Misfire Detected', 'critical'),
        'P0420': ('Catalyst System Efficiency Below Threshold', 'warning'),
        'P0500': ('Vehicle Speed Sensor Malfunction', 'warning'),
        'P0505': ('Idle Control System Malfunction', 'warning'),
        # ... extend with more fault codes
    }

    def parse_csv(self, file_path: str) -> dict:
        """Parse OBD-II CSV log file"""
        try:
            df = pd.read_csv(file_path)
            return self._extract_metrics(df)
        except Exception as e:
            raise OBDParseError(f"Failed to parse CSV: {str(e)}")

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate if file is a valid OBD-II log"""
        if not file_path.endswith('.csv'):
            return False, "File must be a .csv file"

        try:
            df = pd.read_csv(file_path)
            required_columns = self._get_required_columns(df)
            if not required_columns:
                return False, "No valid OBD-II data found in file"
            return True, "Valid OBD-II log file"
        except Exception as e:
            return False, f"Invalid file format: {str(e)}"

    def extract_fault_codes(self, df: pd.DataFrame) -> list[FaultCode]:
        """Extract and categorize fault codes from data"""
        fault_codes = []
        # Implementation for fault code extraction
        return fault_codes

    def classify_metric_status(self, metric: str, value: float) -> str:
        """Classify metric as normal, warning, or critical"""
        ranges = self.METRIC_RANGES.get(metric)
        if not ranges:
            return 'normal'

        if value < ranges['warning_low'] or value > ranges['warning_high']:
            return 'critical'
        elif value < ranges['min'] or value > ranges['max']:
            return 'warning'
        return 'normal'
```

### 4.3 Chat Management Service (BR3)

**Requirements Covered:** BR3.1, BR3.2, BR3.3, BR3.4

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P2.13 | Create Chat model | High |
| P2.14 | Create Message model | High |
| P2.15 | Implement chat creation with log association | High |
| P2.16 | Implement chat history retrieval | High |
| P2.17 | Implement chat rename functionality | Medium |
| P2.18 | Implement chat deletion | Medium |
| P2.19 | Implement chat export (to .txt) | Medium |

**Implementation:**

```python
# models/chat.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), default="New Chat")
    obd_log_path = Column(String(500))
    parsed_metrics = Column(JSON)  # Store parsed OBD data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    severity = Column(String(20))  # 'critical', 'warning', 'normal' (BR8)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
```

---

## 5. Phase 3: IBM Granite RAG Pipeline

### 5.1 RAG Architecture

**Requirements Covered:** BR4.1, BR4.2, BR4.3, BR5.1, BR5.2, BR5.3, BR5.4

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ User Query   │───▶│ Query        │───▶│ Retriever    │       │
│  │              │    │ Processor    │    │ (ChromaDB)   │       │
│  └──────────────┘    └──────────────┘    └──────┬───────┘       │
│                                                  │               │
│                                                  ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Response     │◀───│ Granite LLM  │◀───│ Context      │       │
│  │ Formatter    │    │ Generator    │    │ Augmenter    │       │
│  └──────┬───────┘    └──────────────┘    └──────────────┘       │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ Severity     │  (BR8: Danger Level Classification)           │
│  │ Classifier   │                                               │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Tasks

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P3.1 | Set up ChromaDB vector store | High |
| P3.2 | Implement document chunking for OBD data | High |
| P3.3 | Create embedding generation service | High |
| P3.4 | Implement similarity search retriever | High |
| P3.5 | Build context augmentation service | High |
| P3.6 | Create prompt templates for different query types | High |
| P3.7 | Implement response generation with Granite | High |
| P3.8 | Build severity classification system (BR8) | High |
| P3.9 | Create fault code knowledge base | High |
| P3.10 | Implement follow-up question handling | Medium |

### 5.3 Implementation

```python
# services/rag_pipeline.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

class RAGPipeline:
    def __init__(self, granite_client: GraniteClient):
        self.granite = granite_client
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

    def index_obd_data(self, parsed_data: dict, chat_id: int):
        """Index parsed OBD data into vector store"""
        documents = self._create_documents(parsed_data)
        chunks = self.text_splitter.split_documents(documents)

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.granite.embeddings,
            collection_name=f"chat_{chat_id}"
        )

    def query(self, user_query: str, chat_context: dict) -> dict:
        """Process user query through RAG pipeline"""
        # 1. Retrieve relevant context
        relevant_docs = self.vector_store.similarity_search(user_query, k=5)

        # 2. Build augmented prompt
        prompt = self._build_prompt(user_query, relevant_docs, chat_context)

        # 3. Generate response with Granite
        response = self.granite.generate_response(prompt)

        # 4. Classify severity (BR8)
        severity = self._classify_severity(response, chat_context)

        return {
            "response": response,
            "severity": severity,
            "sources": [doc.metadata for doc in relevant_docs]
        }

    def _build_prompt(self, query: str, docs: list, context: dict) -> str:
        """Build context-aware prompt for Granite"""
        template = """You are OBD InsightBot, an expert automotive diagnostic assistant.

You are analyzing OBD-II diagnostic data for a vehicle. Use the following context
to answer the user's question accurately and in simple, non-technical language.

VEHICLE DATA CONTEXT:
{context}

RELEVANT INFORMATION:
{retrieved_docs}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer in clear, conversational language suitable for non-technical users
2. If the data shows abnormal readings, explain the potential implications
3. If asked about something not in the data, clearly state that information is not available
4. For fault codes, provide the code definition and potential causes
5. Include safety recommendations when relevant

RESPONSE:"""

        return template.format(
            context=self._format_context(context),
            retrieved_docs=self._format_docs(docs),
            query=query
        )

    def _classify_severity(self, response: str, context: dict) -> str:
        """Classify response severity for BR8 (danger level)"""
        # Check for critical indicators
        critical_keywords = ['immediate', 'dangerous', 'stop driving', 'critical',
                           'severe', 'emergency', 'safety risk']
        warning_keywords = ['attention', 'monitor', 'soon', 'potential',
                          'recommend', 'check', 'abnormal']

        response_lower = response.lower()

        # Check fault codes severity
        if context.get('fault_codes'):
            for code in context['fault_codes']:
                if code.get('severity') == 'critical':
                    return 'critical'

        # Check response content
        if any(kw in response_lower for kw in critical_keywords):
            return 'critical'
        elif any(kw in response_lower for kw in warning_keywords):
            return 'warning'

        return 'normal'
```

### 5.4 Prompt Templates

```python
# prompts/templates.py

VEHICLE_SUMMARY_PROMPT = """
Analyze the following OBD-II data and provide a comprehensive vehicle health summary:

METRICS:
{metrics}

FAULT CODES:
{fault_codes}

Provide a summary that includes:
1. Overall vehicle health status
2. Any concerning metrics with explanations
3. Fault code explanations if present
4. Recommended actions

Keep the language simple and accessible for non-technical users.
"""

FAULT_CODE_EXPLANATION_PROMPT = """
Explain the following OBD-II fault code in simple terms:

FAULT CODE: {fault_code}

Provide:
1. What this code means
2. Common causes
3. Potential symptoms the driver might notice
4. Recommended actions
5. Urgency level (can they continue driving or should they stop immediately)
"""

METRIC_ANALYSIS_PROMPT = """
Analyze the following vehicle metric:

METRIC: {metric_name}
VALUE: {value} {unit}
NORMAL RANGE: {normal_range}
STATUS: {status}

Explain:
1. What this metric measures
2. Whether the current value is concerning
3. What might cause abnormal readings
4. Any recommended actions
"""
```

---

## 6. Phase 4: User Interface Development

### 6.1 UI Components (PyQt6)

**Requirements Covered:** BR1, BR2, BR3, BR4, BR8

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P4.1 | Create main application window | High |
| P4.2 | Implement login/registration screens (BR1) | High |
| P4.3 | Create file upload dialog with validation (BR2) | High |
| P4.4 | Build chat interface with message display | High |
| P4.5 | Implement chat history sidebar (BR3) | High |
| P4.6 | Add severity color coding (BR8) | High |
| P4.7 | Create settings/profile menu | Medium |
| P4.8 | Implement chat rename/delete context menu | Medium |
| P4.9 | Add chat export functionality | Medium |
| P4.10 | Create loading/progress indicators | Medium |

### 6.2 Screen Layouts

#### Login Screen (BR1.2)
```
┌─────────────────────────────────────┐
│         OBD InsightBot              │
│                                     │
│    ┌─────────────────────────┐      │
│    │     Username            │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │     Password            │      │
│    └─────────────────────────┘      │
│                                     │
│    [  Login  ]  [ Register ]        │
│                                     │
└─────────────────────────────────────┘
```

#### Main Chat Screen
```
┌─────────────────────────────────────────────────────────────┐
│  OBD InsightBot                              [User] [⚙️]    │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  Chat        │   Welcome! Upload an OBD-II log to begin.   │
│  History     │                                              │
│              │   ┌────────────────────────────────────┐     │
│  ──────────  │   │ 🟢 Your vehicle appears healthy.  │     │
│  📁 Honda    │   │ Engine RPM: 850 (Normal)          │     │
│     Civic    │   │ Coolant Temp: 92°C (Normal)       │     │
│  📁 Toyota   │   │ No fault codes detected.          │     │
│     Camry    │   └────────────────────────────────────┘     │
│              │                                              │
│  ──────────  │   ┌────────────────────────────────────┐     │
│  [+ New Chat]│   │ 🔴 CRITICAL: P0300 detected       │     │
│              │   │ Multiple cylinder misfire.         │     │
│              │   │ Recommend immediate inspection.    │     │
│              │   └────────────────────────────────────┘     │
│              │                                              │
│              ├──────────────────────────────────────────────┤
│              │ [🎤] Type your question...        [Send]     │
└──────────────┴──────────────────────────────────────────────┘
```

### 6.3 Severity Color Coding (BR8)

```python
# ui/styles.py

SEVERITY_STYLES = {
    'critical': {
        'background': '#FFEBEE',  # Light red
        'border': '#F44336',       # Red
        'icon': '🔴',
        'text_color': '#C62828'
    },
    'warning': {
        'background': '#FFF8E1',  # Light amber
        'border': '#FFC107',       # Amber
        'icon': '🟡',
        'text_color': '#F57F17'
    },
    'normal': {
        'background': '#E8F5E9',  # Light green
        'border': '#4CAF50',       # Green
        'icon': '🟢',
        'text_color': '#2E7D32'
    }
}
```

---

## 7. Phase 5: Voice Features Integration

### 7.1 Speech-to-Text Dictation (BR6)

**Requirements Covered:** BR6.1, BR6.2, BR6.3, BR6.4

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P5.1 | Integrate IBM Watson Speech-to-Text API | High |
| P5.2 | Implement microphone capture | High |
| P5.3 | Create dictation button and UI | High |
| P5.4 | Implement silence detection (BR6.3) | Medium |
| P5.5 | Handle microphone permission errors (BR6.4) | Medium |
| P5.6 | Support caret position insertion (BR6.2) | Medium |

### 7.2 Voice Conversation Mode (BR7)

**Requirements Covered:** BR7.1, BR7.2, BR7.3

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P5.7 | Integrate IBM Watson Text-to-Speech API | High |
| P5.8 | Implement voice mode toggle | High |
| P5.9 | Create audio playback system | High |
| P5.10 | Implement end-pointing detection (BR7.2) | Medium |
| P5.11 | Add wake word detection (BR7.3) - Optional | Low |
| P5.12 | Create voice mode UI indicators | Medium |

### 7.3 Implementation

```python
# services/voice_service.py
from ibm_watson import SpeechToTextV1, TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
import threading

class VoiceService:
    def __init__(self, api_key: str, url: str):
        # Speech-to-Text
        stt_authenticator = IAMAuthenticator(api_key)
        self.stt = SpeechToTextV1(authenticator=stt_authenticator)
        self.stt.set_service_url(url)

        # Text-to-Speech
        tts_authenticator = IAMAuthenticator(api_key)
        self.tts = TextToSpeechV1(authenticator=tts_authenticator)
        self.tts.set_service_url(url)

        self.is_recording = False
        self.silence_threshold = 3.0  # seconds

    def start_dictation(self, callback) -> None:
        """Start speech-to-text dictation (BR6.1)"""
        self.is_recording = True
        threading.Thread(target=self._record_and_transcribe, args=(callback,)).start()

    def stop_dictation(self) -> None:
        """Stop dictation recording"""
        self.is_recording = False

    def speak_response(self, text: str) -> None:
        """Convert text to speech and play (BR7.1)"""
        response = self.tts.synthesize(
            text,
            voice='en-US_MichaelV3Voice',
            accept='audio/wav'
        ).get_result()

        self._play_audio(response.content)

    def _record_and_transcribe(self, callback):
        """Record audio and transcribe in real-time"""
        # Implementation with PyAudio and WebSocket streaming
        pass

    def _detect_silence(self, audio_data, threshold_seconds: float) -> bool:
        """Detect silence for auto-stop (BR6.3)"""
        # Implementation for silence detection
        pass
```

---

## 8. Phase 6: Testing & Quality Assurance

### 8.1 Test Categories

| Test Type | Coverage | Tools |
|-----------|----------|-------|
| Unit Tests | Services, Models, Parsers | pytest, pytest-cov |
| Integration Tests | API integrations, Database | pytest, responses |
| UI Tests | PyQt6 components | pytest-qt |
| End-to-End Tests | Full user flows | pytest, selenium |
| Performance Tests | Response times, Load | locust |

### 8.2 Test Cases by Feature

#### BR1 - Account Management Tests
```python
# tests/test_auth.py
class TestAuthentication:
    def test_user_registration_success(self):
        """BR1.1: User creates an account"""
        pass

    def test_user_login_valid_credentials(self):
        """BR1.2: User logs in with valid credentials"""
        pass

    def test_user_login_invalid_credentials(self):
        """BR1.2: User login fails with invalid credentials"""
        pass

    def test_user_logout(self):
        """BR1.3: User logs out successfully"""
        pass

    def test_user_account_deletion(self):
        """BR1.4: User deletes their account"""
        pass
```

#### BR2 - File Upload Tests
```python
# tests/test_obd_parser.py
class TestOBDParser:
    def test_valid_csv_upload(self):
        """BR2.1: Valid OBD-II CSV file is processed"""
        pass

    def test_invalid_file_type_rejected(self):
        """BR2.2: Non-CSV file is rejected"""
        pass

    def test_valid_csv_invalid_data_rejected(self):
        """BR2.3: CSV without OBD-II data is rejected"""
        pass

    def test_unauthenticated_user_redirect(self):
        """BR2.4: Unauthenticated user redirected to login"""
        pass
```

#### BR4/BR5 - Granite Response Tests
```python
# tests/test_rag_pipeline.py
class TestRAGPipeline:
    def test_vehicle_summary_healthy(self):
        """BR4.1: Summary when all metrics normal"""
        pass

    def test_vehicle_summary_abnormal(self):
        """BR4.2: Summary when metrics are abnormal"""
        pass

    def test_query_unavailable_metric(self):
        """BR4.3: Query about unavailable data"""
        pass

    def test_fault_code_explanation(self):
        """BR5.1: Specific fault code explanation"""
        pass

    def test_all_fault_codes_summary(self):
        """BR5.2: Summary of all fault codes"""
        pass
```

### 8.3 Tasks

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P6.1 | Set up pytest framework and configuration | High |
| P6.2 | Write unit tests for authentication service | High |
| P6.3 | Write unit tests for OBD parser | High |
| P6.4 | Write integration tests for Granite API | High |
| P6.5 | Write UI component tests | Medium |
| P6.6 | Create test fixtures and mock data | High |
| P6.7 | Set up CI/CD pipeline for automated testing | Medium |
| P6.8 | Perform manual QA testing | High |
| P6.9 | Create test OBD-II log files | High |

---

## 9. Phase 7: Documentation & Deployment

### 9.1 Documentation Tasks

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P7.1 | Write user manual | High |
| P7.2 | Create API documentation | Medium |
| P7.3 | Write installation guide | High |
| P7.4 | Create troubleshooting guide | Medium |
| P7.5 | Prepare demo presentation | High |

### 9.2 Deployment Tasks

| Task ID | Task Description | Priority |
|---------|------------------|----------|
| P7.6 | Create Windows installer (PyInstaller) | High |
| P7.7 | Bundle all dependencies | High |
| P7.8 | Create .env configuration wizard | Medium |
| P7.9 | Test installation on clean Windows system | High |
| P7.10 | Prepare release package | High |

### 9.3 Packaging Configuration

```python
# pyinstaller.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*', 'assets'),
        ('prompts/*', 'prompts'),
    ],
    hiddenimports=[
        'ibm_watsonx_ai',
        'langchain_ibm',
        'chromadb',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OBDInsightBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico',
)
```

---

## 10. File Structure

```
obd-insightbot/
├── src/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # Configuration management
│   │   └── logging_config.py        # Logging setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                  # SQLAlchemy base
│   │   ├── user.py                  # User model (BR1)
│   │   ├── chat.py                  # Chat model (BR3)
│   │   └── message.py               # Message model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication (BR1)
│   │   ├── chat_service.py          # Chat management (BR3)
│   │   ├── obd_parser.py            # OBD-II parsing (BR2)
│   │   ├── granite_client.py        # IBM Granite API client
│   │   ├── rag_pipeline.py          # RAG implementation (BR4, BR5)
│   │   ├── voice_service.py         # Voice features (BR6, BR7)
│   │   └── severity_classifier.py   # Danger levels (BR8)
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main application window
│   │   ├── login_screen.py          # Login/Register (BR1)
│   │   ├── chat_screen.py           # Chat interface (BR4)
│   │   ├── history_sidebar.py       # Chat history (BR3)
│   │   ├── file_upload_dialog.py    # File upload (BR2)
│   │   ├── voice_controls.py        # Voice UI (BR6, BR7)
│   │   └── styles.py                # UI styles and themes
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py             # Prompt templates
│   └── utils/
│       ├── __init__.py
│       ├── validators.py            # Input validation
│       └── helpers.py               # Utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_auth.py                 # Auth tests
│   ├── test_obd_parser.py           # Parser tests
│   ├── test_rag_pipeline.py         # RAG tests
│   ├── test_chat_service.py         # Chat tests
│   └── fixtures/
│       └── sample_obd_logs/         # Test OBD-II files
├── assets/
│   ├── icon.ico
│   └── images/
├── docs/
│   ├── user_manual.md
│   ├── installation_guide.md
│   └── api_documentation.md
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
└── IMPLEMENTATION_PLAN.md
```

---

## 11. API Specifications

### 11.1 Internal Service APIs

#### AuthService
```python
class AuthService:
    def register(username: str, password: str) -> User
    def login(username: str, password: str) -> tuple[User, str]  # (user, session_token)
    def logout(session_token: str) -> bool
    def delete_account(user_id: int) -> bool
    def validate_session(session_token: str) -> Optional[User]
```

#### ChatService
```python
class ChatService:
    def create_chat(user_id: int, obd_file_path: str) -> Chat
    def get_user_chats(user_id: int) -> list[Chat]
    def get_chat_messages(chat_id: int) -> list[Message]
    def rename_chat(chat_id: int, new_name: str) -> Chat
    def delete_chat(chat_id: int) -> bool
    def export_chat(chat_id: int, format: str) -> str  # Returns file path
```

#### RAGPipeline
```python
class RAGPipeline:
    def index_obd_data(parsed_data: dict, chat_id: int) -> None
    def query(user_query: str, chat_context: dict) -> dict
    def get_vehicle_summary(chat_id: int) -> dict
    def explain_fault_code(code: str) -> dict
```

### 11.2 IBM watsonx.ai API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ml/v1/text/generation` | POST | Generate text with Granite |
| `/ml/v1/text/embeddings` | POST | Generate embeddings |
| `/speech-to-text/api/v1/recognize` | POST | Transcribe audio |
| `/text-to-speech/api/v1/synthesize` | POST | Generate speech |

---

## 12. Database Schema

### 12.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │     chats       │       │    messages     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │──┐    │ id (PK)         │
│ username        │  │    │ user_id (FK)    │◀─┘    │ chat_id (FK)    │◀─┘
│ password_hash   │  │    │ name            │       │ role            │
│ created_at      │  └───▶│ obd_log_path    │       │ content         │
└─────────────────┘       │ parsed_metrics  │       │ severity        │
                          │ created_at      │       │ created_at      │
                          │ updated_at      │       └─────────────────┘
                          └─────────────────┘
```

### 12.2 SQL Schema

```sql
-- Users table (BR1)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chats table (BR2, BR3)
CREATE TABLE chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) DEFAULT 'New Chat',
    obd_log_path VARCHAR(500),
    parsed_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages table (BR4, BR5, BR8)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    severity VARCHAR(20),       -- 'critical', 'warning', 'normal'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_chats_created_at ON chats(created_at);
```

---

## Summary: Implementation Phases & Requirements Mapping

| Phase | Requirements Covered | Priority |
|-------|---------------------|----------|
| Phase 1: Setup | Infrastructure | High |
| Phase 2: Backend | BR1, BR2, BR3 | High (MUST) |
| Phase 3: RAG | BR4, BR5, BR8 | High (MUST) |
| Phase 4: UI | BR1-BR5, BR8 | High (MUST) |
| Phase 5: Voice | BR6, BR7 | Medium (SHOULD) |
| Phase 6: Testing | All | High |
| Phase 7: Deploy | All | High |

---

## Appendix: Dependencies

### requirements.txt

```
# Core
python>=3.11

# IBM watsonx.ai & Granite
ibm-watsonx-ai>=1.0.0
langchain-ibm>=0.1.0
ibm-watson>=8.0.0

# LangChain & RAG
langchain>=0.1.0
langchain-community>=0.0.10
chromadb>=0.4.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# GUI
PyQt6>=6.5.0

# Database
SQLAlchemy>=2.0.0

# Security
bcrypt>=4.0.0
python-dotenv>=1.0.0

# Audio
pyaudio>=0.2.13
sounddevice>=0.4.6

# Testing
pytest>=7.0.0
pytest-qt>=4.2.0
pytest-cov>=4.0.0

# Packaging
pyinstaller>=6.0.0
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Group 18 - OBD InsightBot*
