from fastmcp import FastMCP
import random
import json

# Create the FastMCP server instance
mcp = FastMCP("Simple Calculator Server")

# Tool: Add two numbers
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b

# Tool: Generate a random number within a range
@mcp.tool()
def generate_random_number(min_val: int, max_val: int) -> int:
    """Generate a random number between min_val and max_val.

    Args:
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        A random integer
    """
    return random.randint(min_val, max_val)

# Resource: Server information
@mcp.resource("info://server")
def get_server_info() -> str:
    """Get information about this simple remote calculator server."""
    return json.dumps({
        "name": "Simple Calculator Server",
        "version": "1.0.0",
        "description": "A remote test MCP server built with FastMCP."
    })

if __name__ == "__main__":
    # Note: For remote server deployment, set transport to HTTP with appropriate host and port
    mcp.run(transport="http", host="0.0.0.0", port=8000)