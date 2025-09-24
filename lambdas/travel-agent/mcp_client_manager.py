from user import User
import jwt
import time
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import logging

jwt_signature_secret = os.environ['JWT_SIGNATURE_SECRET']
mcp_endpoint = os.getenv("MCP_ENDPOINT")

l = logging.getLogger(__name__)

mcp_tools = {}
mcp_clients = {}

def get_mcp_tools_for_user(user: User):
    if user.id in mcp_tools and user.id in mcp_clients:
        l.info(f"MCP_CACHE_HIT: user_id={user.id}, tools_count={len(mcp_tools[user.id])}")
        return mcp_tools[user.id]

    l.info(f"MCP_CACHE_MISS: user_id={user.id}, creating new client")
    
    # Generate JWT for MCP authentication
    token_payload = {
        "sub": "travel-agent",
        "user_id": user.id,
        "user_name": user.name,
    }
    token = jwt.encode(token_payload, jwt_signature_secret, algorithm="HS256")
    l.info(f"MCP_JWT_GENERATED: user_id={user.id}, payload={token_payload}")

    try:
        # Create MCP client with timing
        client_start = time.time()
        mcp_client = MCPClient(lambda: streamablehttp_client(
            url=mcp_endpoint,
            headers={"Authorization": f"Bearer {token}"},
        ))
        
        l.info(f"MCP_CLIENT_CREATED: endpoint={mcp_endpoint}")
        
        # Start client connection
        connection_start = time.time()
        mcp_client.start()
        connection_duration = time.time() - connection_start
        l.info(f"MCP_CONNECTION_ESTABLISHED: duration={connection_duration:.2f}s")
        
        # List available tools
        tools_start = time.time()
        tools = mcp_client.list_tools_sync()
        tools_duration = time.time() - tools_start
        
        client_total_duration = time.time() - client_start
        l.info(f"MCP_TOOLS_RETRIEVED: count={len(tools)}, tools_duration={tools_duration:.2f}s, total_duration={client_total_duration:.2f}s")
        
        # Log individual tools
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, 'name', 'unknown')
            l.info(f"MCP_TOOL_{i}: name={tool_name}")
        
        # Cache for future use
        mcp_clients[user.id] = mcp_client
        mcp_tools[user.id] = tools
        
        l.info(f"MCP_SETUP_SUCCESS: user_id={user.id}, cached_tools={len(tools)}")
        return mcp_tools[user.id]
        
    except Exception as e:
        l.error(f"MCP_SETUP_ERROR: user_id={user.id}, error_type={type(e).__name__}, error={str(e)}", exc_info=True)
        raise

