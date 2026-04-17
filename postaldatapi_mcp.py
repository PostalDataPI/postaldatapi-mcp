#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 PostalDataPI (Thom Ives)
"""
PostalDataPI MCP Server

Exposes PostalDataPI endpoints as MCP tools so AI agents (Claude, etc.)
can look up, validate, and search postal codes across 240+ countries
with rich metadata: timezone, admin regions, elevation, and coordinates.

Usage:
    # Direct run
    postaldatapi-mcp

    # With Claude Code
    claude mcp add --transport stdio postaldatapi -- postaldatapi-mcp

    # Environment variable for API key
    POSTALDATAPI_KEY=your_key postaldatapi-mcp
"""

import logging
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Logging to stderr only — stdout is reserved for MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("postaldatapi-mcp")

# Configuration
API_BASE = "https://postaldatapi.com/api"
API_KEY = os.environ.get("POSTALDATAPI_KEY", "")

# Initialize MCP server
mcp = FastMCP(
    "postaldatapi",
    instructions="PostalDataPI: Look up, validate, and search postal codes across 240+ countries with rich metadata (timezone, admin regions, elevation, coordinates). Sub-5ms responses.",
)


async def _call_api(endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """Call a PostalDataPI endpoint. Raises on HTTP errors."""
    key = API_KEY or os.environ.get("POSTALDATAPI_KEY", "")
    if not key:
        return {"error": "No API key configured. Set POSTALDATAPI_KEY environment variable."}

    body["apiKey"] = key

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{API_BASE}/{endpoint}",
            json=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PostalDataPI-MCP/0.1.0",
            },
        )
        return resp.json()


def _format_error(data: dict[str, Any]) -> str | None:
    """Return formatted error string if response contains an error."""
    if "error" in data:
        msg = data["error"]
        if "currentBalance" in data:
            msg += f" (balance: {data['currentBalance']})"
        return f"Error: {msg}"
    return None


@mcp.tool()
async def lookup_postal_code(postal_code: str, country: str = "US") -> str:
    """Look up a postal code and get city, state, and region information.

    Works for ZIP codes (US), postcodes (UK), PLZ (Germany), and postal codes
    in 240+ countries. Use this when someone asks about a postal code, wants to
    know what city a ZIP code belongs to, or needs address information.

    Args:
        postal_code: The postal code to look up (e.g., "90210", "SW1A", "10115", "100-0001")
        country: ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "DE", "JP"). Defaults to "US".

    Returns:
        City, state/region, and abbreviation for the postal code.
    """
    data = await _call_api("lookup", {"zipcode": postal_code, "country": country})

    err = _format_error(data)
    if err:
        return err

    city = data.get("city", "Unknown")
    state = data.get("state", "")
    st = data.get("ST", "")

    parts = [f"City: {city}"]
    if state:
        parts.append(f"State/Region: {state}")
    if st:
        parts.append(f"Abbreviation: {st}")
    parts.append(f"Country: {country}")

    return "\n".join(parts)


@mcp.tool()
async def validate_postal_code(postal_code: str, country: str = "US") -> str:
    """Check whether a postal code exists in a given country.

    Use this when someone wants to verify if a postal code is valid before
    processing an order, form, or address.

    Args:
        postal_code: The postal code to validate
        country: ISO 3166-1 alpha-2 country code. Defaults to "US".

    Returns:
        Whether the postal code is valid or invalid.
    """
    data = await _call_api("validate", {"zipcode": postal_code, "country": country})

    err = _format_error(data)
    if err:
        return err

    is_valid = data.get("valid", False)
    return f"Postal code {postal_code} ({country}): {'VALID' if is_valid else 'INVALID'}"


@mcp.tool()
async def search_by_city(city: str, state: str = "", country: str = "US") -> str:
    """Find all postal codes for a given city.

    Use this when someone has a city name and needs the postal codes that serve
    it. For US cities, provide the state name or 2-letter abbreviation.

    Args:
        city: City name (e.g., "Beverly Hills", "Berlin", "Tokyo")
        state: State or region name/abbreviation. Required for US cities (e.g., "CA" or "California").
        country: ISO 3166-1 alpha-2 country code. Defaults to "US".

    Returns:
        List of postal codes for the city.
    """
    body: dict[str, Any] = {"city": city, "country": country}

    # For US, determine if state is an abbreviation or full name
    if state:
        if len(state) == 2 and state.isalpha():
            body["ST"] = state.upper()
        else:
            body["state"] = state

    data = await _call_api("city", body)

    err = _format_error(data)
    if err:
        return err

    zipcodes = data.get("zipcodes", [])
    if not zipcodes:
        return f"No postal codes found for {city}, {state} ({country})"

    header = f"Postal codes for {city}"
    if state:
        header += f", {state}"
    header += f" ({country}): {len(zipcodes)} found"

    if len(zipcodes) <= 20:
        return f"{header}\n" + ", ".join(zipcodes)
    else:
        shown = ", ".join(zipcodes[:20])
        return f"{header}\n{shown}\n... and {len(zipcodes) - 20} more"


@mcp.tool()
async def get_postal_code_metadata(postal_code: str, country: str = "US") -> str:
    """Get full metadata for a postal code including coordinates.

    Returns latitude, longitude, county/municipality, and all available
    country-specific fields. Use this when someone needs geographic coordinates,
    timezone, or detailed location data for a postal code.

    Args:
        postal_code: The postal code to look up
        country: ISO 3166-1 alpha-2 country code. Defaults to "US".

    Returns:
        Full metadata including coordinates, region, and country-specific fields.
    """
    data = await _call_api("metazip", {"zipcode": postal_code, "country": country})

    err = _format_error(data)
    if err:
        return err

    meta = data.get("meta", {})
    if not meta:
        return f"No metadata found for {postal_code} ({country})"

    parts = []
    # Standard fields
    field_labels = {
        "postalCode": "Postal Code",
        "zipcode": "ZIP Code",
        "placeName": "Place",
        "city": "City",
        "country": "Country",
        "adminLevel1": "State/Region",
        "adminLevel1Code": "Region Code",
        "adminLevel2": "County/Municipality",
        "state": "State",
        "stateAbbrev": "State Abbreviation",
        "county": "County",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "timezone": "Timezone",
        "province": "Province",
        "prefecture": "Prefecture",
    }

    for key, label in field_labels.items():
        if key in meta and meta[key] is not None:
            parts.append(f"{label}: {meta[key]}")

    # Any extra fields not in the standard list
    for key, value in meta.items():
        if key not in field_labels and value is not None:
            parts.append(f"{key}: {value}")

    return "\n".join(parts) if parts else f"No metadata available for {postal_code}"


def main():
    """Entry point for the MCP server."""
    if not API_KEY and not os.environ.get("POSTALDATAPI_KEY"):
        logger.warning(
            "POSTALDATAPI_KEY not set. Tools will return errors until an API key is configured."
        )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
