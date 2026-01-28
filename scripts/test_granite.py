#!/usr/bin/env python3
"""
Quick test script to verify local Granite model is working via llama-cpp-python.
Run: python scripts/test_granite.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_llama_cpp_installed():
    """Check if llama-cpp-python is installed."""
    print("Checking if llama-cpp-python is installed...")
    try:
        import llama_cpp
        print(f"  llama-cpp-python version: {llama_cpp.__version__}")
        return True
    except ImportError:
        print("  llama-cpp-python is not installed.")
        print("  Install with: pip install llama-cpp-python")
        return False


def check_huggingface_hub():
    """Check if huggingface-hub is installed."""
    print("\nChecking if huggingface-hub is installed...")
    try:
        import huggingface_hub
        print(f"  huggingface-hub version: {huggingface_hub.__version__}")
        return True
    except ImportError:
        print("  huggingface-hub is not installed.")
        print("  Install with: pip install huggingface-hub")
        return False


def check_model_available():
    """Check if a Granite GGUF model is available locally."""
    print("\nChecking for Granite model file...")

    from src.config.settings import get_settings
    settings = get_settings()

    # Check explicit path
    if settings.granite_model_path and Path(settings.granite_model_path).is_file():
        model_path = settings.granite_model_path
        size_mb = Path(model_path).stat().st_size / (1024 * 1024)
        print(f"  Found model at: {model_path} ({size_mb:.1f} MB)")
        return model_path

    # Check models directory
    candidate = settings.models_dir / settings.granite_model_file
    if candidate.is_file():
        size_mb = candidate.stat().st_size / (1024 * 1024)
        print(f"  Found model at: {candidate} ({size_mb:.1f} MB)")
        return str(candidate)

    print(f"  Model not found at: {candidate}")
    print(f"  Expected repo: {settings.granite_model_repo}")
    print(f"  Expected file: {settings.granite_model_file}")
    print("\n  The model will be auto-downloaded on first run.")
    print("  Or download manually:")
    print(f"    pip install huggingface-hub")
    print(f"    huggingface-cli download {settings.granite_model_repo} {settings.granite_model_file} --local-dir {settings.models_dir}")
    return None


def test_generation(model_path):
    """Test a simple generation with the local Granite model."""
    print(f"\nLoading model from {model_path}...")
    try:
        from llama_cpp import Llama

        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_gpu_layers=0,
            verbose=False,
        )
        print("  Model loaded successfully!")

        print("\nTesting chat generation...")
        result = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is an OBD-II fault code? Answer in one sentence."},
            ],
            max_tokens=100,
            temperature=0.7,
        )

        content = result["choices"][0]["message"]["content"]
        print(f"  Generation successful!")
        print(f"\n  Response: {content[:200]}")
        return True

    except Exception as e:
        print(f"  Error during generation: {e}")
        return False


def main():
    print("=" * 50)
    print("OBD InsightBot - Local Granite Model Test")
    print("=" * 50)

    # Check dependencies
    has_llama = check_llama_cpp_installed()
    has_hf = check_huggingface_hub()

    if not has_llama:
        print("\nllama-cpp-python is required. Install it and try again.")
        sys.exit(1)

    # Check model
    model_path = check_model_available()

    if not model_path:
        print("\nModel not found locally. It will be auto-downloaded when you run the app.")
        if has_hf:
            print("Or run the app once to trigger the download.")
        sys.exit(0)

    # Test generation
    if not test_generation(model_path):
        sys.exit(1)

    print("\n" + "=" * 50)
    print("All checks passed! Ready to run OBD InsightBot.")
    print("=" * 50)
    print("\nRun the app with: python -m src.main")


if __name__ == "__main__":
    main()
