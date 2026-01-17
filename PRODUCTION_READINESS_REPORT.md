# Production Readiness Report: OBD InsightBot

**Date:** January 17, 2026
**Version:** 1.0.0
**Status:** NOT READY FOR PRODUCTION

---

## Executive Summary

This report provides a comprehensive production readiness assessment for OBD InsightBot. While the codebase demonstrates good architectural practices and security fundamentals, there are **critical issues** that must be resolved before production deployment.

**Overall Score: 6.5/10** - Needs significant fixes before production.

---

## Critical Issues (Must Fix Before Production)

### 1. In-Memory Session Storage - CRITICAL
**File:** `src/services/auth_service.py:37`

```python
_sessions: Dict[str, Tuple[int, datetime]] = {}  # In-memory, lost on restart!
```

**Problem:** User sessions are stored in a class variable in memory. This means:
- All users are logged out on application restart
- Sessions cannot be shared across multiple instances
- No persistence of authentication state

**Fix Required:** Store sessions in the database with a `sessions` table.

---

### 2. SQLAlchemy DetachedInstanceError - CRITICAL
**Files:** `src/services/auth_service.py:73`, `src/services/chat_service.py:56`

**Problem:** Objects are returned after being detached from the SQLAlchemy session, causing errors when accessing lazy-loaded attributes.

**Evidence from tests:**
```
sqlalchemy.orm.exc.DetachedInstanceError: Instance <User at 0x...> is not bound to a Session
```

**Fix Required:** Either:
- Eagerly load all needed attributes before detaching
- Return data dictionaries instead of ORM objects
- Use `expire_on_commit=False` in session configuration

---

### 3. Test Suite Failures - CRITICAL
**Files:** `tests/test_auth.py`, `tests/test_chat_service.py`

**Test Results:**
- 50 tests collected
- 7 FAILED
- 8 ERRORS
- Only 35 PASSED (70%)

**Problems:**
- No database isolation between test runs (duplicate usernames)
- Session fixture doesn't reset database state
- DetachedInstanceError issues

**Fix Required:** Add proper test database cleanup fixtures.

---

### 4. Weak Password Policy - HIGH
**File:** `src/services/auth_service.py:254-258`

```python
if not password or len(password) < 6:
    raise AuthenticationError("Password must be at least 6 characters")
```

**Problem:** Only requires 6 characters with no complexity requirements.

**Fix Required:** Implement stronger password policy:
- Minimum 8 characters
- At least one uppercase, lowercase, digit, and special character

---

## High Priority Issues

### 5. No Rate Limiting on Authentication
**File:** `src/services/auth_service.py`

**Problem:** No protection against brute force login attacks.

**Recommendation:** Implement:
- Account lockout after N failed attempts
- Progressive delays between login attempts
- IP-based rate limiting

---

### 6. SQL Injection Risk in Search
**File:** `src/services/chat_service.py:382-383`

```python
Chat.name.ilike(f"%{query}%")
```

**Status:** LOW RISK - SQLAlchemy parameterizes this query, but the pattern is worth noting.

---

### 7. Missing Input Sanitization for LLM Prompts
**File:** `src/services/granite_client.py`

**Problem:** User input is passed directly to the LLM without sanitization. While not a traditional security vulnerability, this could lead to prompt injection attacks.

**Recommendation:** Add input sanitization and prompt boundary markers.

---

## Medium Priority Issues

### 8. Insecure Default Configuration
**File:** `src/services/granite_client.py:50-51`

```python
OLLAMA_BASE_URL = "http://localhost:11434"  # HTTP, not HTTPS
```

**Problem:** Communication with Ollama is over unencrypted HTTP.

**Recommendation:** Support HTTPS for production deployments.

---

### 9. Debug Mode Exposure
**File:** `src/config/settings.py:54-56`

**Problem:** Debug mode can be enabled via environment variable. Ensure `APP_DEBUG=false` in production.

---

### 10. File Extension-Only Validation
**File:** `src/services/obd_parser.py:247`

```python
if path.suffix.lower() != ".csv":
```

**Problem:** Only checks file extension, not actual content type.

**Recommendation:** Add MIME type validation and content inspection.

---

### 11. Missing Log Rotation
**File:** `src/config/logging_config.py`

**Problem:** Logs are written to daily files but there's no automatic rotation or cleanup.

**Recommendation:** Implement `RotatingFileHandler` with size limits.

---

## Security Strengths (Good Practices Found)

| Practice | Implementation | Status |
|----------|---------------|--------|
| Password Hashing | bcrypt with 12 rounds | GOOD |
| SQL Injection Prevention | SQLAlchemy ORM | GOOD |
| Environment Config | python-dotenv | GOOD |
| Secure Token Generation | secrets.token_urlsafe(32) | GOOD |
| Session Expiry | 24-hour automatic expiry | GOOD |
| Input Validation | Username/password validation | GOOD |
| Error Logging | Comprehensive logging | GOOD |
| Cascade Delete | User data cleanup | GOOD |

---

## Test Coverage Summary

| Test File | Tests | Passed | Failed | Errors |
|-----------|-------|--------|--------|--------|
| test_auth.py | 13 | 9 | 4 | 0 |
| test_chat_service.py | 9 | 1 | 1 | 8 |
| test_obd_parser.py | 15 | 15 | 0 | 0 |
| test_severity_classifier.py | 13 | 11 | 2 | 0 |
| **TOTAL** | **50** | **36** | **7** | **8** |

**Coverage:** 72% pass rate (needs improvement to 95%+)

---

## Dependency Audit

| Dependency | Version | Security Status |
|------------|---------|-----------------|
| SQLAlchemy | >=2.0.0 | OK |
| bcrypt | >=4.0.0 | OK |
| pandas | >=2.0.0 | OK |
| PyQt6 | >=6.5.0 | OK |
| langchain | >=0.1.0 | Review for updates |
| chromadb | >=0.4.0 | OK |

**Recommendation:** Pin exact versions for reproducible builds.

---

## Required Actions Before Production

### Immediate (P0 - Blockers)
1. [ ] Fix session storage - move to database persistence
2. [ ] Fix SQLAlchemy DetachedInstanceError issues
3. [ ] Fix test suite - add database isolation
4. [ ] Strengthen password policy

### Short-term (P1 - High Priority)
5. [ ] Add rate limiting for authentication
6. [ ] Add input sanitization for LLM prompts
7. [ ] Pin dependency versions in requirements.txt
8. [ ] Add log rotation

### Medium-term (P2 - Recommended)
9. [ ] Add HTTPS support for Ollama communication
10. [ ] Add MIME type validation for file uploads
11. [ ] Improve test coverage to 95%+
12. [ ] Add integration tests

---

## Architecture Review

### Strengths
- Clean separation of concerns (services, models, UI)
- Comprehensive OBD-II fault code database
- Dual AI backend support (Ollama + watsonx.ai)
- Mock mode fallback for demo/testing
- Proper context managers for database sessions

### Weaknesses
- No API layer (desktop-only)
- Single database file (SQLite) - not scalable
- No caching layer
- No health checks or monitoring endpoints

---

## Conclusion

OBD InsightBot has a solid foundation with good architectural practices. However, the **critical issues** identified (session storage, SQLAlchemy errors, test failures) must be resolved before production deployment.

**Estimated time to production-ready:** Address P0 issues first (1-2 days of focused work), then P1 issues (2-3 days), achieving a minimum viable production state.

---

*Report generated by Claude Code production readiness review*
