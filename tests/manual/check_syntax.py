import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from tools.web_search import web_search
from tools.market_structure import analyze_market_structure

print("Modules imported successfully.")

# We can't easily test BQ without creds, but we can check if the function signatures match
import inspect
sig = inspect.signature(analyze_market_structure)
print(f"analyze_market_structure signature: {sig}")

# Check web_search
sig_web = inspect.signature(web_search)
print(f"web_search signature: {sig_web}")
