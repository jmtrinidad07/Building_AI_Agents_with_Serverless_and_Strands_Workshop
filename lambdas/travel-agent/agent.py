from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
import os
import logging
import time
from user import User
import mcp_client_manager
import tools
from agent_config import model, system_prompt
from logger import log_agent_interaction

l = logging.getLogger(__name__)
l.setLevel(logging.INFO)

SESSION_STORE_BUCKET_NAME = os.environ['SESSION_STORE_BUCKET_NAME']

@log_agent_interaction
def prompt(user: User, composite_prompt: str):
    l.info(f"AGENT_INIT: user_id={user.id}, username={user.name}, bucket={SESSION_STORE_BUCKET_NAME}")
    
    session_id = f"session_for_user_{user.id}"
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=SESSION_STORE_BUCKET_NAME,
        prefix="agent_sessions"
    )
    l.info(f"SESSION_MANAGER: session_id={session_id}")

    try:
        # Get MCP tools with timing
        mcp_start = time.time()
        mcp_tools = mcp_client_manager.get_mcp_tools_for_user(user)
        mcp_duration = time.time() - mcp_start
        l.info(f"MCP_TOOLS_LOADED: count={len(mcp_tools)}, duration={mcp_duration:.2f}s")
        
        # Initialize agent
        agent_start = time.time()
        agent = Agent(
            model=model,
            agent_id="travel_agent",
            session_manager=session_manager,
            system_prompt=system_prompt,
            callback_handler=None,
            tools=[tools] + mcp_tools,
        )
        agent_init_duration = time.time() - agent_start
        l.info(f"AGENT_INITIALIZED: duration={agent_init_duration:.2f}s")
        
        # Execute agent prompt
        execution_start = time.time()
        l.info(f"AGENT_EXECUTION_START: prompt_length={len(composite_prompt)}")
        agent_response = agent(composite_prompt)
        execution_duration = time.time() - execution_start
        
        response_text = agent_response.message["content"][0]["text"]
        l.info(f"AGENT_EXECUTION_SUCCESS: duration={execution_duration:.2f}s, response_length={len(response_text)}")
        
        # Log any tool calls made during execution
        if hasattr(agent_response, 'tool_calls') and agent_response.tool_calls:
            l.info(f"TOOL_CALLS_MADE: count={len(agent_response.tool_calls)}")
            for i, tool_call in enumerate(agent_response.tool_calls):
                l.info(f"TOOL_CALL_{i}: name={tool_call.get('name', 'unknown')}")
        
        return response_text

    except Exception as e:
        l.error(f"AGENT_ERROR: type={type(e).__name__}, message={str(e)}", exc_info=True)
        return f'Agent execution failed. Error: {str(e)}'

