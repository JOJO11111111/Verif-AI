"""Convenience launcher: loads .env then starts the Streamlit app.

Usage:
    python run.py
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print(f"ERROR: Missing API keys in .env: {', '.join(missing)}")
    print("Copy .env.example to .env and fill in your keys.")
    sys.exit(1)

subprocess.run(["streamlit", "run", "app.py"])