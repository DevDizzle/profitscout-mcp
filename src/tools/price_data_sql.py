"""
Tool: run_price_query
Run custom SQL queries against the price_data table
"""

import json
import logging

from data.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)

# Initialize BigQuery client
bq_client = BigQueryClient()


async def run_price_query(query: str) -> str:
    """Run a custom SQL query against the price_data table.

    Allows for flexible querying of historical price and volume data.
    The table contains: ticker, date, open, high, low, adj_close, volume.
    
    Example Queries:
    1. "SELECT * FROM `profitscout-lx6bb.profit_scout.price_data` WHERE ticker = 'AAPL' ORDER BY date DESC LIMIT 5"
    2. "SELECT ticker, date, volume FROM `profitscout-lx6bb.profit_scout.price_data` WHERE volume > 10000000 LIMIT 10"

    Args:
        query: Valid SQL query string.

    Returns:
        JSON string with query results.
    """
    try:
        # Basic validation
        if not query or not query.strip():
            return json.dumps({"error": "Query is required"}, indent=2)

        # Execute Query
        result = await bq_client.execute_price_query(query)

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error in run_price_query: {e}", exc_info=True)
        return json.dumps(
            {
                "error": "Failed to execute price query",
                "details": str(e),
            },
            indent=2,
        )
