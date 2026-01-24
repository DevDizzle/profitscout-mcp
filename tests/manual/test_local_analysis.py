import asyncio
import os
import sys
import logging

# Add src to path so imports work
sys.path.append(os.path.join(os.getcwd(), "src"))

from dotenv import load_dotenv

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

# Load env vars
load_dotenv()

from tools.stock_analysis import get_stock_analysis

async def main():
    print("----------------------------------------------------------------")
    print("🔍 Testing get_stock_analysis('GOOG') locally...")
    print(f"   Project: {os.getenv('GCP_PROJECT_ID')}")
    print(f"   Bucket: {os.getenv('GCS_BUCKET_NAME')}")
    print("----------------------------------------------------------------\n")

    try:
        # Call the tool directly
        result_json = await get_stock_analysis("GOOG")
        
        # Check if we got an error response in the JSON
        if '"error":' in result_json:
            print("❌ Tool returned an error:")
            print(result_json)
        else:
            print("✅ Success! Data retrieved.")
            print("   Response Preview (first 500 chars):")
            print("   " + result_json[:500] + "...")
            
    except Exception as e:
        print(f"❌ Python Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
