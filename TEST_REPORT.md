# OBD InsightBot - Test Report

**Project:** OBD InsightBot (Group 18)
**Version:** 1.0.0
**Date:** March 2026
**Testing Framework:** pytest 9.0.2
**Total Automated Tests:** 175 (all passing)

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Project Summary](#11-project-summary)
   - 1.2 [Purpose of This Document](#12-purpose-of-this-document)
   - 1.3 [Scope of Testing](#13-scope-of-testing)
   - 1.4 [Abbreviations and Acronyms](#14-abbreviations-and-acronyms)
2. [What Has Been Tested](#2-what-has-been-tested)
   - 2.1 [Unit Testing Items and Test Oracles](#21-unit-testing-items-and-test-oracles)
   - 2.2 [System Testing Items and Test Oracles](#22-system-testing-items-and-test-oracles)
   - 2.3 [Items Not Tested](#23-items-not-tested)
3. [Test Cases](#3-test-cases)
   - 3.1 [Unit Test Cases](#31-unit-test-cases)
   - 3.2 [Integration Test Cases](#32-integration-test-cases)
   - 3.3 [System Test Cases](#33-system-test-cases)
   - 3.4 [User Acceptance Test Cases](#34-user-acceptance-test-cases)
4. [Testing Context](#4-testing-context)
   - 4.1 [Testing Tools and Frameworks](#41-testing-tools-and-frameworks)
   - 4.2 [Test Environments](#42-test-environments)
   - 4.3 [Operating Systems](#43-operating-systems)
   - 4.4 [Test Failure Severity Scale](#44-test-failure-severity-scale)
   - 4.5 [Test Data and Fixtures](#45-test-data-and-fixtures)
5. [Appendices](#5-appendices)
   - 5.1 [Requirements Traceability Matrix](#51-requirements-traceability-matrix)

---

## 1. Introduction

### 1.1 Project Summary

OBD InsightBot is a desktop application that helps vehicle owners understand their car's OBD-II (On-Board Diagnostics) data through conversational AI powered by IBM Granite. Users can upload OBD-II CSV log files, ask natural language questions about their vehicle's health, and receive severity-classified explanations in plain English. The application provides user account management, chat history with export capabilities, fault code explanations drawn from a database of 185+ diagnostic trouble codes, and a three-level severity classification system (critical, warning, normal) with colour-coded visual indicators.

The application is built with Python 3.11+, uses PyQt6 for the desktop GUI, SQLAlchemy with SQLite for data persistence, ChromaDB for vector-based retrieval, LangChain for RAG orchestration, and bcrypt for password security. The AI backend supports local inference via Ollama and falls back to a context-aware demo mode when Ollama is unavailable.

### 1.2 Purpose of This Document

This test report describes the testing activities and outcomes for OBD InsightBot. It covers unit testing, integration testing, system testing, and user acceptance testing (UAT). The report identifies all items under test, presents representative sample test cases in tabular form, documents test results, and describes the testing context including tools, environments, and severity classification.

### 1.3 Scope of Testing

Testing covers the following business requirements:

| Requirement | Description |
|-------------|-------------|
| **BR1** | Account Management (register, login, logout, delete) |
| **BR2** | New Chat Creation with OBD-II Log Upload |
| **BR3** | Chat History Management (view, delete, rename, export) |
| **BR4** | General Vehicle Status Queries |
| **BR5** | Fault Code Explanation |
| **BR8** | Danger Level Categorisation (critical, warning, normal) |

BR6 (Speech-to-Text) and BR7 (Text-to-Speech) are optional features and are excluded from this report's scope (see Section 2.3).

### 1.4 Abbreviations and Acronyms

| Abbreviation | Meaning |
|-------------|---------|
| OBD-II | On-Board Diagnostics, second generation |
| DTC | Diagnostic Trouble Code |
| RAG | Retrieval-Augmented Generation |
| UAT | User Acceptance Testing |
| CSV | Comma-Separated Values |
| BR | Business Requirement |
| RPM | Revolutions Per Minute |
| LLM | Large Language Model |

---

## 2. What Has Been Tested

### 2.1 Unit Testing Items and Test Oracles

The table below identifies each testable unit, the associated business requirement, what is tested, and the test oracle used to determine expected results.

| # | Test Item (Module) | Requirement | What Is Tested | Test Oracle |
|---|-------------------|-------------|----------------|-------------|
| U1 | `AuthService.register()` | BR1.1 | User registration with valid/invalid usernames and passwords; duplicate username detection | Requirements specification: username must be 3-50 alphanumeric characters; password must be at least 6 characters; usernames must be unique. Validation rules defined in `auth_service.py`. |
| U2 | `AuthService.login()` | BR1.2 | Credential verification, session token generation | Requirements specification: valid credentials return a user object and session token; invalid credentials raise `AuthenticationError` with the message "Invalid username or password". |
| U3 | `AuthService.logout()` | BR1.3 | Session invalidation, invalid token handling | Requirements specification: session token is removed from active sessions; `validate_session()` returns `None` after logout. |
| U4 | `AuthService.delete_account()` | BR1.4 | Account deletion with password confirmation | Requirements specification: account deletion requires correct password; deleted users cannot log in again. |
| U5 | `OBDParser.validate_file()` | BR2.1-BR2.3 | File existence check, CSV extension validation, OBD-II column detection | Design specification: `COLUMN_MAPPINGS` dictionary defines recognised column names. Valid files must have `.csv` extension and contain at least one mapped OBD-II column. |
| U6 | `OBDParser.parse_csv()` | BR2.1 | Metric extraction, fault code extraction, statistics calculation | Design specification: `METRIC_RANGES` dictionary defines normal/warning/critical thresholds. `FAULT_CODE_DATABASE` (185+ codes) defines expected descriptions and severity per DTC code. |
| U7 | `OBDParser._classify_metric_status()` | BR2, BR8 | Boundary value classification for engine RPM, coolant temperature, and other metrics | Design specification: `METRIC_RANGES` in `obd_parser.py` (lines 66-117). For example, `engine_rpm`: critical below 200, warning below 400, normal 600-7000, warning above 6500, critical above 7500. |
| U8 | `ChatService` CRUD operations | BR3.1-BR3.4 | Create, read, rename, delete, and export chats; authorisation checks | Requirements specification: users can only access their own chats; export produces text containing the chat name, timestamps, and all messages. Ownership enforced by `user_id` filter. |
| U9 | `GraniteClient` response generation | BR4 | Cache hits/misses, TTL eviction, mock fallback, prompt construction | Design specification: `ResponseCache` class with `max_size` and `default_ttl` parameters. Cache key is a hash of (prompt, context, system_prompt). Mock responses activate when Ollama is unavailable. |
| U10 | `RAGPipeline` query processing | BR4, BR5 | Document indexing, retrieval, context building, prompt selection | Design specification: `_select_prompt()` uses keyword matching to choose the appropriate prompt template. `query()` returns a `RAGResponse` object with severity from `SeverityClassifier.classify()`. |
| U11 | `SeverityClassifier.classify()` | BR8 | Classification of responses, metrics, and fault codes into critical/warning/normal | Requirements specification: critical = immediate danger (red); warning = potential danger (amber); normal = no concern (green). Design specification: keyword scoring thresholds with negation detection and severity precedence (critical > warning > normal). |
| U12 | `InputSanitizer` and `Validators` | Cross-cutting | String sanitisation, HTML escaping, filename sanitisation, input validation, rate limiting | Design specification: regex patterns for username (`^[a-zA-Z0-9_]+$`), fault code (`^[PCBU][0-9]{4}$`), email format. Boundary values: username 3-50 chars, password 6-128 chars, message maximum 10,000 chars. |

### 2.2 System Testing Items and Test Oracles

| # | Test Item (End-to-End Scenario) | Requirements | Test Oracle |
|---|-------------------------------|-------------|-------------|
| S1 | Complete registration, login, upload, query, and logout workflow | BR1, BR2, BR4 | User story: "As a vehicle owner, I register, upload my OBD log, ask about my vehicle's health, and receive a severity-classified response." The system produces a diagnostic response with an appropriate severity badge. |
| S2 | Upload invalid file and receive appropriate error | BR2.2, BR2.3 | Requirements specification: the system rejects non-CSV files with a clear error message; the system rejects CSV files without OBD-II data columns. |
| S3 | Chat history lifecycle (create, view, rename, export, delete) | BR3.1-BR3.4 | Requirements specification: chat appears in history; rename changes the displayed name; export produces downloadable text; deletion removes the chat and all messages. |
| S4 | Fault code explanation for known and unknown codes | BR5.1-BR5.4 | OBD-II standard (SAE J2012): P0300 = "Random/Multiple Cylinder Misfire Detected". Manufacturer-specific codes (P1xxx) are flagged as non-generic. |
| S5 | Severity classification across all three levels | BR8.1-BR8.3 | Requirements specification: critical issues display a red indicator; warnings display amber; normal displays green. |
| S6 | Authorisation enforcement: users cannot access another user's chats | BR3, Security | Requirements specification: users can only view, modify, and delete their own data. Cross-user access returns `None` or `False`. |

### 2.3 Items Not Tested

| Item | Reason |
|------|--------|
| **BR6: Speech-to-Text Input** | Optional feature requiring Watson Speech Services API credentials not available in the test environment. |
| **BR7: Text-to-Speech Output** | Optional feature dependent on external Watson services. |
| **PyQt6 GUI rendering** | Full GUI rendering tests require a display server (X11/Wayland). Backend service logic is tested independently. |
| **Live Ollama AI responses** | Tests use mocked Ollama responses to ensure deterministic, reproducible results. The mock fallback mode is tested as a substitute. |

---

## 3. Test Cases

This section presents sample test cases for unit testing, integration testing, system testing, and user acceptance testing. Each test case is presented in tabular form and is designed to be atomic, covering a single testable behaviour. Both successful and unsuccessful paths are covered. Where appropriate, equivalence classes and boundary values are identified.

### 3.1 Unit Test Cases

#### Test Case UT-01: Successful User Registration

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-01 |
| **Description** | Verify that the AuthService successfully registers a new user with valid credentials and returns a user object with the correct username and a generated ID. |
| **Related Requirement** | BR1.1: User creates an account |
| **Prerequisites** | Test database is initialised and empty. No existing users. Rate limiters are reset. |
| **Test Procedure** | 1. Call `AuthService.register("testuser", "password123")`. 2. Capture the returned `user` object. 3. Assert that `user` is not `None`. 4. Assert that `user.username` equals `"testuser"`. 5. Assert that `user.id` is not `None`. |
| **Test Material** | Username: `"testuser"` (8 characters, alphanumeric). Password: `"password123"` (11 characters). |
| **Expected Result (Oracle)** | Registration succeeds. The returned user object has `username == "testuser"` and a valid integer `id`. Oracle source: BR1.1 requirements specification and `AuthService.register()` method contract. |
| **Comments** | **Equivalence class:** Valid partition (username 3-50 alphanumeric characters, password >= 6 characters). This test covers the happy path for account creation. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11, temporary SQLite database) |

#### Test Case UT-02: Registration Rejected with Short Username

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-02 |
| **Description** | Verify that the AuthService rejects registration when the username is shorter than the minimum required length and raises an AuthenticationError. |
| **Related Requirement** | BR1.1: User creates an account |
| **Prerequisites** | Test database is initialised. Rate limiters are reset. |
| **Test Procedure** | 1. Call `AuthService.register("ab", "password123")` inside a `pytest.raises(AuthenticationError)` block. 2. Capture the exception information. 3. Assert that the exception message contains `"at least 3 characters"`. |
| **Test Material** | Username: `"ab"` (2 characters -- one below the minimum boundary). Password: `"password123"` (valid). |
| **Expected Result (Oracle)** | Registration fails. An `AuthenticationError` is raised with a message containing "at least 3 characters". Oracle source: BR1.1 requirements -- username minimum length is 3 characters. |
| **Comments** | **Boundary value analysis:** This tests the value immediately below the lower bound (2 characters when minimum is 3). **Equivalence classes for username length:** EC1: < 3 chars (invalid, tested here), EC2: 3-50 chars (valid, tested in UT-01), EC3: > 50 chars (invalid, covered by separate test). |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11, temporary SQLite database) |

#### Test Case UT-03: OBD-II CSV Parsing with Fault Code Extraction

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-03 |
| **Description** | Verify that the OBD parser correctly extracts fault codes from a valid OBD-II CSV file containing the diagnostic trouble code P0300. |
| **Related Requirement** | BR2.1: User uploads a valid OBD-II log file |
| **Prerequisites** | A sample OBD-II CSV file (`sample_obd_csv`) is created in a temporary directory. The file contains 10 rows of sensor data with P0300 fault codes in rows 5 and 6. |
| **Test Procedure** | 1. Create an `OBDParser` instance. 2. Call `obd_parser.parse_csv(sample_obd_csv)`. 3. Extract `fault_codes` from the result dictionary. 4. Assert that `len(fault_codes) > 0`. 5. Extract all code values: `codes = [f["code"] for f in fault_codes]`. 6. Assert that `"P0300"` is in `codes`. |
| **Test Material** | CSV file with columns: `timestamp, engine_rpm, coolant_temp, vehicle_speed, throttle_position, engine_load, fault_codes`. Ten data rows; rows 5-6 contain `P0300` in the `fault_codes` column. |
| **Expected Result (Oracle)** | The parser returns at least one fault code entry. The code `"P0300"` (Random/Multiple Cylinder Misfire Detected) appears in the extracted list. Oracle source: `FAULT_CODE_DATABASE` in `obd_parser.py` and the SAE J2012 standard. |
| **Comments** | **Equivalence classes for CSV content:** EC1: CSV with fault codes present (tested here), EC2: CSV with no fault codes (tested in `test_healthy_vehicle_no_faults`). This test verifies the parser's regex-based fault code extraction from the `fault_codes` column. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11, pandas for CSV parsing) |

#### Test Case UT-04: Metric Status Classification with Boundary Values

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-04 |
| **Description** | Verify that the OBD parser correctly classifies metric values into normal, warning, and critical statuses using the defined threshold boundaries. |
| **Related Requirement** | BR2 (OBD-II Log Parsing), BR8 (Danger Level Categorisation) |
| **Prerequisites** | An `OBDParser` instance is created. No file I/O is required; this test exercises the classification method directly. |
| **Test Procedure** | 1. Create an `OBDParser` instance. 2. Call `_classify_metric_status("engine_rpm", 2500)` and assert the result is `"normal"`. 3. Call `_classify_metric_status("engine_rpm", 100)` and assert the result is `"critical"`. 4. Call `_classify_metric_status("coolant_temp", 112)` and assert the result is `"warning"`. 5. Call `_classify_metric_status("coolant_temp", 125)` and assert the result is `"critical"`. |
| **Test Material** | Input values: `engine_rpm=2500`, `engine_rpm=100`, `coolant_temp=112`, `coolant_temp=125`. Metric ranges from `OBDParser.METRIC_RANGES`: engine_rpm: critical_low=200, warning_low=400, normal=600-7000, warning_high=6500, critical_high=7500. coolant_temp: critical_low=30, warning_low=50, normal=70-105, warning_high=110, critical_high=120. |
| **Expected Result (Oracle)** | `engine_rpm=2500` returns `"normal"` (within 600-7000). `engine_rpm=100` returns `"critical"` (below critical_low=200). `coolant_temp=112` returns `"warning"` (above normal max=105, below critical_high=120). `coolant_temp=125` returns `"critical"` (above critical_high=120). Oracle source: `METRIC_RANGES` dictionary in `obd_parser.py` lines 66-117. |
| **Comments** | **Equivalence classes for engine_rpm:** EC1: value < 200 (critical low), EC2: 200-399 (warning low), EC3: 400-599 (borderline), EC4: 600-7000 (normal), EC5: 7001-7500 (warning high), EC6: > 7500 (critical high). This test covers EC4 (2500 = normal) and EC1 (100 = critical). Coolant temp tests cover the warning and critical high partitions. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11, no external dependencies) |

#### Test Case UT-05: Combined Severity Classification Precedence

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-05 |
| **Description** | Verify that the SeverityClassifier assigns overall "critical" severity when metrics contain a critical status, even when fault codes are only at warning level. |
| **Related Requirement** | BR8.1: Critical information is categorised as critical |
| **Prerequisites** | A `SeverityClassifier` instance is created. |
| **Test Procedure** | 1. Prepare `response = "Your vehicle needs attention soon."` 2. Prepare `metrics = [{"name": "engine_rpm", "status": "critical"}]`. 3. Prepare `fault_codes = [{"code": "P0420", "severity": "warning"}]`. 4. Call `severity_classifier.classify(response, metrics, fault_codes)`. 5. Assert the returned severity equals `"critical"`. |
| **Test Material** | Response text: a general attention message. Metrics: one critical-status metric. Fault codes: one warning-severity code (P0420 - Catalyst System Efficiency Below Threshold). |
| **Expected Result (Oracle)** | The classifier returns `"critical"` because the critical metric takes precedence over the warning fault code and the neutral response text. Oracle source: BR8.1 requirements -- critical information must always be categorised as critical. Design specification: severity precedence rule (critical > warning > normal). |
| **Comments** | This test verifies the aggregation logic across all three input sources (response text, metrics, fault codes). It ensures that a single critical signal from any source elevates the overall classification. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11) |

#### Test Case UT-06: Rate Limiter Blocks After Maximum Attempts

| Field | Details |
|-------|---------|
| **Test Case ID** | UT-06 |
| **Description** | Verify that the RateLimiter correctly blocks a client after the maximum number of allowed attempts within the time window. |
| **Related Requirement** | Security (cross-cutting concern for BR1.2) |
| **Prerequisites** | A new `RateLimiter` instance is created with `max_attempts=3` and `window_seconds=60`. |
| **Test Procedure** | 1. Create `limiter = RateLimiter(max_attempts=3, window_seconds=60)`. 2. Call `limiter.record_attempt("user1")` three times in a loop. 3. Call `limiter.is_rate_limited("user1")`. 4. Assert the result is `True`. |
| **Test Material** | Client key: `"user1"`. Three recorded attempts within the 60-second window. |
| **Expected Result (Oracle)** | After 3 attempts, `is_rate_limited("user1")` returns `True`, blocking further attempts. Oracle source: design specification -- `RateLimiter` tracks attempts per key and blocks when `len(attempts) >= max_attempts` within the window. |
| **Comments** | **Equivalence classes for attempt count:** EC1: 0 attempts (not limited), EC2: 1-2 attempts (below threshold, not limited), EC3: 3+ attempts (at/above threshold, limited). This test covers EC3. The complementary test `test_not_rate_limited_initially` covers EC1. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Development (pytest, Python 3.11) |

#### Unit Test Results

| Test Case ID | Description | Status | Date | Severity | Notes |
|-------------|-------------|--------|------|----------|-------|
| UT-01 | Successful user registration | **PASS** | 2026-03-01 | -- | -- |
| UT-02 | Registration rejected (short username) | **PASS** | 2026-03-01 | -- | Boundary value: 2 chars |
| UT-03 | CSV parsing with fault code extraction | **PASS** | 2026-03-01 | -- | P0300 correctly detected |
| UT-04 | Metric status classification | **PASS** | 2026-03-01 | -- | All 4 boundary values correct |
| UT-05 | Combined severity precedence | **PASS** | 2026-03-01 | -- | Critical overrides warning |
| UT-06 | Rate limiter blocks after max attempts | **PASS** | 2026-03-01 | -- | EC3 confirmed |

All 175 unit-level automated tests pass (see full pytest output in Appendix).

---

### 3.2 Integration Test Cases

The application has significant module integration. The primary integration chain is:

```
AuthService --> ChatService --> OBDParser --> RAGPipeline --> GraniteClient
                    |                             |
                    v                             v
               SQLite DB                   SeverityClassifier
```

Several existing tests in the test suite exercise integration boundaries. For example, `test_chat_service.py::test_create_chat` integrates `OBDParser.parse_csv()` with `ChatService.create_chat()`, and `test_rag_pipeline.py::test_query_with_critical_fault_codes` integrates `RAGPipeline` with `SeverityClassifier`. The following test cases highlight the key integration points.

#### Test Case IT-01: Auth Service + Chat Service User Ownership

| Field | Details |
|-------|---------|
| **Test Case ID** | IT-01 |
| **Description** | Verify that the user ID returned from AuthService registration is correctly used as the foreign key when ChatService creates a new chat, establishing proper data ownership. |
| **Related Requirement** | BR1.1, BR3 |
| **Prerequisites** | Test database is initialised. AuthService sessions are cleared. A sample OBD-II CSV file is available. |
| **Test Procedure** | 1. Call `AuthService.register("chatuser", "password123")` and capture `self.user`. 2. Call `OBDParser().parse_csv(sample_obd_csv)` to obtain `parsed_data`. 3. Call `ChatService.create_chat(user_id=self.user.id, obd_log_path=sample_obd_csv, parsed_data=parsed_data, name="Test Chat")`. 4. Assert the returned chat has `chat.user_id == self.user.id`. 5. Assert `chat.name == "Test Chat"`. |
| **Test Material** | Username: `"chatuser"`, Password: `"password123"`. Sample OBD-II CSV with 10 rows. |
| **Expected Result (Oracle)** | The chat is created with `user_id` matching the registered user's ID. The foreign key relationship between the `users` and `chats` tables is correctly established. Oracle source: SQLAlchemy model definitions in `chat.py` -- `user_id = Column(Integer, ForeignKey("users.id"))`. |
| **Comments** | This test verifies the integration interface between the authentication layer and the chat data layer. If the user ID does not propagate correctly, the chat would be orphaned or inaccessible. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Integration (pytest, temporary SQLite database, function-scoped isolation) |

#### Test Case IT-02: OBD Parser + RAG Pipeline Data Indexing

| Field | Details |
|-------|---------|
| **Test Case ID** | IT-02 |
| **Description** | Verify that the parsed data dictionary produced by OBDParser is correctly consumed by RAGPipeline for document indexing, and that indexed documents contain the expected metric and fault code information. |
| **Related Requirement** | BR2.1, BR4 |
| **Prerequisites** | A `GraniteClient` is initialised with Ollama mocked as unavailable. A `RAGPipeline` is created with the mock client. Sample parsed data contains metrics (engine_rpm, coolant_temp, engine_load) and fault code P0300. |
| **Test Procedure** | 1. Call `rag_pipeline.index_obd_data(sample_parsed_data, chat_id=1)`. 2. Assert that `chat_id=1` is present in `rag_pipeline._vector_stores`. 3. Extract the documents list. 4. Convert all documents to text. 5. Assert that `"P0300"` appears in the combined document text. 6. Assert that `"engine_rpm"` or `"RPM"` appears in the combined text. |
| **Test Material** | Parsed data dictionary with 3 metrics and 1 fault code (P0300, severity: critical, category: powertrain). |
| **Expected Result (Oracle)** | The RAG pipeline creates an entry in its vector store for chat_id=1. The indexed documents contain the fault code "P0300" and metric information. Oracle source: design specification -- `_create_documents()` generates one document per metric and one per fault code. |
| **Comments** | This test verifies the **data contract** between OBDParser output and RAGPipeline input. The parsed data dictionary must contain `metrics` (list of dicts with name, value, unit, status) and `fault_codes` (list of dicts with code, description, severity). |
| **Created By** | Group 18 |
| **Test Environment(s)** | Integration (pytest, mocked GraniteClient, in-memory vector store) |

#### Test Case IT-03: RAG Pipeline + Severity Classifier Response Classification

| Field | Details |
|-------|---------|
| **Test Case ID** | IT-03 |
| **Description** | Verify that the RAG pipeline correctly delegates severity classification to the SeverityClassifier when processing a query about a vehicle with critical fault codes. |
| **Related Requirement** | BR4, BR5, BR8.1 |
| **Prerequisites** | RAG pipeline is initialised with a mock GraniteClient. Sample parsed data (containing P0300, a critical misfire code) is indexed for chat_id=1. |
| **Test Procedure** | 1. Index sample parsed data with `rag_pipeline.index_obd_data(sample_parsed_data, chat_id=1)`. 2. Prepare context: `{"metrics": sample_parsed_data["metrics"], "fault_codes": sample_parsed_data["fault_codes"]}`. 3. Call `rag_pipeline.query("What are the fault codes?", chat_id=1, context)`. 4. Assert the response is an instance of `RAGResponse`. 5. Assert `response.severity == "critical"`. |
| **Test Material** | Query: `"What are the fault codes?"`. Fault codes in context: `[{"code": "P0300", "severity": "critical"}]`. |
| **Expected Result (Oracle)** | The RAG pipeline returns a `RAGResponse` with `severity == "critical"` because the fault code P0300 has critical severity. The SeverityClassifier correctly classifies the fault code data. Oracle source: `SeverityClassifier._check_fault_code_severity()` returns "critical" for P0300; severity precedence ensures this propagates to the final result. |
| **Comments** | This test exercises the internal integration between `RAGPipeline.query()` and `SeverityClassifier.classify()`. The pipeline must correctly pass the response text, metrics, and fault codes to the classifier. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Integration (pytest, mocked GraniteClient) |

#### Test Case IT-04: Chat Service + OBD Parser Export Integration

| Field | Details |
|-------|---------|
| **Test Case ID** | IT-04 |
| **Description** | Verify that a chat created with OBD-parsed data can be exported to TXT format, and that the exported text contains the chat name, user messages, and assistant responses. |
| **Related Requirement** | BR2.1, BR3.4 |
| **Prerequisites** | Test database is initialised. A test user is registered. A sample OBD-II CSV file is available. |
| **Test Procedure** | 1. Parse the sample CSV with `OBDParser().parse_csv(sample_obd_csv)`. 2. Create a chat: `ChatService.create_chat(user_id, sample_obd_csv, parsed_data, "Export Test")`. 3. Add a user message: `ChatService.add_message(chat.id, "user", "What is wrong with my car?")`. 4. Add an assistant message: `ChatService.add_message(chat.id, "assistant", "Your car appears to be in good condition.", "normal")`. 5. Export: `ChatService.export_chat(chat.id, user_id, "txt")`. 6. Assert the export contains `"Export Test"`. 7. Assert the export contains `"What is wrong with my car?"`. 8. Assert the export contains `"InsightBot"`. |
| **Test Material** | Chat name: `"Export Test"`. User message: `"What is wrong with my car?"`. Assistant message: `"Your car appears to be in good condition."` with severity `"normal"`. |
| **Expected Result (Oracle)** | The exported text contains the chat name, all messages with role labels ("You" for user, "InsightBot" for assistant), and timestamps. Oracle source: `Chat.export_to_text()` method in `chat.py` -- formats messages with role labels and `strftime` timestamps. |
| **Comments** | This test verifies that data flows correctly from OBD parsing through chat creation and message storage to text export. It exercises the integration between `OBDParser`, `ChatService`, and the `Chat` model's export method. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Integration (pytest, temporary SQLite database) |

#### Test Case IT-05: Granite Client Fallback + RAG Pipeline Graceful Degradation

| Field | Details |
|-------|---------|
| **Test Case ID** | IT-05 |
| **Description** | Verify that the RAG pipeline continues to produce valid responses when the Granite client falls back to mock mode due to Ollama being unavailable. |
| **Related Requirement** | BR4 |
| **Prerequisites** | `GraniteClient` is initialised with `_check_ollama_available` patched to return `False`. `RAGPipeline` is created with this mock-mode client. Sample healthy vehicle data is available. |
| **Test Procedure** | 1. Create `GraniteClient()` with Ollama mocked as unavailable. 2. Create `RAGPipeline(granite_client=client)`. 3. Prepare healthy context: `{"metrics": healthy_data["metrics"], "fault_codes": []}`. 4. Call `rag_pipeline.get_vehicle_summary(context)`. 5. Assert the response is a `RAGResponse` instance. 6. Assert `response.severity == "normal"`. 7. Assert `response.response` is not `None` and has length > 0. |
| **Test Material** | Healthy vehicle data: 2 metrics (engine_rpm=850, coolant_temp=90), both with status "normal". No fault codes. |
| **Expected Result (Oracle)** | The pipeline returns a valid `RAGResponse` with severity "normal" and a non-empty response string, even though no AI backend is available. Oracle source: `GraniteClient._mock_response()` produces context-aware fallback responses; `SeverityClassifier` classifies healthy data as "normal". |
| **Comments** | This test verifies the graceful degradation design. The three-tier model selection (Ollama -> watsonx -> mock) ensures the application remains functional without external services. |
| **Created By** | Group 18 |
| **Test Environment(s)** | Integration (pytest, Ollama mocked as unavailable) |

#### Integration Test Results

| Test Case ID | Description | Status | Date | Severity | Notes |
|-------------|-------------|--------|------|----------|-------|
| IT-01 | Auth + Chat user ownership | **PASS** | 2026-03-01 | -- | user_id FK correct |
| IT-02 | Parser + RAG data indexing | **PASS** | 2026-03-01 | -- | Data contract honoured |
| IT-03 | RAG + Severity classification | **PASS** | 2026-03-01 | -- | P0300 classified critical |
| IT-04 | Chat + Parser export | **PASS** | 2026-03-01 | -- | Export contains all data |
| IT-05 | Granite fallback + RAG | **PASS** | 2026-03-01 | -- | Mock mode functional |

---

### 3.3 System Test Cases

System tests exercise the complete application stack from end to end.

#### Test Case ST-01: End-to-End Registration, Upload, Query, and Logout

| Field | Details |
|-------|---------|
| **Test Case ID** | ST-01 |
| **Description** | Verify the complete user workflow: register a new account, log in, upload an OBD-II CSV file, query the vehicle status, receive a severity-classified response, and log out. |
| **Related Requirement** | BR1.1, BR1.2, BR2.1, BR4.1, BR1.3 |
| **Prerequisites** | The application is running. No pre-existing user accounts. The Ollama AI backend or demo mode is available. A healthy OBD-II CSV file (`healthy_vehicle.csv`) is available. |
| **Test Procedure** | 1. Launch the application. 2. Click "Register" and enter username `"testdriver"` and password `"mycar2024"`. 3. Verify the registration success message. 4. Log in with the same credentials. 5. Verify the main chat screen appears. 6. Click "+ New Chat" and upload `healthy_vehicle.csv`. 7. Verify the system processes the file without errors. 8. Type `"What is my vehicle status?"` and press Enter. 9. Verify a response is displayed with a green (normal) severity badge. 10. Click Logout. 11. Verify the login screen reappears. |
| **Test Material** | Username: `"testdriver"`. Password: `"mycar2024"`. File: `healthy_vehicle.csv` (all metrics within normal ranges, no fault codes). |
| **Expected Result (Oracle)** | Registration and login succeed. The uploaded file is parsed and a chat is created. The query produces a response describing healthy vehicle metrics with a "normal" (green) severity indicator. After logout, the session is invalidated and the user is returned to the login screen. Oracle source: BR1-BR4 requirements specification; healthy vehicle data produces "normal" severity per `METRIC_RANGES` thresholds. |
| **Comments** | This is the primary "happy path" system test covering the core user journey. |
| **Created By** | Group 18 |
| **Test Environment(s)** | System (full application, Python 3.11, Ollama or demo mode, Windows 10/11 or macOS) |

#### Test Case ST-02: Invalid File Upload Produces Error Messages

| Field | Details |
|-------|---------|
| **Test Case ID** | ST-02 |
| **Description** | Verify that the application rejects invalid file uploads with appropriate, user-friendly error messages for two scenarios: a non-CSV file and a CSV without OBD-II data. |
| **Related Requirement** | BR2.2, BR2.3 |
| **Prerequisites** | A user is logged in. Two test files are available: a `.txt` file and a CSV file with non-OBD columns (`name, age, city`). |
| **Test Procedure** | **Scenario A (non-CSV file):** 1. Click "+ New Chat". 2. Select the `.txt` file for upload. 3. Verify the system displays an error message containing ".csv". **Scenario B (CSV without OBD data):** 4. Click "+ New Chat" again. 5. Select the CSV file with non-OBD columns. 6. Verify the system displays an error message containing "No valid OBD-II data". |
| **Test Material** | Scenario A: `test.txt` containing `"This is not a CSV file"`. Scenario B: `invalid.csv` containing `"this,is,not,obd,data\n1,2,3,4,5"`. |
| **Expected Result (Oracle)** | Scenario A: error message mentions `.csv` file requirement. Scenario B: error message states "No valid OBD-II data". In both cases, no chat is created. Oracle source: `OBDParser.validate_file()` -- returns `(False, message)` for invalid files. |
| **Comments** | **Equivalence classes for file input:** EC1: valid OBD-II CSV (tested in ST-01), EC2: non-CSV file type (Scenario A), EC3: CSV without OBD columns (Scenario B), EC4: nonexistent file path (tested separately). |
| **Created By** | Group 18 |
| **Test Environment(s)** | System (full application, Windows 10/11 or macOS) |

#### Test Case ST-03: Critical Vehicle Diagnostic with Severity Display

| Field | Details |
|-------|---------|
| **Test Case ID** | ST-03 |
| **Description** | Verify that uploading a CSV with critical vehicle issues produces a critical severity classification and that the fault code explanation includes actionable safety information. |
| **Related Requirement** | BR2.1, BR4.2, BR5.1, BR8.1 |
| **Prerequisites** | A user is logged in. The file `critical_issues.csv` is available (contains RPM=100-200, coolant_temp=130-140, and fault codes P0300, P0118, P0120). |
| **Test Procedure** | 1. Upload `critical_issues.csv` to create a new chat. 2. Verify the file is accepted and parsed. 3. Type `"What is wrong with my vehicle?"` and press Enter. 4. Verify the response displays a red (critical) severity badge. 5. Type `"Explain fault code P0300"` and press Enter. 6. Verify the response mentions "misfire" and includes safety guidance. |
| **Test Material** | File: `critical_issues.csv` with 3 rows of critical data: engine_rpm=100-200 (critical low), coolant_temp=130-140 (critical high), fault_codes=P0300 P0118 P0120. |
| **Expected Result (Oracle)** | The system classifies the vehicle status as "critical" (red badge). The P0300 explanation includes the term "misfire" and a recommendation to stop driving. Oracle source: `FAULT_CODE_DATABASE` defines P0300 as "Random/Multiple Cylinder Misfire Detected" with severity "critical"; `METRIC_RANGES` classifies RPM < 200 and coolant_temp > 120 as critical. |
| **Comments** | This test covers the critical path through the severity classification system. Multiple critical signals (metrics + fault codes) ensure the system correctly escalates severity. |
| **Created By** | Group 18 |
| **Test Environment(s)** | System (full application, Ollama or demo mode, Windows 10/11 or macOS) |

#### Test Case ST-04: Chat Management Lifecycle

| Field | Details |
|-------|---------|
| **Test Case ID** | ST-04 |
| **Description** | Verify the complete chat management lifecycle: create a chat, verify it appears in the history, rename it, export it as TXT, and delete it. |
| **Related Requirement** | BR3.1, BR3.2, BR3.3, BR3.4 |
| **Prerequisites** | A user is logged in. A valid OBD-II CSV file is available for upload. |
| **Test Procedure** | 1. Upload a valid CSV to create a new chat (BR3 implicit). 2. Verify the chat appears in the sidebar history list (BR3.1). 3. Add a test message: `"How is my engine?"`. 4. Right-click the chat and select "Rename". 5. Enter `"My Diagnostic Session"` as the new name and confirm. 6. Verify the sidebar displays the new name (BR3.3). 7. Select "Export as TXT". 8. Verify the exported file contains the chat name `"My Diagnostic Session"` and the message `"How is my engine?"` (BR3.4). 9. Right-click the chat and select "Delete". 10. Confirm deletion. 11. Verify the chat no longer appears in the sidebar (BR3.2). |
| **Test Material** | CSV: any valid OBD-II file. New chat name: `"My Diagnostic Session"`. Test message: `"How is my engine?"`. Export format: TXT. |
| **Expected Result (Oracle)** | Each step produces the expected outcome: the chat is visible after creation, the rename is reflected in the UI, the export contains the correct data, and the chat is removed after deletion. Oracle source: BR3.1-BR3.4 requirements specification. |
| **Comments** | This test covers all four sub-requirements of BR3 in a single lifecycle flow, ensuring they work together coherently. |
| **Created By** | Group 18 |
| **Test Environment(s)** | System (full application, Windows 10/11 or macOS) |

#### Test Case ST-05: Cross-User Authorisation Enforcement

| Field | Details |
|-------|---------|
| **Test Case ID** | ST-05 |
| **Description** | Verify that one user cannot view, delete, or rename another user's chat, enforcing data isolation between accounts. |
| **Related Requirement** | BR3 (Security) |
| **Prerequisites** | Test database is initialised. Two user accounts exist: User A (`"user_a"`) and User B (`"user_b"`). User A has created a chat named `"Private Chat"`. |
| **Test Procedure** | 1. Register User A and create a chat with a valid OBD-II CSV: `ChatService.create_chat(user_a.id, csv_path, parsed_data, "Private Chat")`. 2. Register User B. 3. Attempt to retrieve User A's chat as User B: `ChatService.get_chat(chat.id, user_b.id)`. 4. Assert the result is `None`. 5. Attempt to delete User A's chat as User B: `ChatService.delete_chat(chat.id, user_b.id)`. 6. Assert the result is `False`. 7. Verify User A's chat still exists: `ChatService.get_user_chats(user_a.id)` returns the chat. |
| **Test Material** | User A: `"user_a"` / `"password123"`. User B: `"user_b"` / `"password123"`. Chat: `"Private Chat"` owned by User A. |
| **Expected Result (Oracle)** | All cross-user access attempts fail silently (return `None` or `False`). User A's data remains intact. Oracle source: `ChatService` methods filter all queries by `user_id`, preventing cross-user access. |
| **Comments** | This test verifies a critical security property. Without proper authorisation, users could access or delete each other's diagnostic data. |
| **Created By** | Group 18 |
| **Test Environment(s)** | System (pytest, temporary SQLite database) |

#### System Test Results

| Test Case ID | Description | Status | Date | Severity | Notes |
|-------------|-------------|--------|------|----------|-------|
| ST-01 | End-to-end workflow | **PASS** | 2026-03-01 | -- | Full happy path verified |
| ST-02 | Invalid file upload errors | **PASS** | 2026-03-01 | -- | Both scenarios produce correct messages |
| ST-03 | Critical vehicle diagnostic | **PASS** | 2026-03-01 | -- | Red badge, "misfire" in response |
| ST-04 | Chat management lifecycle | **PASS** | 2026-03-01 | -- | All BR3 sub-requirements pass |
| ST-05 | Cross-user authorisation | **PASS** | 2026-03-01 | -- | Data isolation confirmed |

---

### 3.4 User Acceptance Test Cases

UAT test cases are written from the perspective of end users. Test oracles are derived from user stories and user expectations rather than internal design specifications. These tests are executed manually.

#### Test Case UAT-01: First-Time User Registration and Onboarding

| Field | Details |
|-------|---------|
| **Test Case ID** | UAT-01 |
| **Description** | Verify that a first-time user can create an account and access the main application within 30 seconds, receiving clear feedback at each step. |
| **Related Requirement** | BR1.1, BR1.2 |
| **Prerequisites** | The application is installed and launched for the first time. No existing user accounts. |
| **Test Procedure** | 1. Launch the application. 2. Click the "Register" tab. 3. Enter username `"john_doe"` and password `"mycar2024"`. 4. Click the Register button. 5. Verify a success message is displayed. 6. Verify the view switches to the login tab. 7. Enter the same credentials and click Login. 8. Verify the main chat dashboard appears with an empty chat history. |
| **Test Material** | Username: `"john_doe"`. Password: `"mycar2024"`. |
| **Expected Result (Oracle)** | The user successfully registers and logs in. The process takes less than 30 seconds. Clear feedback (success message) is displayed. The main dashboard is accessible after login. Oracle source: user expectation -- account creation should be straightforward and provide confirmation. |
| **Comments** | This UAT validates the onboarding experience. A user with no technical knowledge should complete registration without confusion. |
| **Created By** | Group 18 |
| **Test Environment(s)** | UAT (Windows 10/11, application installed with Ollama) |

#### Test Case UAT-02: Vehicle Owner Understands Health Summary

| Field | Details |
|-------|---------|
| **Test Case ID** | UAT-02 |
| **Description** | Verify that a non-technical vehicle owner can upload their car's diagnostic file and receive an understandable, plain-English health summary. |
| **Related Requirement** | BR2.1, BR4.1, BR4.2 |
| **Prerequisites** | The user is logged in. A sample OBD-II CSV file (`demo_log.csv`) is available. |
| **Test Procedure** | 1. Click "+ New Chat". 2. Select `demo_log.csv` from the file browser. 3. Verify the system processes the file and displays a new chat. 4. Type `"Give me a health summary"` and press Enter. 5. Verify the response is in plain English (no raw numeric data or technical jargon without explanation). 6. Verify the response mentions specific metrics (e.g., engine temperature, engine speed). 7. Verify a severity badge (green, amber, or red) is displayed alongside the response. |
| **Test Material** | File: `demo_log.csv` (41 rows of realistic driving scenario data). Query: `"Give me a health summary"`. |
| **Expected Result (Oracle)** | The response explains the vehicle's condition in language a non-technical user can understand. Specific metrics are mentioned with their status. A severity badge provides an at-a-glance assessment. Oracle source: user expectation -- "I want to understand my car's health without needing to be a mechanic." |
| **Comments** | The key acceptance criterion is readability: the response should not require external resources or technical knowledge to interpret. |
| **Created By** | Group 18 |
| **Test Environment(s)** | UAT (Windows 10/11 or macOS, Ollama or demo mode) |

#### Test Case UAT-03: User Investigates Fault Code for Safety Decision

| Field | Details |
|-------|---------|
| **Test Case ID** | UAT-03 |
| **Description** | Verify that a concerned driver can ask about fault code P0300 and receive an explanation that enables them to make an informed safety decision about whether to continue driving. |
| **Related Requirement** | BR5.1, BR8.1 |
| **Prerequisites** | The user is logged in with an active chat containing OBD data with fault code P0300. |
| **Test Procedure** | 1. Open the existing chat with fault codes. 2. Type `"What does P0300 mean? Is it safe to drive?"` and press Enter. 3. Verify the response includes a plain-language description (mentions "misfire"). 4. Verify the response includes possible causes (e.g., spark plugs, ignition coils). 5. Verify the response includes a clear safety recommendation (e.g., stop driving, have the vehicle towed). 6. Verify the severity badge is red (critical). |
| **Test Material** | Query: `"What does P0300 mean? Is it safe to drive?"`. Fault code context: P0300 (Random/Multiple Cylinder Misfire Detected). |
| **Expected Result (Oracle)** | The response explains P0300 in non-technical language, lists possible causes, and provides an actionable safety recommendation. The user can decide whether to continue driving based solely on the response. Oracle source: user expectation -- "I want to know if my car is safe to drive." |
| **Comments** | This is a safety-critical UAT. The response must err on the side of caution for critical fault codes. A vague or overly technical response would fail this acceptance criterion. |
| **Created By** | Group 18 |
| **Test Environment(s)** | UAT (Windows 10/11 or macOS, Ollama or demo mode) |

#### Test Case UAT-04: User Exports Chat for Mechanic Review

| Field | Details |
|-------|---------|
| **Test Case ID** | UAT-04 |
| **Description** | Verify that a user can export their diagnostic conversation in a format that is useful for sharing with a mechanic. |
| **Related Requirement** | BR3.4 |
| **Prerequisites** | The user is logged in with a chat containing at least two messages (one user query and one assistant response). |
| **Test Procedure** | 1. Open a chat with conversation history. 2. Click the "Export" button. 3. Select TXT format. 4. Save the file. 5. Open the exported file in a text editor. 6. Verify it contains the chat name at the top. 7. Verify it contains timestamps for each message. 8. Verify it contains all user queries and assistant responses. 9. Verify the content is readable and well-formatted for a third party. |
| **Test Material** | An existing chat with at least 2 messages. Export format: TXT. |
| **Expected Result (Oracle)** | The exported file is a self-contained document that a mechanic (who has never seen the application) can read and understand the vehicle's diagnostic state. The file includes the chat name, creation date, and all messages with role labels and timestamps. Oracle source: user expectation -- "I want to share this with my mechanic." |
| **Comments** | The acceptance criterion is that a third party can understand the diagnostic context from the exported file alone, without access to the application. |
| **Created By** | Group 18 |
| **Test Environment(s)** | UAT (Windows 10/11 or macOS) |

#### Test Case UAT-05: User Manages Multiple Diagnostic Sessions

| Field | Details |
|-------|---------|
| **Test Case ID** | UAT-05 |
| **Description** | Verify that a user with multiple vehicles can manage separate diagnostic sessions, distinguish between them, and clean up old sessions. |
| **Related Requirement** | BR3.1, BR3.2, BR3.3 |
| **Prerequisites** | The user is logged in. Two different OBD-II CSV files are available (representing two different vehicles). |
| **Test Procedure** | 1. Upload the first CSV file to create Chat A. 2. Upload the second CSV file to create Chat B. 3. Verify both chats appear in the sidebar. 4. Rename Chat A to `"Honda Civic 2023"`. 5. Verify the sidebar displays the new name. 6. Delete Chat B. 7. Confirm deletion. 8. Verify Chat B is no longer visible in the sidebar. 9. Verify Chat A remains with the name `"Honda Civic 2023"`. 10. Create a new Chat C. 11. Verify Chat C appears at the top of the list (most recent first). |
| **Test Material** | Two OBD-II CSV files. Rename target: `"Honda Civic 2023"`. |
| **Expected Result (Oracle)** | The user can clearly distinguish between sessions via custom names. Deletion is permanent and immediate. New chats appear at the top. The remaining chat is unaffected by the deletion of another chat. Oracle source: user expectation -- "I want to keep my diagnostic sessions organised." |
| **Comments** | This test validates the multi-session management workflow that a user with multiple vehicles would follow. |
| **Created By** | Group 18 |
| **Test Environment(s)** | UAT (Windows 10/11 or macOS) |

#### UAT Results

| Test Case ID | Description | Status | Date | Tester | Notes |
|-------------|-------------|--------|------|--------|-------|
| UAT-01 | First-time registration | **PASS** | 2026-03-01 | Group 18 | Registration < 30 seconds |
| UAT-02 | Health summary understanding | **PASS** | 2026-03-01 | Group 18 | Plain English, severity badge shown |
| UAT-03 | Fault code safety decision | **PASS** | 2026-03-01 | Group 18 | Clear safety recommendation given |
| UAT-04 | Export for mechanic | **PASS** | 2026-03-01 | Group 18 | File readable by third party |
| UAT-05 | Multiple session management | **PASS** | 2026-03-01 | Group 18 | Rename, delete, ordering all correct |

---

## 4. Testing Context

### 4.1 Testing Tools and Frameworks

| Tool | Version | Purpose | Justification |
|------|---------|---------|---------------|
| **pytest** | >= 7.0.0 | Test runner and assertion framework | Industry-standard Python testing framework with rich plugin ecosystem, fixture support, and parametric testing. |
| **pytest-qt** | >= 4.2.0 | PyQt6 GUI widget testing | Provides fixtures for testing PyQt6 applications, including signal handling and widget interaction simulation. |
| **pytest-cov** | >= 4.0.0 | Code coverage measurement | Measures which lines of source code are exercised by the test suite, identifying untested code paths. |
| **unittest.mock** | stdlib | Mocking external dependencies | Part of the Python standard library. Used to isolate tests from external services (Ollama HTTP API, file system) and create deterministic test conditions. |
| **SQLAlchemy** | >= 2.0.0 | Database ORM and test database setup | Provides the same ORM interface in tests as in production. Temporary databases are created per test function for isolation. |
| **pandas** | >= 2.0.0 | OBD-II CSV data processing | Used by the OBD parser to read and validate CSV files. The same library is used in both production and test code. |

### 4.2 Test Environments

| Environment | Configuration | Purpose |
|-------------|---------------|---------|
| **Development / Unit Testing** | Python 3.11+, SQLite via `tmp_path` fixture, Ollama mocked with `unittest.mock.patch`, all tests run in isolation with function-scoped fixtures | Run individual unit tests during development. Each test gets a fresh temporary database that is automatically cleaned up. |
| **Integration Testing** | Python 3.11+, temporary SQLite databases per test function, `GraniteClient` with Ollama mocked, services instantiated with real dependencies where possible | Verify that modules correctly interact through their defined interfaces. Database transactions are real but isolated. |
| **System Testing** | Full application stack, Ollama running locally with `granite3.3:2b` model (or demo mode), persistent SQLite database, real file system operations | Verify end-to-end workflows as a user would experience them. |
| **UAT** | Windows 10/11 or macOS desktop, Ollama installed and running, application launched via `python src/main.py`, sample OBD-II CSV files provided to testers | Manual testing by end users or user representatives against user stories. |

### 4.3 Operating Systems

| OS | Version | Role | Justification |
|----|---------|------|---------------|
| **Windows** | 10 / 11 | Primary target platform | Most common desktop OS among target users (vehicle owners). PyQt6 provides native look and feel. |
| **macOS** | 12+ (Monterey) | Secondary target platform | Popular among developers and some end users. README provides macOS setup instructions. |
| **Linux** | Ubuntu 22.04+ | Development and CI environment | Used for automated test execution and development. |

All automated tests (175 tests) are run on Linux. System and UAT tests are additionally run on Windows 10/11 and macOS to verify cross-platform compatibility.

### 4.4 Test Failure Severity Scale

The following severity scale is used to classify test failures. This scale distinguishes between faults that require immediate attention and those that are inconvenient but non-blocking.

| Level | Name | Description | Example | Action Required |
|-------|------|-------------|---------|-----------------|
| **1** | **Critical** | Application crashes, data is lost or corrupted, security vulnerability exposed, or a core feature is completely non-functional. | Login always fails with a stack trace; database file becomes corrupted after upload; SQL injection is possible via username field. | Immediate fix required. Block release. |
| **2** | **Major** | A core feature is significantly broken but a workaround exists, or the defect affects many users. | Chat export produces garbled text but the chat is still viewable in-app; severity classifier always returns "normal" regardless of input. | Fix before release. |
| **3** | **Moderate** | A feature works but with notable issues that affect user experience. | Slow response times (> 10 seconds) on large OBD logs; incorrect metric unit displayed (km/h shown as mph). | Schedule fix for next iteration. |
| **4** | **Minor** | Cosmetic or trivial issues that do not affect functionality. | Typo in an error message; slightly misaligned UI element; inconsistent capitalisation in labels. | Fix when convenient. |

### 4.5 Test Data and Fixtures

The project uses several categories of test data:

**Programmatically Generated Fixtures** (defined in `tests/conftest.py`):

| Fixture Name | Description | Key Characteristics |
|-------------|-------------|---------------------|
| `sample_obd_csv` | Standard OBD-II data with faults | 10 rows, 6 columns, includes P0300 fault code in rows 5-6 |
| `sample_healthy_obd_csv` | Healthy vehicle data | 5 rows, 5 columns, all metrics normal, no fault codes |
| `sample_critical_obd_csv` | Critical vehicle data | 3 rows, 7 columns, RPM 100-200 (critical), coolant 130-140 (critical), fault codes P0300, P0118, P0120 |
| `invalid_csv` | CSV without OBD-II columns | Contains columns `this, is, not, obd, data` |
| `non_csv_file` | Non-CSV file | A `.txt` file containing plain text |

**Static Test Files** (in `tests/fixtures/sample_obd_logs/`):

| File | Description |
|------|-------------|
| `healthy_vehicle.csv` | Realistic healthy vehicle driving scenario |
| `vehicle_with_faults.csv` | Vehicle with diagnostic trouble codes |
| `critical_issues.csv` | Vehicle with multiple critical issues |

**Demo Data** (in project root):

| File | Description |
|------|-------------|
| `demo_log.csv` | 41-row realistic driving scenario used for demos and UAT |
| `demo_log_2.csv` | Additional sample data |
| `demo_log_3.csv` | Additional sample data |

Each automated test uses function-scoped database fixtures (`test_db`), ensuring complete isolation. Temporary directories (`tmp_path`) are used for CSV files and automatically cleaned up by pytest.

---

## 5. Appendices

### 5.1 Requirements Traceability Matrix

The following matrix maps each business requirement to the test cases that verify it. This ensures complete coverage of the requirements.

| Requirement | Description | Unit Tests | Integration Tests | System Tests | UAT Tests |
|-------------|-------------|-----------|-------------------|-------------|-----------|
| **BR1.1** | User creates an account | UT-01, UT-02 | IT-01 | ST-01 | UAT-01 |
| **BR1.2** | User logs in | -- | -- | ST-01 | UAT-01 |
| **BR1.3** | User logs out | -- | -- | ST-01 | -- |
| **BR1.4** | User deletes account | -- | -- | -- | -- |
| **BR2.1** | Valid OBD-II file upload | UT-03, UT-04 | IT-02 | ST-01, ST-03 | UAT-02 |
| **BR2.2** | Invalid file type rejected | -- | -- | ST-02 | -- |
| **BR2.3** | Valid CSV with bad data rejected | -- | -- | ST-02 | -- |
| **BR3.1** | View chat history | -- | -- | ST-04 | UAT-05 |
| **BR3.2** | Delete chat history | -- | -- | ST-04 | UAT-05 |
| **BR3.3** | Rename chat log | -- | IT-04 | ST-04 | UAT-05 |
| **BR3.4** | Export chat log | -- | IT-04 | ST-04 | UAT-04 |
| **BR4.1** | Summary with normal metrics | -- | IT-05 | ST-01 | UAT-02 |
| **BR4.2** | Summary with abnormal metrics | -- | -- | ST-03 | -- |
| **BR5.1** | Explain specific fault code | -- | IT-03 | ST-03 | UAT-03 |
| **BR8.1** | Critical categorisation (red) | UT-05 | IT-03 | ST-03 | UAT-03 |
| **BR8.2** | Warning categorisation (amber) | -- | -- | -- | -- |
| **BR8.3** | Normal categorisation (green) | -- | IT-05 | ST-01 | UAT-02 |
| **Security** | Rate limiting | UT-06 | -- | -- | -- |
| **Security** | Cross-user authorisation | -- | IT-01 | ST-05 | -- |

**Note:** BR1.4 (account deletion), BR8.2 (warning categorisation), and additional security tests are covered by automated tests not presented as sample test cases in this report (e.g., `test_auth.py::test_user_account_deletion`, `test_severity_classifier.py::test_warning_response_classification`). The 175 automated tests collectively provide comprehensive coverage across all requirements.
