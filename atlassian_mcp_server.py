#!/usr/bin/env python3
import asyncio
from typing import Any
from atlassian import Confluence
import urllib3
import logging

# Set up logging so we can see where errors are
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Turn off SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("atlassian-mcp")

# Atlassian configuration, REPLACE THIS WITH YOUR INFORMATION or set external environment variables
CONFLUENCE_URL = "CONFLUENCE_URL"
CONFLUENCE_USERNAME = "CONFLUENCE_USERNAME"
CONFLUENCE_TOKEN = "CONFLUENCE_TOKEN"

# Connect to Confluence right away so it's ready to go
try:
    confluence = Confluence(
        url=CONFLUENCE_URL,
        username=CONFLUENCE_USERNAME,
        password=CONFLUENCE_TOKEN,
        verify_ssl=False
    )
    logger.info("Connected to Confluence successfully")
except Exception as e:
    logger.error(f"Couldn't connect to Confluence: {e}")
    confluence = None

def create_simple_content(title: str, content: str = "", code: str = "", file_path: str = "") -> str:
    """Makes a nice Confluence page from code - analyzes what's in there and formats it nicely"""
    if content:
        return content
    
    if code:
        lines = code.split('\n')
        functions = [line.strip() for line in lines if line.strip().startswith('def ')]
        classes = [line.strip() for line in lines if line.strip().startswith('class ')]
        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
        
        page_content = f"<h1>{title}</h1>"
        
        if file_path:
            page_content += f"<p><strong>File:</strong> <code>{file_path}</code></p>"
        
        if imports:
            page_content += "<h2>Dependencies</h2><ul>"
            for imp in imports[:5]:
                page_content += f"<li><code>{imp}</code></li>"
            page_content += "</ul>"
        
        if classes:
            page_content += "<h2>Classes</h2><ul>"
            for cls in classes[:5]:
                page_content += f"<li><code>{cls}</code></li>"
            page_content += "</ul>"
        
        if functions:
            page_content += "<h2>Functions</h2><ul>"
            for func in functions[:10]:
                page_content += f"<li><code>{func}</code></li>"
            page_content += "</ul>"
        
        # Throw in the actual code with syntax highlighting
        page_content += '<h2>Source Code</h2>'
        page_content += f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:parameter>'
        page_content += f'<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>'
        
        return page_content
    
    return f"<h1>{title}</h1><p>Documentation page created.</p>"

def create_code_documentation_content(title: str, code_snippet: str, functionality_explanation: str, file_context: str = "", project_context: str = "") -> str:
    """Creates detailed docs for a specific piece of code - perfect for functions or important code blocks"""
    content = f"<h1><strong>{title}</strong></h1>"
    
    # Show the code first
    content += f"<h2><strong>Code</strong></h2>"
    content += f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:parameter>'
    content += f'<ac:plain-text-body><![CDATA[{code_snippet}]]></ac:plain-text-body></ac:structured-macro>'
    
    # Explain what it actually does
    content += f"<h2><strong>Functionality</strong></h2>"
    content += f"<p>{functionality_explanation}</p>"
    
    # Where it fits in the file
    if file_context:
        content += f"<h2><strong>File Context</strong></h2>"
        content += f"<p>{file_context}</p>"
    
    # How it fits in the bigger picture
    if project_context:
        content += f"<h2><strong>Project Context</strong></h2>"
        content += f"<p>{project_context}</p>"
    
    return content

# Tell the MCP client what tools we have available
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    # Here's all the stuff this server can do for you
    return [
        Tool(
            name="create_page",
            description="Create Confluence page with optional code content",
            inputSchema={
                "type": "object",
                "properties": {
                    "space": {"type": "string", "description": "Space key"},
                    "title": {"type": "string", "description": "Page title"},
                    "content": {"type": "string", "description": "Page content in Confluence format"},
                    "code": {"type": "string", "description": "Optional code content for analysis"},
                    "file_path": {"type": "string", "description": "File path"},
                    "parent_id": {"type": "string", "description": "Parent page ID to create page under"}
                },
                "required": ["space", "title"]
            }
        ),
        Tool(
            name="list_spaces",
            description="List available Confluence spaces",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_pages",
            description="Get pages in a space or under a parent page",
            inputSchema={
                "type": "object",
                "properties": {
                    "space": {"type": "string", "description": "Space key"},
                    "parent_id": {"type": "string", "description": "Parent page ID (optional)"}
                },
                "required": ["space"]
            }
        ),
        Tool(
            name="get_page_content",
            description="Get content of a specific page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID"}
                },
                "required": ["page_id"]
            }
        ),
        Tool(
            name="find_page",
            description="Find pages by title in a space",
            inputSchema={
                "type": "object",
                "properties": {
                    "space": {"type": "string", "description": "Space key"},
                    "title": {"type": "string", "description": "Page title to search for"}
                },
                "required": ["space", "title"]
            }
        ),

        Tool(
            name="append_to_page",
            description="Append content to existing Confluence page while preserving existing content",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID to append to"},
                    "new_content": {"type": "string", "description": "Content to append in Confluence storage format"},
                    "insert_after": {"type": "string", "description": "Text marker to insert content after (optional, defaults to end of page)"},
                    "insert_before": {"type": "string", "description": "Text marker to insert content before (optional)"}
                },
                "required": ["page_id", "new_content"]
            }
        ),
        Tool(
            name="get_full_page_content",
            description="Get complete content of a page without truncation",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID"}
                },
                "required": ["page_id"]
            }
        ),
        Tool(
            name="remove_content",
            description="Remove specific content from a Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID"},
                    "content_to_remove": {"type": "string", "description": "Exact content to remove from the page"}
                },
                "required": ["page_id", "content_to_remove"]
            }
        ),
        Tool(
            name="replace_content",
            description="Replace specific content in a Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Page ID"},
                    "old_content": {"type": "string", "description": "Content to replace"},
                    "new_content": {"type": "string", "description": "New content to insert"}
                },
                "required": ["page_id", "old_content", "new_content"]
            }
        ),
        Tool(
            name="create_code_documentation",
            description="Create code documentation for functions or files from the active file or workspace context",
            inputSchema={
                "type": "object",
                "properties": {
                    "space": {"type": "string", "description": "Space key"},
                    "title": {"type": "string", "description": "Page title"},
                    "code_snippet": {"type": "string", "description": "The specific code section to document"},
                    "functionality_explanation": {"type": "string", "description": "Explanation of what this code does"},
                    "file_context": {"type": "string", "description": "How this code fits within the current file"},
                    "project_context": {"type": "string", "description": "How this code relates to the overall project"},
                    "parent_id": {"type": "string", "description": "Parent page ID to create page under"}
                },
                "required": ["space", "title", "code_snippet", "functionality_explanation"]
            }
        )
    ]

# This is where the magic happens - when someone asks us to do something
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    global confluence
    
    # Show them what Confluence spaces they can work with
    if name == "list_spaces":
        if not confluence:
            return [TextContent(type="text", text="Error: Confluence not initialized")]
        try:
            spaces = confluence.get_all_spaces(limit=50)
            result = "Available Confluence Spaces:\n\n"
            for space in spaces['results']:
                result += f"**{space['key']}**: {space['name']}\n"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            logger.error(f"Error listing spaces: {e}")
            return [TextContent(type="text", text=f"Error listing spaces: {str(e)}")]
    
    # Get a list of pages from a space, useful for browsing what's already there
    elif name == "get_pages":
        try:
            space = arguments["space"]
            parent_id = arguments.get("parent_id")
            
            # Either get child pages or all pages in the space
            if parent_id:
                pages = confluence.get_child_pages(parent_id)
                result = f"Pages under parent {parent_id}:\n"
            else:
                pages = confluence.get_all_pages_from_space(space, limit=50)
                result = f"Pages in space {space}:\n"
            
            # List them out nicely
            for page in pages:
                result += f"- {page['id']}: {page['title']}\n"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting pages: {str(e)}")]
    
    # Peek at what's inside a page, gives you a preview of the content
    elif name == "get_page_content":
        try:
            page_id = arguments["page_id"]
            page = confluence.get_page_by_id(page_id, expand='body.storage')
            
            # Show the basics plus a snippet of content
            result = f"Page: {page['title']}\n"
            result += f"ID: {page['id']}\n"
            result += f"Content preview: {page['body']['storage']['value'][:500]}...\n"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting page content: {str(e)}")]
    
    # Hunt for pages by searching their titles, case insensitive search
    elif name == "find_page":
        try:
            space = arguments["space"]
            title = arguments["title"]
            
            # Get all pages and filter by title match
            pages = confluence.get_all_pages_from_space(space, limit=100)
            matches = [p for p in pages if title.lower() in p['title'].lower()]
            
            # Show what we found
            result = f"Pages matching '{title}' in {space}:\n"
            for page in matches:
                result += f"- {page['id']}: {page['title']}\n"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding pages: {str(e)}")]
    
    # Create a basic page, can be just text or include code analysis
    elif name == "create_page":
        if not confluence:
            return [TextContent(type="text", text="Confluence isn't connected, can't create pages right now")]
        try:
            # Grab all the info we need
            space = arguments["space"]
            title = arguments["title"]
            content = arguments.get("content", "")
            code = arguments.get("code", "")
            file_path = arguments.get("file_path", "")
            parent_id = arguments.get("parent_id")
            
            # Let our helper function do the heavy lifting
            page_content = create_simple_content(title, content, code, file_path)
            
            # Create as child page or standalone page
            if parent_id:
                page = confluence.create_page(
                    space=space,
                    title=title,
                    body=page_content,
                    parent_id=parent_id
                )
            else:
                page = confluence.create_page(
                    space=space,
                    title=title,
                    body=page_content
                )
            
            # Build the URL so they can go check it out
            page_url = f"{confluence.url}/pages/viewpage.action?pageId={page['id']}"
            logger.info(f"Page created: {title} (ID: {page['id']})")
            return [TextContent(type="text", text=f"**Page created!**\n\n**Title:** {title}\n**URL:** {page_url}")]
            
        except Exception as e:
            logger.error(f"Page creation failed: {e}")
            return [TextContent(type="text", text=f"Couldn't create the page: {str(e)}")]
    
    # Create detailed documentation for specific code
    elif name == "create_code_documentation":
        if not confluence:
            return [TextContent(type="text", text="Confluence isn't connected, can't create documentation right now")]
        try:
            # Get all the details about the code
            space = arguments["space"]
            title = arguments["title"]
            code_snippet = arguments["code_snippet"]
            functionality_explanation = arguments["functionality_explanation"]
            file_context = arguments.get("file_context", "")
            project_context = arguments.get("project_context", "")
            parent_id = arguments.get("parent_id")
            
            # Build the detailed documentation
            page_content = create_code_documentation_content(
                title, code_snippet, functionality_explanation, file_context, project_context
            )
            
            # Child page or standalone
            if parent_id:
                page = confluence.create_page(
                    space=space,
                    title=title,
                    body=page_content,
                    parent_id=parent_id
                )
            else:
                page = confluence.create_page(
                    space=space,
                    title=title,
                    body=page_content
                )
            
            page_url = f"{confluence.url}/pages/viewpage.action?pageId={page['id']}"
            logger.info(f"Code documentation created: {title} (ID: {page['id']})")
            return [TextContent(type="text", text=f"**Code documentation created!**\n\n**Title:** {title}\n**URL:** {page_url}")]
            
        except Exception as e:
            logger.error(f"Code documentation failed: {e}")
            return [TextContent(type="text", text=f"Couldn't create the code documentation: {str(e)}")]
    

    # Add to an existing page without destroying what's already there
    elif name == "append_to_page":
        try:
            page_id = arguments["page_id"]
            new_content = arguments["new_content"]
            insert_after = arguments.get("insert_after")
            insert_before = arguments.get("insert_before")
            
            # Get the current page content
            current_page = confluence.get_page_by_id(page_id, expand='body.storage')
            existing_content = current_page['body']['storage']['value']
            
            # Figure out where to put the new content
            if insert_before:
                # Try to insert before a specific marker
                if insert_before in existing_content:
                    updated_content = existing_content.replace(insert_before, new_content + insert_before)
                else:
                    # Marker not found, just append to end
                    updated_content = existing_content + new_content
            elif insert_after:
                # Try to insert after a specific marker
                if insert_after in existing_content:
                    updated_content = existing_content.replace(insert_after, insert_after + new_content)
                else:
                    # Marker not found, just append to end
                    updated_content = existing_content + new_content
            else:
                # No markers specified, just add to the end
                updated_content = existing_content + new_content
            
            # Save the updated page
            confluence.update_page(
                page_id=page_id,
                title=current_page['title'],
                body=updated_content
            )
            
            page_url = f"{confluence.url}/pages/viewpage.action?pageId={page_id}"
            return [TextContent(type="text", text=f"Content inserted in: {current_page['title']}\nURL: {page_url}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error inserting content: {str(e)}")]
    
    # Get the complete page content, no truncation
    elif name == "get_full_page_content":
        try:
            page_id = arguments["page_id"]
            page = confluence.get_page_by_id(page_id, expand='body.storage')
            
            # Give them everything, title, ID, and full content
            result = f"Page: {page['title']}\n"
            result += f"ID: {page['id']}\n"
            result += f"Full content:\n{page['body']['storage']['value']}"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting full page content: {str(e)}")]
    
    # Delete specific content from a page
    elif name == "remove_content":
        try:
            page_id = arguments["page_id"]
            content_to_remove = arguments["content_to_remove"]
            
            # Get the current page
            current_page = confluence.get_page_by_id(page_id, expand='body.storage')
            existing_content = current_page['body']['storage']['value']
            
            # Remove the specified content and replace with nothing
            updated_content = existing_content.replace(content_to_remove, "")
            
            # Save the cleaned up page
            confluence.update_page(
                page_id=page_id,
                title=current_page['title'],
                body=updated_content
            )
            
            page_url = f"{confluence.url}/pages/viewpage.action?pageId={page_id}"
            return [TextContent(type="text", text=f"Content removed from: {current_page['title']}\nURL: {page_url}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error removing content: {str(e)}")]
    
    # Swap out old content with new content, like find and replace
    elif name == "replace_content":
        try:
            page_id = arguments["page_id"]
            old_content = arguments["old_content"]
            new_content = arguments["new_content"]
            
            # Get the current page
            current_page = confluence.get_page_by_id(page_id, expand='body.storage')
            existing_content = current_page['body']['storage']['value']
            
            # Do the replacement
            updated_content = existing_content.replace(old_content, new_content)
            
            # Save the updated page
            confluence.update_page(
                page_id=page_id,
                title=current_page['title'],
                body=updated_content
            )
            
            page_url = f"{confluence.url}/pages/viewpage.action?pageId={page_id}"
            return [TextContent(type="text", text=f"Content replaced in: {current_page['title']}\nURL: {page_url}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error replacing content: {str(e)}")]
    
    # Provide a tool that is not right
    else:
        raise ValueError(f"Unknown tool: {name}")

# This is the main event loop, keeps the server running and listening
async def main():
    # Set up the stdio connection, which is how we talk to the MCP client
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="atlassian-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())