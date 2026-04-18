# MCP Integration Skill

## Pattern: Local Binary Anchoring
When configuring MCP servers in environments with non-standard paths (e.g., `nvm` sessions, Homebrew on dynamic prefixes), use absolute paths discovered via symlink resolution.

### System Audit Findings
- **nvm Path**: `/Users/hamednejat/.nvm/versions/node/v24.14.0/bin/npx`
- **Global Symlink**: `/usr/local/bin/npx`

## Pattern: LM Studio Bridge
To integrate LM Studio as an MCP tool source:
- **Command**: `npx -y lm-studio-mcp-server`
- **Required Env**: `LM_STUDIO_BASE_URL` (usually `http://localhost:1234/v1`)

## references
- mcp_config.json:L21-L30
- mcp_lm_studio_resolution.gamma
