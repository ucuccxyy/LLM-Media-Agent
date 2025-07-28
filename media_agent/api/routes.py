from flask import Blueprint, request, Response, stream_with_context, jsonify
from threading import Lock
import json
import time
import logging
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from langchain_core.messages import AIMessage, HumanMessage, AIMessageChunk

# We need to import the necessary components to initialize our agent
from media_agent.core.agent import MediaAgent
from media_agent.core.llm_manager import OllamaManager
from media_agent.config.settings import Settings
from media_agent.api.sessions import get_session_history

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
            llm_manager = OllamaManager(settings.ollama_host, settings.ollama_model)
            # Create the singleton instance
            agent_instance = MediaAgent(llm_manager, settings)
            logging.info("MediaAgent initialized.")
    return agent_instance

def convert_chunk_to_dict(chunk):
    """Converts a LangChain stream chunk to a JSON-serializable dictionary."""
    
    # Case 0: Final output in a dictionary with 'output' key
    if isinstance(chunk, dict) and 'output' in chunk:
        output = chunk['output']
        logging.info(f"Detected final output dictionary: {output}")
        return {"type": "final_output", "data": {"output": output}}
    
    # The new streaming format gives us dictionaries at each step.
    # We need to inspect the contents of the dictionary to see what's inside.
    
    # Case 1: A "final" answer is being streamed token by token.
    # It's inside the 'messages' list as an AIMessageChunk.
    if isinstance(chunk, dict) and 'messages' in chunk and chunk['messages'] and isinstance(chunk['messages'][0], AIMessageChunk):
        message_chunk = chunk['messages'][0]
        
        # This is a thinking step or part of the final answer
        if message_chunk.content:
            logging.info(f"Detected content chunk: {message_chunk.content}")
            return {"type": "thinking_step", "data": message_chunk.content}
        
        # This is the agent deciding to use a tool.
        # Note: The 'args' are often streamed as a partial JSON string.
        if hasattr(message_chunk, 'tool_call_chunks') and message_chunk.tool_call_chunks:
            tool_call_chunk = message_chunk.tool_call_chunks[0]
            logging.info(f"Detected tool_call_chunk: {tool_call_chunk}")
            return {
                "type": "tool_call",
                "tool_name": tool_call_chunk['name'],
                "tool_input_chunk": tool_call_chunk['args'] 
            }

    # Case 1.5: Final output in messages list as AIMessage
    if isinstance(chunk, dict) and 'messages' in chunk and chunk['messages'] and isinstance(chunk['messages'][0], AIMessage):
        message = chunk['messages'][0]
        if message.content:
            logging.info(f"Detected final AIMessage: {message.content}")
            return {"type": "final_output", "data": {"output": message.content}}

    # Case 2: Direct AgentAction object (alternative format)
    if isinstance(chunk, AgentAction):
        logging.info(f"Detected AgentAction for tool '{chunk.tool}'.")
        return {
            "type": "tool_run", 
            "tool_name": chunk.tool, 
            "tool_input": chunk.tool_input
        }

    # Case 3: A tool's output has been received.
    # This is an AgentStep object inside the 'steps' list.
    if isinstance(chunk, dict) and 'steps' in chunk and chunk['steps'] and isinstance(chunk['steps'][0], AgentStep):
        step = chunk['steps'][0]
        logging.info(f"Detected AgentStep (tool result) for tool '{step.action.tool}'.")
        return {
            "type": "tool_result",
            "tool_name": step.action.tool,
            "observation": step.observation
        }

    # Case 4: The agent has finished its work.
    # This is an AgentFinish object inside the 'messages' list.
    if isinstance(chunk, dict) and 'messages' in chunk and chunk['messages'] and isinstance(chunk['messages'][0], AgentFinish):
        finish = chunk['messages'][0]
        logging.info("Detected AgentFinish.")
        return {
            "type": "final_output",
            "data": finish.return_values
        }
    
    # Case 5: Direct AgentFinish object (alternative format)
    if isinstance(chunk, AgentFinish):
        logging.info("Detected direct AgentFinish.")
        return {
            "type": "final_output",
            "data": chunk.return_values
        }
        
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
    
    agent_input = {
        "input": message_text,
        "chat_history": history.messages
    }

    logging.info(f"Streaming response for session_id: {session_id} with history length: {len(history.messages)}")
    
    def generate():
        final_answer = None
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Agent is thinking...'})}\n\n"
            
            for chunk in agent.agent_executor.stream(agent_input):
                converted_chunk = convert_chunk_to_dict(chunk)
                if converted_chunk:
                    logging.info(f"Streaming chunk: {json.dumps(converted_chunk)}")
                    if converted_chunk.get('type') == 'final_output':
                        final_answer_data = converted_chunk.get('data', {})
                        if isinstance(final_answer_data, dict):
                            final_answer = final_answer_data.get('output')

                    yield f"data: {json.dumps(converted_chunk)}\n\n"
                    time.sleep(0.01)
            
            history.add_user_message(message_text)
            if final_answer:
                history.add_ai_message(final_answer)
            else:
                logging.warning(f"Stream for session {session_id} finished without a final output. AI message not added to history.")
                history.add_ai_message("Task completed.") # Fallback

        except Exception as e:
            logging.error(f"Error during agent stream for session {session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
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
    
    try:
        # Get the singleton agent instance
        agent = get_agent()
        # Process the request
        result = agent.process_request(user_input)
        
        # Extract the final natural language response from the agent's output
        final_response = result.get("output", "Sorry, I encountered an issue and couldn't get a response.")
        
        return jsonify({"response": final_response})

    except Exception as e:
        # Log the exception for debugging purposes
        logging.error(f"An error occurred while processing a chat request: {e}", exc_info=True)
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