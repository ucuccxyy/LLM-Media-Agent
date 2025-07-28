import argparse
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# 将项目根目录添加到Python路径，以确保模块可以被正确导入
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from media_agent.api.app import create_app
from media_agent.core.agent import MediaAgent
from media_agent.core.llm_manager import OllamaManager
from media_agent.config.settings import Settings


def run_cli_mode():
    """Runs the agent in a command-line interface mode for interactive testing."""
    print("Starting Media Agent in CLI mode...")

    settings = Settings()
    settings.load_from_env()

    llm_manager = OllamaManager(settings.ollama_host, settings.ollama_model)
    agent = MediaAgent(llm_manager, settings)

    print("Media management assistant is ready! Type 'exit' to quit.")
    while True:
        try:
            user_input = input("\nYour request: ")
            if user_input.lower() == 'exit':
                print("Exiting...")
                break
            
            if not user_input.strip():
                continue

            response = agent.process_request(user_input)
            print("\n--- Agent Response ---")
            # The final response is in the 'output' key
            print(response.get('output', 'No output from agent.'))
            print("--- End of Response ---\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")


def run_api_mode():
    """Runs the agent as a web API service using Flask."""
    # Setup logging first to capture all subsequent errors
    log_dir = os.path.join(project_root, 'media_agent', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'api.log')

    # Clear previous log file for a clean start
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except OSError as e:
            # This can happen if another process is holding the file
            # We can log this to stderr for immediate visibility
            print(f"Error removing log file: {e}", file=sys.stderr)


    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    
    # Also log to console for immediate feedback during script execution
    # This might help us see errors that don't make it to the file
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


    logging.info("--- Starting Media Agent in API mode ---")

    try:
        settings = Settings()
        settings.load_from_env()
        logging.info(f"Using LLM model: {settings.ollama_model}")

        app = create_app()
        logging.info("Flask app created successfully.")

        logging.info("Attempting to start Flask server on host=0.0.0.0, port=5001...")
        # Note: debug=False is important for production and nohup
        app.run(host='0.0.0.0', port=5001, debug=False) 
        
    except Exception as e:
        logging.error("!!! A critical error occurred during API startup !!!", exc_info=True)
    
    logging.info("--- Media Agent has shut down ---")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Media Management Agent')
    parser.add_argument(
        '--mode',
        choices=['cli', 'api'],
        default='cli',
        help='Running mode: cli (command-line interface) or api (Web API)'
    )
    args = parser.parse_args()

    if args.mode == 'cli':
        run_cli_mode()
    else:
        run_api_mode()

if __name__ == "__main__":
    main() 