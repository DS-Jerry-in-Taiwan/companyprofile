#!/bin/bash
# Script to render OpenCode configuration from template using environment variables

set -euo pipefail

TEMPLATE_FILE=".opencode/opencode.json.template"
OUTPUT_FILE=".opencode/opencode.json"

# Check if template exists
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "Error: Template file $TEMPLATE_FILE not found"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Render template by replacing placeholders with environment variables
# Using sed to substitute variables
sed \
    -e "s|{{SUPERMEMORY_API_KEY}}|${SUPERMEMORY_API_KEY:-}|g" \
    -e "s|{{TAVILY_API_KEY}}|${TAVILY_API_KEY:-}|g" \
    -e "s|{{BRAVE_API_KEY}}|${BRAVE_API_KEY:-}|g" \
    -e "s|{{PROJECT_PATH}}|${PROJECT_PATH:-/home/ubuntu/projects/OrganBriefOptimization}|g" \
    "$TEMPLATE_FILE" > "$OUTPUT_FILE"

# Check if any placeholders remain (indicating missing variables)
if grep -q "{{.*}}" "$OUTPUT_FILE"; then
    echo "Warning: Some placeholders were not replaced in $OUTPUT_FILE"
    echo "This usually means some environment variables are not set."
    grep -o "{{.*}}" "$OUTPUT_FILE" | sort -u
fi

echo "Configuration rendered to $OUTPUT_FILE"
echo "Please verify the contents before use."

# Set restrictive permissions on the output file (since it contains secrets)
chmod 600 "$OUTPUT_FILE"