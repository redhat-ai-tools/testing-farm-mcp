
_default: run

SHELL := /bin/bash
SCRIPT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
IMG := localhost/testing-farm-mcp:latest
ENV_FILE := $(HOME)/.testing-farm-mcp.env
DEFAULT_PORT := 8000

.PHONY: build run run-sse clean cursor-config setup

# Build the container image
build:
	@echo "🛠️  Building Testing Farm MCP Server image..."
	podman build -t $(IMG) .
	@echo "✅ Image built successfully: $(IMG)"

# Run with stdio transport (default)
run:
	@echo "🚀 Running Testing Farm MCP Server with stdio transport..."
	@echo "   Use Ctrl-D to quit nicely"
	podman run -i --tty --rm --env-file $(ENV_FILE) \
		-e MCP_TRANSPORT=stdio \
		$(IMG)

# Run with SSE transport
run-sse:
	@echo "🚀 Running Testing Farm MCP Server with SSE transport on port $(DEFAULT_PORT)..."
	@echo "   Server will be available at http://localhost:$(DEFAULT_PORT)"
	@echo "   Use Ctrl-C to stop"
	podman run -i --rm \
		--network host \
		-p $(DEFAULT_PORT):$(DEFAULT_PORT) \
		--env-file $(ENV_FILE) \
		-e MCP_TRANSPORT=sse \
		-e MCP_PORT=$(DEFAULT_PORT) \
		$(IMG)

# Clean up container image
clean:
	@echo "🧹 Cleaning up..."
	-podman rmi $(IMG)
	@echo "✅ Cleanup complete"

# Configure Cursor with MCP server settings
MCP_JSON=$(HOME)/.cursor/mcp.json
cursor-config:
	@echo "🛠️  Configuring Cursor MCP settings..."
	@echo "   Updating $(MCP_JSON)"
	@yq -ojson '. *= load("example.mcp.json")' -i $(MCP_JSON)
	@yq -ojson $(MCP_JSON)
	@echo "✅ Cursor configuration updated"

# Copy the example .env file only if it doesn't exist already
$(ENV_FILE):
	@cp example.env $@
	@echo "🛠️  Environment file created: $@"
	@echo "   ⚠️  Please edit this file to add your Testing Farm API token"
	@echo "   📝 Set TESTING_FARM_API_TOKEN to your actual token"

# Complete setup: build, configure, and create env file
setup: build cursor-config $(ENV_FILE)
	@echo ""
	@echo "🎉 Setup complete! Next steps:"
	@echo ""
	@echo "1. Edit $(ENV_FILE) and set your Testing Farm API token"
	@echo "2. Choose a run mode:"
	@echo "   • make run      # stdio transport (default)"
	@echo "   • make run-sse  # SSE transport"
	@echo ""