# app/fx_client.py
# --------------------
# Implements a client for the external FX service provided by Ripple.
# It calls the /twirp/payments.v1.FXService/GetQuote endpoint with retries
# and returns the FX rate plus a latency measurement.

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Tuple

import httpx

# HTTP client for the FX service. 
# Attributes: base_url: Base URL for the FX service (e.g., http://localhost:4000). timeout_seconds: Per-request timeout in seconds. max_retries: Number of times to retry on failure.
@dataclass
class FXClient:
    base_url: str
    timeout_seconds: float = 3.0
    max_retries: int = 3

    # Fetch an FX quote for a currency pair.
    async def get_quote(
        self, source_currency: str, dest_currency: str
    ) -> Tuple[float, int]:
        """
        Returns (rate, latency_ms). Raises an exception on overall failure.
        """
        if not source_currency or not dest_currency:
            raise ValueError("source_currency and dest_currency are required")

        url = f"{self.base_url}/twirp/payments.v1.FXService/GetQuote"
        payload = {
            "source_currency": source_currency,
            "target_currency": dest_currency,
        }

        last_exc: Exception | None = None
        latency_ms = 0

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries):
                try:
                    start = httpx.Timeout(0)
                    # we'll track latency ourselves with monotonic
                    import time

                    t0 = time.monotonic()
                    resp = await client.post(url, json=payload)
                    latency_ms = int((time.monotonic() - t0) * 1000)

                    if resp.status_code != 200:
                        last_exc = RuntimeError(
                            f"FX service returned status {resp.status_code}"
                        )
                    else:
                        data = resp.json()
                        rate = float(data.get("exchange_rate", 0.0))
                        if rate <= 0:
                            last_exc = RuntimeError(
                                f"Invalid exchange rate from FX: {rate}"
                            )
                        else:
                            # success
                            return rate, latency_ms
                except Exception as e:  # network or decode error
                    last_exc = e

                # backoff between retries, except after last
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.2 * (attempt + 1))

        assert last_exc is not None
        raise last_exc
