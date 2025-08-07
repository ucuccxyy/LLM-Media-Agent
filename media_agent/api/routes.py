from flask import Blueprint, request, Response, stream_with_context, jsonify
from threading import Lock
import json
import time
import logging
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from langchain_core.messages import AIMessage, HumanMessage, AIMessageChunk
from uuid import uuid4

# We need to import the necessary components to initialize our agent
from media_agent.core.agent import MediaAgent
from media_agent.core.llm_manager import LLMManager
from media_agent.config.settings import Settings
from media_agent.api.sessions import get_session_history, clear_session_history, cleanup_old_sessions

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

api_v1 = Blueprint('api_v1', __name__)

# A global variable to hold our agent instance.
# We use a lock to ensure thread-safe initialization.
agent_instance: MediaAgent = None
agent_lock = Lock()

# In-memory cache for conversation histories
# The key is session_id, the value is a list of Messages
conversation_histories = {}


def get_agent() -> MediaAgent:
    """
    Initializes and returns a thread-safe, singleton instance of the MediaAgent.
    This "lazy initialization" ensures the agent is only created when the first
    API request comes in, not on application startup.
    """
    global agent_instance
    # Use a lock to prevent race conditions during initialization
    with agent_lock:
        if agent_instance is None:
            logging.info("Initializing MediaAgent for the first time...")
            # Load settings and create the necessary components
            settings = Settings()
            settings.load_from_env()
            llm_manager = LLMManager(settings)
            # Create the singleton instance
            agent_instance = MediaAgent(llm_manager, settings)
            logging.info("MediaAgent initialized.")
    return agent_instance


@api_v1.route('/reset_session', methods=['POST'])
def reset_session():
    """
    Resets the conversation history for a given session ID.
    """
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    # 使用新的清理函数
    if clear_session_history(session_id):
        log.info(f"Conversation history for session_id '{session_id}' has been reset.")
        return jsonify({"status": "success", "message": f"Session {session_id} reset."})
    else:
        log.warning(f"Attempted to reset non-existent session_id: '{session_id}'")
        return jsonify({"status": "not_found", "message": f"No active session {session_id} to reset."})


def convert_chunk_to_dict(chunk):
    """Converts a LangChain stream chunk to a JSON-serializable dictionary."""
    
    # The new streaming format gives us dictionaries at each step.
    if isinstance(chunk, dict) and 'messages' in chunk and chunk['messages']:
        message = chunk['messages'][0]
        if isinstance(message, AIMessageChunk):
            # Case 1: This is a thinking step or part of the final answer
            if message.content:
                return {"type": "thinking_step", "data": message.content}
            
            # Case 2: The agent has decided to use a tool.
            # This is the most complex part, as args are streamed.
            # We will return a standardized 'tool_run' event.
            if hasattr(message, 'tool_call_chunks') and message.tool_call_chunks:
                tool_call_chunk = message.tool_call_chunks[0]
                # Let's build the full tool call object from the chunks
                args_str = tool_call_chunk.get('args', '{}')
                try:
                    args_dict = json.loads(args_str)
                except json.JSONDecodeError:
                    args_dict = {} # Handle partially streamed JSON

                logging.info(f"Detected tool_call_chunk: {tool_call_chunk}")
                return {
                    "type": "tool_run",
                    "data": {
                        "tool_name": tool_call_chunk['name'],
                        "tool_input": args_dict,
                        "tool_call_id": tool_call_chunk['id']
                    }
                }

    # Case 3: A tool's output has been received.
    if isinstance(chunk, dict) and 'steps' in chunk and chunk['steps']:
        step = chunk['steps'][0]
        if isinstance(step, AgentStep):
            logging.info(f"Detected AgentStep (tool result) for tool '{step.action.tool}'.")
            return {
                "type": "tool_result",
                "data": {
                    "tool_name": step.action.tool,
                    "observation": step.observation,
                    "tool_call_id": step.action.tool_call_id
                }
            }

    # Case 4: The agent has finished its work and is giving the final output.
    if isinstance(chunk, dict) and 'output' in chunk:
        output = chunk['output']
        logging.info(f"Detected final output dictionary: {output}")
        return {"type": "final_output", "data": {"output": output}}
        
    logging.warning(f"Unhandled or empty chunk of type {type(chunk)}: {chunk}")
    return None


@api_v1.route('/stream', methods=['GET'])
def stream():
    session_id = request.args.get('session_id', 'default_session')
    message_text = request.args.get('message', '')

    if not message_text:
        return jsonify({"error": "Message text is required"}), 400

    agent = get_agent()
    history = get_session_history(session_id)
    
    # 先添加用户消息到历史
    history.add_user_message(message_text)
    
    agent_input = {
        "input": message_text,
        "chat_history": history.messages
    }

    logging.info(f"Streaming response for session_id: {session_id} with history length: {len(history.messages)}")
    
    def generate():
        final_answer = ""
        try:

            yield f"data: {json.dumps({'type': 'status', 'message': 'Agent is thinking...'})}\n\n"
            
            for chunk in agent.agent_executor.stream(agent_input):
                converted_chunk = convert_chunk_to_dict(chunk)
                if converted_chunk:
                    logging.info(f"Streaming chunk: {json.dumps(converted_chunk)}")
                    yield f"data: {json.dumps(converted_chunk)}\n\n"

                    chunk_type = converted_chunk.get("type")
                    chunk_data = converted_chunk.get("data", {})
                    
                    if chunk_type == 'tool_run':
                        history.add_ai_tool_call_message({
                            "name": chunk_data['tool_name'],
                            "args": chunk_data['tool_input'],
                            "id": chunk_data['tool_call_id']
                        })
                    
                    elif chunk_type == 'tool_result':
                        history.add_tool_result_message(
                            chunk_data['tool_name'], 
                            chunk_data['observation'], 
                            chunk_data['tool_call_id']
                        )
                    
                    elif chunk_type == 'final_output':
                        if isinstance(chunk_data, dict):
                            final_answer = chunk_data.get('output', '')

                    time.sleep(0.01)

        except Exception as e:
            logging.error(f"Error during agent stream for session {session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            if final_answer:
                # The final answer part of the AIMessage.
                history.add_ai_message(final_answer)
                logging.info(f"History for {session_id} updated with final AI answer.")
            else:
                logging.warning(f"Stream for session {session_id} finished without a final output. Final AI message not added to history.")

            logging.info(f"Stream finished for session {session_id}.")
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@api_v1.route('/chat_sync', methods=['POST'])
def chat_sync():
    """
    The original synchronous endpoint for interacting with the agent.
    This is kept for testing or for simple, quick requests.
    It waits for the full agent execution to complete.
    """
    data = request.get_json()
    if not data or 'message' not in data or not data['message'].strip():
        return jsonify({"error": "A non-empty 'message' field is required."}), 400

    user_input = data['message']
    session_id = data.get('session_id', 'default_session')
    
    try:
        # Get the singleton agent instance
        agent = get_agent()
        
        # Get session history
        history = get_session_history(session_id)
        
        # Add user message to history
        history.add_user_message(user_input)
        
        # Build agent input with chat history
        agent_input = {
            "input": user_input,
            "chat_history": history.messages
        }
        
        logging.info(f"Processing chat_sync request for session_id: {session_id} with history length: {len(history.messages)}")
        
        # Process the request using the same method as stream endpoint
        response = agent.agent_executor.invoke(agent_input)
        
        # Extract the final natural language response from the agent's output
        final_response = response.get("output", "Sorry, I encountered an issue and couldn't get a response.")
        
        # Add AI response to history - handle both simple responses and tool call responses
        if final_response and final_response != "Sorry, I encountered an issue and couldn't get a response.":
            # Check if the response contains tool calls that need to be added to history
            if "intermediate_steps" in response:
                # Handle tool calls and results like in stream endpoint
                for step in response["intermediate_steps"]:
                    if hasattr(step, 'action') and hasattr(step, 'observation'):
                        # Add tool call to history
                        history.add_ai_tool_call_message({
                            "name": step.action.tool,
                            "args": step.action.tool_input,
                            "id": step.action.tool_call_id
                        })
                        # Add tool result to history
                        history.add_tool_result_message(
                            step.action.tool,
                            step.observation,
                            step.action.tool_call_id
                        )
            
            # Add the final AI response
            history.add_ai_message(final_response)
            logging.info(f"History for {session_id} updated with AI response.")
        
        return jsonify({"response": final_response})

    except Exception as e:
        # Log the exception for debugging purposes
        logging.error(f"An error occurred while processing a chat request for session {session_id}: {e}", exc_info=True)
        # Return a generic error message to the user
        return jsonify({"error": "An internal server error occurred."}), 500


@api_v1.route('/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    In a real-world scenario, this could be expanded to check the status
    of dependent services like Radarr, Sonarr, etc.
    """
    return jsonify({"status": "healthy"}) 