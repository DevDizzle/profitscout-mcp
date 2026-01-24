"""
Tool: Market Structure (Options Flow)
Analyzes options chain structure to find support/resistance walls, sentiment, and specific contract Greeks.
"""

import json
import logging
from typing import Optional

from data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)

# Initialize BigQuery client
bq_client = BigQueryClient()


async def analyze_market_structure(
    ticker: str,
    as_of: str = "latest",
    sort_by: Optional[str] = None,
    expiration_date: Optional[str] = None,
    option_type: Optional[str] = None,
    limit: int = 20
) -> str:
    """Analyze options market structure or find specific contracts.
    
    **Modes:**
    1. **Structure Analysis (Default):** Returns Vol/OI Walls (Support/Resistance) and Put/Call Ratios.
       - Use this to validate trade levels and sentiment.
       - Leave `sort_by` empty.
    
    2. **Contract Scanner (Detail View):** Returns specific contracts with Greeks (Gamma, Delta).
       - Use this to find "High Gamma" options or specific strikes.
       - Set `sort_by` to "gamma", "delta", "volume", "oi", or "iv".

    Args:
        ticker: Stock ticker symbol (e.g., "NVDA").
        as_of: Date (YYYY-MM-DD) or "latest".
        sort_by: Metric to sort individual contracts by (e.g., "gamma", "delta").
                 If provided, returns specific contracts instead of structure summary.
        expiration_date: Filter by expiration (YYYY-MM-DD).
        option_type: Filter by "CALL" or "PUT".
        limit: Number of contracts to return (for Scanner mode).

    Returns:
        JSON string with market structure or contract details.
    """
    try:
        if not ticker:
            return json.dumps({"error": "Ticker is required"})

        if sort_by:
            # Detail View (Scanner)
            result = await bq_client.get_option_contracts(
                ticker=ticker,
                sort_by=sort_by,
                limit=limit,
                option_type=option_type,
                expiration_date=expiration_date,
                as_of=as_of
            )
        else:
            # Aggregate View (Structure)
            # Note: get_market_structure currently aggregates ALL dates unless we update it
            # For now, it provides the "Big Picture" walls.
            result = await bq_client.get_market_structure(ticker, as_of)

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in analyze_market_structure for {ticker}: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)
