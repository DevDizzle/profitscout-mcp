"""
Tool: get_business_summary
Get business summary and qualitative profile for a ticker
"""

import json
import logging

from data.gcs_client import GCSClient

logger = logging.getLogger(__name__)

# Initialize GCS client
gcs_client = GCSClient()


async def get_business_summary(ticker: str, as_of: str = "latest") -> str:
    """Get business summary and corporate profile.

    Returns the business overview, including subsidiaries, hubs,
    strategic positioning, and other qualitative data.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
        as_of: Date for historical data in YYYY-MM-DD format, or "latest" (default: "latest")

    Returns:
        JSON string with business summary.
    """
    try:
        # Validate ticker
        if not ticker or not ticker.strip():
            return json.dumps({"error": "Ticker is required"}, indent=2)

        # Query GCS
        result = await gcs_client.get_business_summary(
            ticker=ticker.strip().upper(),
            as_of=as_of,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in get_business_summary for {ticker}: {e}", exc_info=True)
        return json.dumps(
            {
                "error": f"Failed to fetch business summary for {ticker}",
                "details": str(e),
            },
            indent=2,
        )
