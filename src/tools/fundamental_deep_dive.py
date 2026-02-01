"""
Tool: Fundamental Deep Dive
Retrieves deep fundamental context: Macro Thesis, MD&A, and Transcript Analysis.
"""

import json
import logging

from data.gcs_client import GCSClient

logger = logging.getLogger(__name__)

# Initialize GCS client
gcs_client = GCSClient()


async def get_macro_thesis(as_of: str = "latest") -> str:
    """Get the current macro-economic thesis to understand market conditions.

    Provides top-down context on interest rates, inflation, sector rotation,
    and geopolitical risks. Use this to validate if a trade setup aligns
    with the broader market environment.

    Args:
        as_of: Date for historical thesis (YYYY-MM-DD) or "latest".

    Returns:
        JSON string with the macro thesis.
    """
    try:
        result = await gcs_client.get_macro_thesis(as_of)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_macro_thesis: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)


async def get_mda_analysis(ticker: str, as_of: str = "latest") -> str:
    """Get analysis of the Management Discussion & Analysis (MD&A) section.

    Extracts insights from 10-K/10-Q filings, highlighting risks,
    future outlooks, and operational changes that raw numbers might miss.

    Args:
        ticker: Stock ticker symbol.
        as_of: Date (YYYY-MM-DD) or "latest".

    Returns:
        JSON string with MD&A analysis.
    """
    try:
        if not ticker:
            return json.dumps({"error": "Ticker is required"})

        result = await gcs_client.get_mda_analysis(ticker, as_of)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_mda_analysis for {ticker}: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)


async def get_transcript_analysis(ticker: str, as_of: str = "latest") -> str:
    """Get analysis of recent Earnings Call Transcripts.

    Analyzes executive tone, Q&A confidence, and forward guidance
    to detect if management is confident or defensive.

    Args:
        ticker: Stock ticker symbol.
        as_of: Date (YYYY-MM-DD) or "latest".

    Returns:
        JSON string with transcript analysis.
    """
    try:
        if not ticker:
            return json.dumps({"error": "Ticker is required"})

        result = await gcs_client.get_transcript_analysis(ticker, as_of)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_transcript_analysis for {ticker}: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)
