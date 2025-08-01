# Atlassian MCP Server

MCP server for creating Confluence documentation from code using the official Atlassian Python API.

## Features

- Auto-connects to Confluence (credentials built-in)
- Creates documentation pages with syntax highlighting
- Supports function and file-level documentation
- Manages page content (create, append, replace, remove)
- Lists spaces and finds existing pages

## Setup

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Add to your MCP client configuration:

For Q Developer:
- Name: Atlassian
- Transport: stdio
- Command: py
- Arguments: \path\to\mcp\server\

For Copilot (mcp.json):
```json
{
	"servers": {
		"atlassian-confluence": {
			"type": "stdio",
			"command": "py",
			"args": ["Path\\To\\Atlassian-Confluence-MCP-Server\\atlassian_mcp_server.py"],
			"env": {}
		}
	},
	"inputs": []
}
```


## Usage Examples

### List Available Spaces
**Prompt:** "What Confluence spaces are available?"
- Uses `list_spaces` tool automatically
- Shows all spaces you can create pages in

### Create Simple Documentation Page
**Prompt:** "Create a Confluence page in the AUC space called 'User Authentication System' describing all of our user authentication specifics"
- Uses `create_page` tool
- Creates sections of content to describe the topic at hand
- Creates formatted page with syntax highlighting

### Create Detailed Code Documentation
**Prompt:** "Document this login function in AUC space - it handles user authentication by checking credentials against the database and returns a JWT token"
- Uses `create_code_documentation` tool
- Creates detailed documentation with explanations
- Perfect for specific functions or code blocks

### Find Existing Pages
**Prompt:** "Find pages about 'authentication' in the AUC space"
- Uses `find_page` tool
- Searches page titles for matches

### Add Content to Existing Page
**Prompt:** "Add this new function documentation to page ID 12345"
- Uses `append_to_page` tool
- Preserves existing content

### Update Page Content
**Prompt:** "Replace the old login method with this new implementation on page 12345"
- Uses `replace_content` tool
- Finds and replaces specific content

## Real AI Prompting Examples

Instead of JSON configurations or any complex prompting, just talk naturally:

- "Show me what Confluence spaces I can use"
- "Create docs for this authentication module in the DEV space"
- "Document this calculate_tax function - it takes income and returns tax owed"
- "Add this error handling code to the existing API documentation page"
- "Find any pages about database connections in the TECH space"

## Available Tools

### Core Tools
- `list_spaces` - Show available Confluence spaces
- `create_page` - Create basic documentation page
- `create_code_documentation` - Create detailed code documentation

### Page Management
- `get_pages` - List pages in a space
- `find_page` - Search pages by title
- `get_page_content` - View page content
- `append_to_page` - Add content to existing page
- `replace_content` - Replace specific content
- `remove_content` - Remove specific content

## Configuration

Modify these values in the .py file to your actual credentials:
- `CONFLUENCE_URL`
- `CONFLUENCE_USERNAME` 
- `CONFLUENCE_TOKEN`

Get API tokens from: https://id.atlassian.com/manage-profile/security/api-tokens
