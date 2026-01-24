"""
BigQuery client for accessing ProfitScout data
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Client for querying ProfitScout data from BigQuery."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET")
        self.client = bigquery.Client(project=self.project_id)
        logger.info(f"Initialized BigQuery client for project: {self.project_id}")

    def _get_table_id(self, table_name: str) -> str:
        """Get fully qualified table ID."""
        # Allow full table paths if provided, otherwise construct from dataset
        if "." in table_name:
            return table_name
        return f"{self.project_id}.{self.dataset}.{table_name}"

    def _get_latest_run_date(self, table_name: str, date_col: str = "run_date") -> str:
        """Get the most recent run_date from a table."""
        table_id = self._get_table_id(table_name)
        query = f"SELECT MAX({date_col}) as latest_date FROM `{table_id}`"
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            row = next(results)
            latest_date = row.latest_date
            
            if latest_date:
                # Handle DATE objects or Strings
                if hasattr(latest_date, 'strftime'):
                    return latest_date.strftime("%Y-%m-%d")
                return str(latest_date)
            else:
                # Fallback to yesterday if no data
                return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"Error fetching latest run date: {e}")
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    async def get_winners_dashboard(
        self,
        limit: int = 10,
        option_type: Optional[str] = None,
        min_quality: Optional[str] = None,
        as_of: str = "latest",
    ) -> Dict[str, Any]:
        """Get top-ranked options signals from winners_dashboard table."""
        table_name = os.getenv("WINNERS_DASHBOARD_TABLE", "winners_dashboard")
        table_id = self._get_table_id(table_name)
        
        # Get the effective run date
        if as_of == "latest":
            run_date = self._get_latest_run_date(table_name, date_col="run_date")
        else:
            run_date = as_of

        # Build query
        query = f"""
        SELECT *
        FROM `{table_id}`
        WHERE run_date = @run_date
        """
        
        params = [bigquery.ScalarQueryParameter("run_date", "STRING", run_date)]
        
        # Add filters
        if option_type:
            query += " AND option_type = @option_type"
            params.append(bigquery.ScalarQueryParameter("option_type", "STRING", option_type))
        
        if min_quality:
            quality_order = {"High": 3, "Medium": 2, "Low": 1}
            min_quality_value = quality_order.get(min_quality, 0)
            query += f"""
            AND CASE setup_quality_signal
                WHEN 'High' THEN 3
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 1
                ELSE 0
            END >= {min_quality_value}
            """
        
        # Add ordering and limit
        query += """
        ORDER BY
            CASE setup_quality_signal WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 ELSE 0 END DESC,
            CASE volatility_comparison_signal WHEN 'Favorable' THEN 1 ELSE 0 END DESC
        LIMIT @limit
        """
        params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))
        
        # Execute query
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            signals = []
            for row in results:
                signal = dict(row.items())
                # Convert date/datetime objects to strings
                for key, value in signal.items():
                    if isinstance(value, (datetime,)):
                        signal[key] = value.isoformat()
                signals.append(signal)
            
            return {
                "as_of": run_date,
                "count": len(signals),
                "signals": signals,
            }
        except Exception as e:
            logger.error(f"Error querying winners dashboard: {e}")
            raise

    async def get_market_structure(
        self, ticker: str, as_of: str = "latest"
    ) -> Dict[str, Any]:
        """Get market structure (Option Flow & Positioning) for a ticker.
        
        Queries the options_chains table to aggregate Volume, Open Interest,
        and calculate Put/Call ratios and major walls (Support/Resistance).
        """
        table_name = os.getenv("OPTION_CHAINS_TABLE", "options_chain")
        table_id = self._get_table_id(table_name)
        
        # Get the effective run date (using fetch_date)
        if as_of == "latest":
            run_date = self._get_latest_run_date(table_name, date_col="fetch_date")
        else:
            run_date = as_of

        # Query for high-level aggregates
        # We assume the table has columns: ticker, run_date, expiration_date, strike_price, option_type ('call'/'put'), volume, open_interest, implied_volatility
        query = f"""
        SELECT 
            option_type,
            SUM(volume) as total_volume,
            SUM(open_interest) as total_oi,
            AVG(implied_volatility) as avg_iv
        FROM `{table_id}`
        WHERE fetch_date = CAST(@run_date AS DATE) AND ticker = @ticker
        GROUP BY option_type
        """
        
        params = [
            bigquery.ScalarQueryParameter("run_date", "STRING", run_date),
            bigquery.ScalarQueryParameter("ticker", "STRING", ticker.upper()),
        ]
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        
        try:
            # 1. Get Aggregates (PCR, Total Vol)
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            stats = {"call": {"vol": 0, "oi": 0}, "put": {"vol": 0, "oi": 0}}
            for row in results:
                otype = row.option_type.lower()
                if otype in stats:
                    stats[otype]["vol"] = row.total_volume or 0
                    stats[otype]["oi"] = row.total_oi or 0
                    stats[otype]["avg_iv"] = row.avg_iv or 0
            
            total_vol = stats["call"]["vol"] + stats["put"]["vol"]
            total_oi = stats["call"]["oi"] + stats["put"]["oi"]
            
            if total_vol == 0 and total_oi == 0:
                 return {
                    "ticker": ticker.upper(),
                    "as_of": run_date,
                    "message": "No options data found."
                }

            pcr_vol = stats["put"]["vol"] / stats["call"]["vol"] if stats["call"]["vol"] > 0 else 0
            pcr_oi = stats["put"]["oi"] / stats["call"]["oi"] if stats["call"]["oi"] > 0 else 0
            
            # 2. Get "Walls" (Strikes with highest OI)
            walls_query = f"""
            SELECT strike, option_type, open_interest
            FROM `{table_id}`
            WHERE fetch_date = CAST(@run_date AS DATE) AND ticker = @ticker
            ORDER BY open_interest DESC
            LIMIT 10
            """
            walls_job = self.client.query(walls_query, job_config=job_config)
            walls = [{"strike": r.strike, "type": r.option_type, "oi": r.open_interest} for r in walls_job.result()]
            
            # 3. Get "Heat" (Strikes with highest Volume)
            heat_query = f"""
            SELECT strike, option_type, volume
            FROM `{table_id}`
            WHERE fetch_date = CAST(@run_date AS DATE) AND ticker = @ticker
            ORDER BY volume DESC
            LIMIT 10
            """
            heat_job = self.client.query(heat_query, job_config=job_config)
            heat = [{"strike": r.strike, "type": r.option_type, "vol": r.volume} for r in heat_job.result()]
            
            return {
                "ticker": ticker.upper(),
                "as_of": run_date,
                "summary": {
                    "total_volume": total_vol,
                    "total_open_interest": total_oi,
                    "put_call_ratio_volume": round(pcr_vol, 2),
                    "put_call_ratio_oi": round(pcr_oi, 2),
                },
                "structure": {
                    "dominant_walls": walls, # Where price might pin/reject
                    "active_heat": heat,     # Where the bets are today
                }
            }
            
        except Exception as e:
            logger.error(f"Error querying market structure for {ticker}: {e}")
            raise

    async def get_calendar_events(
        self,
        start_date: Optional[str] = None,
        days_forward: int = 7,
        ticker: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get upcoming market calendar events."""
        table_name = os.getenv("CALENDAR_EVENTS_TABLE", "calendar_events")
        table_id = self._get_table_id(table_name)
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
            
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=days_forward)
            end_date = end_dt.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid start_date format: {start_date}. Must be YYYY-MM-DD")

        query = f"""
        SELECT
            event_date,
            entity,
            event_type,
            event_name
        FROM `{table_id}`
        WHERE event_date BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE)
        """
        
        params = [
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
            bigquery.ScalarQueryParameter("end_date", "STRING", end_date),
        ]
        
        if ticker:
            query += " AND entity = @ticker"
            params.append(bigquery.ScalarQueryParameter("ticker", "STRING", ticker.upper()))
            
        if event_type:
            query += " AND event_type = @event_type"
            params.append(bigquery.ScalarQueryParameter("event_type", "STRING", event_type))
            
        query += " ORDER BY event_date ASC LIMIT 50"
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            events = []
            for row in results:
                event = dict(row.items())
                # Serialize dates
                for key, value in event.items():
                    if hasattr(value, 'isoformat'):
                        event[key] = value.isoformat()
                events.append(event)
                
            return {
                "start_date": start_date,
                "end_date": end_date,
                "count": len(events),
                "events": events
            }
        except Exception as e:
            logger.error(f"Error querying calendar events: {e}")
            raise

    async def execute_price_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute a custom SQL query against the price_data table.
        
        Args:
            sql_query: The SQL query string.
            
        Returns:
            Dictionary containing the query results.
        """
        # Security check: Ensure we are mostly querying the price_data table
        # This is a weak check but better than nothing.
        # ideally we should parse the query or restrict the FROM clause.
        
        try:
            # We enforce using the standard client
            query_job = self.client.query(sql_query)
            results = query_job.result()
            
            rows = []
            for row in results:
                # Convert row to dict
                row_dict = dict(row.items())
                # Serialize dates
                for key, value in row_dict.items():
                    if isinstance(value, (datetime,)):
                        row_dict[key] = value.isoformat()
                    elif hasattr(value, 'isoformat'): # Handle date objects
                         row_dict[key] = value.isoformat()
                rows.append(row_dict)
                
            return {
                "count": len(rows),
                "results": rows
            }
        except Exception as e:
            logger.error(f"Error executing price query: {e}")
            return {
                "error": "Failed to execute query",
                "details": str(e)
            }

    async def get_option_contracts(
        self,
        ticker: str,
        sort_by: str = "open_interest",
        limit: int = 20,
        option_type: Optional[str] = None,
        expiration_date: Optional[str] = None,
        as_of: str = "latest"
    ) -> Dict[str, Any]:
        """Get specific option contracts with Greeks."""
        table_name = os.getenv("OPTION_CHAINS_TABLE", "options_chain")
        table_id = self._get_table_id(table_name)
        
        if as_of == "latest":
            run_date = self._get_latest_run_date(table_name, date_col="fetch_date")
        else:
            run_date = as_of

        # Map friendly sort names to columns
        sort_map = {
            "gamma": "gamma",
            "delta": "ABS(delta)", # Absolute delta for magnitude
            "volume": "volume",
            "open_interest": "open_interest",
            "oi": "open_interest",
            "implied_volatility": "implied_volatility",
            "iv": "implied_volatility"
        }
        order_col = sort_map.get(sort_by.lower(), "open_interest")

        query = f"""
        SELECT 
            ticker,
            expiration_date,
            strike,
            option_type,
            last_price,
            volume,
            open_interest,
            implied_volatility,
            delta,
            gamma,
            theta,
            vega,
            dte
        FROM `{table_id}`
        WHERE fetch_date = CAST(@run_date AS DATE) AND ticker = @ticker
        """
        
        params = [
            bigquery.ScalarQueryParameter("run_date", "STRING", run_date),
            bigquery.ScalarQueryParameter("ticker", "STRING", ticker.upper()),
        ]

        if option_type:
            query += " AND option_type = @option_type"
            params.append(bigquery.ScalarQueryParameter("option_type", "STRING", option_type))

        if expiration_date:
            query += " AND expiration_date = CAST(@expiration_date AS DATE)"
            params.append(bigquery.ScalarQueryParameter("expiration_date", "STRING", expiration_date))
        
        # Filter for meaningful liquidity if not sorting by it
        if "volume" not in sort_by and "open_interest" not in sort_by:
             query += " AND (volume > 0 OR open_interest > 0)"

        query += f" ORDER BY {order_col} DESC LIMIT @limit"
        params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))

        job_config = bigquery.QueryJobConfig(query_parameters=params)

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            contracts = []
            for row in results:
                c = dict(row.items())
                for key, value in c.items():
                    if hasattr(value, 'isoformat'):
                        c[key] = value.isoformat()
                contracts.append(c)
                
            return {
                "ticker": ticker.upper(),
                "as_of": run_date,
                "sort_by": sort_by,
                "count": len(contracts),
                "contracts": contracts
            }
        except Exception as e:
            logger.error(f"Error querying option contracts: {e}")
            raise