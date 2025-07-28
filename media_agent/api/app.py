from flask import Flask, Blueprint, send_from_directory
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__, static_folder=None)
    CORS(app)
    
    # Import the API blueprint
    from media_agent.api.routes import api_v1
    
    # Register the blueprint with the URL prefix
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    
    # Serve the frontend
    # Correctly determine the frontend directory relative to this script's location
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    frontend_dir = os.path.join(project_root, 'frontend')

    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(frontend_dir, path)
    
    return app 