"""
Tool: get_financial_analysis
Get financial health and statement analysis for a ticker
"""

import json
import logging

from data.gcs_client import GCSClient

logger = logging.getLogger(__name__)

# Initialize GCS client
gcs_client = GCSClient()


async def get_financial_analysis(ticker: str, as_of: str = "latest") -> str:
    """Get financial health analysis.

    Returns deep-dive analysis of financial statements including
    Revenue, Net Income, Cash Flow, Debt, and Margins.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
        as_of: Date for historical data in YYYY-MM-DD format, or "latest" (default: "latest")

    Returns:
        JSON string with financial analysis.
    """
    try:
        # Validate ticker
        if not ticker or not ticker.strip():
            return json.dumps({"error": "Ticker is required"}, indent=2)

        # Query GCS
        result = await gcs_client.get_financial_analysis(
            ticker=ticker.strip().upper(),
            as_of=as_of,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in get_financial_analysis for {ticker}: {e}", exc_info=True)
        return json.dumps(
            {
                "error": f"Failed to fetch financial analysis for {ticker}",
                "details": str(e),
            },
            indent=2,
        )
