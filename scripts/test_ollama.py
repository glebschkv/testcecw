#!/usr/bin/env python3
"""
Quick test script to verify Ollama and Granite are working.
Run: python scripts/test_ollama.py
"""

import sys
import requests

OLLAMA_URL = "http://localhost:11434"

def check_ollama_running():
    """Check if Ollama server is running."""
    print("Checking if Ollama is running...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running!")
            return True
    except requests.exceptions.ConnectionError:
        print("✗ Ollama is not running.")
        print("  Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Ollama: {e}")
        return False

def check_granite_model():
    """Check if Granite model is available."""
    print("\nChecking for Granite model...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            granite_models = [m for m in model_names if "granite" in m.lower()]

            if granite_models:
                print(f"✓ Found Granite models: {granite_models}")
                return granite_models[0]
            else:
                print("✗ No Granite model found.")
                print("  Install with: ollama pull granite3.3:2b")
                print(f"  Available models: {model_names}")
                return None
    except Exception as e:
        print(f"✗ Error checking models: {e}")
        return None

def test_generation(model_name):
    """Test a simple generation with Granite."""
    print(f"\nTesting generation with {model_name}...")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is an OBD-II fault code? Answer in one sentence."}
                ],
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            print(f"✓ Generation successful!")
            print(f"\nResponse: {content[:200]}...")
            return True
        else:
            print(f"✗ Generation failed: {response.status_code}")
            print(f"  {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out (this is normal for first request)")
        print("  Try running again - model needs to load")
        return False
    except Exception as e:
        print(f"✗ Error during generation: {e}")
        return False

def main():
    print("=" * 50)
    print("OBD InsightBot - Ollama/Granite Test")
    print("=" * 50)

    # Check Ollama
    if not check_ollama_running():
        sys.exit(1)

    # Check Granite model
    model = check_granite_model()
    if not model:
        sys.exit(1)

    # Test generation
    if not test_generation(model):
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✓ All checks passed! Ready to run OBD InsightBot.")
    print("=" * 50)
    print("\nRun the app with: python -m src.main")

if __name__ == "__main__":
    main()
