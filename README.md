# Testing Farm MCP Server

A Model Context Protocol (MCP) server for analyzing [Testing Farm](https://testing-farm.io) jobs. This server provides tools to check job status and analyze failures with detailed error investigation.

## Features

- 🔍 **Job Status Checking**: Get current status of Testing Farm jobs
- 🧪 **Intelligent Failure Analysis**: Automatically investigate failed jobs by examining logs and TMT execution details
- 🚀 **Dual Transport Support**: Works with both stdio and SSE transport modes
- 🐳 **Containerized**: Ready-to-use container images with Podman/Docker
- 🔧 **Generic Error Detection**: Finds failure reasons without hardcoded patterns

## Available Tools

### `get_job_status(job_id: str)`
Returns basic status information for a Testing Farm job including state, result, timing, and environment details.

### `analyze_job(job_id: str)`
Provides comprehensive job analysis:
- **Successful jobs**: Brief summary with environment information
- **Failed jobs**: Investigates logs to find exact failure reasons
- **Running jobs**: Current status information

## Transport Modes

This MCP server supports two transport modes:

### 📡 **stdio Transport (Default)**
- Communication via stdin/stdout
- Best for: IDE integrations, CLI tools
- Process lifecycle: Managed by MCP client

### 🌐 **SSE Transport**
- HTTP server with Server-Sent Events
- Best for: Web applications, debugging, multiple clients
- Process lifecycle: Independent server process

## Quick Start

### 1. Setup

```bash
# Clone and setup
git clone <repository-url>
cd testing-farm-mcp

# Build and configure everything
make setup
```

### 2. Configure API Token

Edit `~/.testing-farm-mcp.env` and set your Testing Farm API token:
```bash
TESTING_FARM_API_TOKEN=your_actual_token_here
```

### 3. Run the server

#### stdio Transport (Default)
```bash
make run
```

## Configuration

### Environment Variables

Create `~/.testing-farm-mcp.env` with the following variables:

```bash
# Required: Your Testing Farm API token
TESTING_FARM_API_TOKEN=your_token_here

# Transport configuration
MCP_TRANSPORT=stdio          # or 'sse'
MCP_PORT=8000               # for SSE transport
```

### MCP Client Configuration

#### For stdio Transport

Add to your MCP client configuration (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "TestingFarmMcp-stdio": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "~/.testing-farm-mcp.env",
        "-e",
        "MCP_TRANSPORT=stdio",
        "localhost/testing-farm-mcp:latest"
      ],
      "description": "Testing Farm MCP server using stdio transport(containerized)"
    }
  }
}
```

#### For SSE Transport

```json
{
  "mcpServers": {
    "TestingFarmMcp-sse": {
      "transport": "sse",
      "url": "http://localhost:8000/sse",
      "name": "Testing Farm MCP server",
      "description": "Testing Farm MCP server using SSE transport with port 8000 (containerized)"
    }
}
```

## Usage Examples

### Check Job Status
```bash
# Basic status check
get_job_status("aeebaa46-4983-4c70-a339-f168c8c427c2")
```

### Analyze Jobs
```bash
# Comprehensive analysis
analyze_job("aeebaa46-4983-4c70-a339-f168c8c427c2")

# For successful jobs, you'll get:
# ✅ Job completed successfully
#    State: complete
#    Result: passed
#    Architecture: aarch64
#    OS: CentOS-Stream-9

# For failed jobs, you'll get failure investigation:
# ❌ Job failed
#    State: complete
#    Result: failed
#    📋 Failed Tests: /Clone SIG repo
#    💥 Failure Details:
#    error: pathspec '2943d306' did not match any file(s) known to git
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file and edit with your API token
cp example.env ~/.testing-farm-mcp.env

# Run locally
export $(cat ~/.testing-farm-mcp.env | xargs)
python server.py
```

### Container Development

```bash
# Build container
make build

# Run container (stdio)
make run

# Run container (SSE)
make run-sse

# Clean up
make clean
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make setup` | Complete setup: build, configure Cursor, create env file |
| `make build` | Build container image |
| `make run` | Run MCP server with stdio transport (default) |
| `make clean` | Clean up container image |
| `make cursor-config` | Configure Cursor IDE |

## Transport Mode Comparison

| Feature | stdio | SSE |
|---------|-------|-----|
| **Use Case** | IDE integration, CLI tools | Web apps, debugging, multi-client |
| **Process Model** | Subprocess of MCP client | Independent server process |
| **Network** | None (pipes) | HTTP on configurable port |
| **Clients** | Single | Multiple concurrent |
| **Resource Usage** | Lower | Slightly higher |
| **Setup Complexity** | Simple | Requires port management |

## Troubleshooting

### Common Issues

**"TESTING_FARM_API_TOKEN not set" warning**
- Edit `~/.testing-farm-mcp.env` and add your API token

**"Could not retrieve job data" error**
- Verify your API token is correct
- Check if the job ID exists
- Ensure network connectivity to testing-farm.io

**SSE transport connection failed**
- Check if port 8000 is available: `netstat -tlnp | grep 8000`
- Try a different port by setting `MCP_PORT=8001`

**Container permission issues**
- Ensure your user can run Podman/Docker
- Check if the env file path is accessible: `~/.testing-farm-mcp.env`

## API Token Setup

1. **Get Testing Farm API Token**:
   - Visit [Testing Farm Console](https://console.testing-farm.io)
   - Sign in with your account
   - Navigate to API tokens section
   - Generate a new token

2. **Configure Token**:
   ```bash
   # Create or edit environment file
   echo "TESTING_FARM_API_TOKEN=your_token_here" > ~/.testing-farm-mcp.env
   ```

## Project Structure

```
testing-farm-mcp/
├── server.py              # Main MCP server implementation
├── requirements.txt       # Python dependencies
├── Containerfile         # Container build configuration
├── Makefile              # Build and run commands
├── example.env           # Environment variables template
├── example.mcp.json      # MCP client configuration examples
└── README.md             # This file
```

## Dependencies

- `httpx` - HTTP client for API requests
- `fastmcp` - MCP server framework
- `python-dotenv` - Environment variable loading

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both transport modes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License**

Copyright (c) 2025 Red Hat AI Tools

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

---

**Note**: This MCP server requires a valid Testing Farm API token to function. The server will work without it but with limited functionality.
