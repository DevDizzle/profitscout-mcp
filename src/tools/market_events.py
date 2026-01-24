"""
Tool: Market Events
Get upcoming market events (Earnings, Econ, Dividends, etc).
"""

import json
import logging
from typing import Optional
from datetime import datetime

from data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)

# Initialize BigQuery client
bq_client = BigQueryClient()


async def get_market_events(
    start_date: Optional[str] = None,
    days_forward: int = 7,
    ticker: Optional[str] = None,
    event_type: Optional[str] = None
) -> str:
    """Get upcoming market calendar events.
    
    Finds catalysts like Earnings, Dividends, IPOs, Splits, or broad Economic events.
    Useful for checking "What is happening next week?" or "When are AAPL earnings?".
    
    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to today.
        days_forward: Number of days to look ahead. Defaults to 7.
        ticker: Optional filter by a specific stock ticker (e.g. 'NVDA').
        event_type: Optional filter by 'Earnings', 'Economic', 'Dividend', 'Split', 'IPO'.

    Returns:
        JSON string with list of events.
    """
    try:
        # Defaults handled in client method
        result = await bq_client.get_calendar_events(
            start_date=start_date,
            days_forward=days_forward,
            ticker=ticker,
            event_type=event_type
        )
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_market_events: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)
