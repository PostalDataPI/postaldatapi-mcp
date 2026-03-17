# PostalDataPI MCP Server

MCP (Model Context Protocol) server for [PostalDataPI](https://postaldatapi.com) — lets AI agents look up, validate, and search postal codes across 70+ countries.

## Tools

| Tool | Description |
|------|-------------|
| `lookup_postal_code` | Get city and state for a postal code (US ZIP, UK postcode, German PLZ, etc.) |
| `validate_postal_code` | Check if a postal code exists in a country |
| `search_by_city` | Find all postal codes for a city |
| `get_postal_code_metadata` | Full metadata: coordinates, county, timezone, and more |

## Setup

### 1. Get an API Key

Sign up at [postaldatapi.com/register](https://postaldatapi.com/register) — 1,000 free queries, no credit card required.

### 2. Install

```bash
pip install postaldatapi-mcp
```

### 3. Configure with Claude Code

```bash
claude mcp add --transport stdio postaldatapi -- \
  env POSTALDATAPI_KEY=your_api_key_here postaldatapi-mcp
```

### 4. Configure with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "postaldatapi": {
      "command": "postaldatapi-mcp",
      "env": {
        "POSTALDATAPI_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Usage

Once configured, ask Claude naturally:

- "What city is ZIP code 90210?"
- "Look up UK postcode SW1A"
- "Is 10115 a valid German postal code?"
- "What are the postal codes for Beverly Hills, CA?"
- "Get the coordinates for postal code 100-0001 in Japan"

Claude will automatically use the PostalDataPI tools to answer.

## Supported Countries

70+ countries including US, UK, Canada, Germany, France, Japan, Australia, and more. See the full list at [postaldatapi.com/countries](https://postaldatapi.com/countries).

## Links

- [PostalDataPI](https://postaldatapi.com)
- [API Reference](https://postaldatapi.com/reference)
- [Documentation](https://docs.postaldatapi.com)
- [Python SDK](https://pypi.org/project/postaldatapi/)
- [Node.js SDK](https://www.npmjs.com/package/postaldatapi)
