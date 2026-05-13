# OpenCode Configuration Guide

## Overview
This document explains how to maintain and share OpenCode configurations across different environments while keeping sensitive information secure.

## Safe to Share (Tracked in Git)
These files contain no sensitive information and can be safely committed:

- `.opencode/agents/` - All agent definition files
- `.opencode/skills/` - All skill definition files
- `.opencode/roles_agent.json` - Role definitions
- `.opencode/package.json` - Dependencies (no secrets)
- `.opencode/opencode.json.template` - Configuration template with placeholders

## Requires Environment-Specific Values (NOT Tracked in Git)
These files contain sensitive information and should never be committed:

- `.opencode/opencode.json` - Contains API keys and local paths
- `.opencode/opencode.json.backup` - Backup of the above

## Environment Variables Needed
To use the template, set these environment variables:

- `SUPERMEMORY_API_KEY` - Your SuperMemory API key
- `TAVILY_API_KEY` - Your Tavily API key
- `BRAVE_API_KEY` - Your Brave Search API key
- `PROJECT_PATH` - Absolute path to your project (default: `/home/ubuntu/projects/OrganBriefOptimization`)

## Usage Instructions

### 1. Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Copy template and fill in values
cp .opencode/opencode.json.template .opencode/opencode.json
# Edit .opencode/opencode.json to replace placeholders with actual values
```

### 2. Development Workflow
```bash
# Make changes to configuration
# Update .opencode/opencode.json.template if changes should be shared
# Never commit .opencode/opencode.json

# Share improvements:
git add .opencode/opencode.json.template
git add .opencode/agents/   # If you modified agent definitions
git add .opencode/skills/   # If you modified skills
git commit -m "Update shared OpenCode configuration"
git push
```

### 3. Deploying to New Environment
```bash
# After cloning/pulling:
cp .opencode/opencode.json.template .opencode/opencode.json
# Edit .opencode/opencode.json with local values
# Or use a secrets management tool to inject values
```

## Security Notes
- Never commit `.opencode/opencode.json` or `.opencode/opencode.json.backup`
- API keys in the template are clearly marked with `{{PLACEHOLDER}}` syntax
- Local paths (like `/home/ubuntu/...`) should be replaced with appropriate values for each environment
- Consider using a secrets manager or .env file for production deployments