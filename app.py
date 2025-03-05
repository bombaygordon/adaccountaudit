from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from extensions import db, migrate, login_manager
from auth.models import User

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'dev'
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_new.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session configuration for ngrok
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Simple request logger
    @app.before_request
    def log_request():
        print("\n=== Request Info ===")
        print(f"URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Is HTTPS: {request.is_secure}")
        print("===================\n")

        # Handle ngrok-specific headers
        if 'X-Forwarded-Proto' in request.headers:
            scheme = request.headers.get('X-Forwarded-Proto')
            if scheme:
                request.environ['wsgi.url_scheme'] = scheme

    # Simple response logger
    @app.after_request
    def add_headers(response):
        print("\n=== Response Info ===")
        print(f"Status: {response.status}")
        print(f"Headers: {dict(response.headers)}")
        print("===================\n")

        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Enable CORS
    CORS(app, 
         resources={r"/*": {"origins": "*"}},
         supports_credentials=True,
         expose_headers=["Content-Type", "X-CSRFToken"])

    # Register blueprints
    from web.routes import web_bp
    from api.routes import api_bp
    from auth.routes import auth_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app

def init_db(app):
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            raise

# Create the application instance
app = create_app()

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        with app.app_context():
            return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None

if __name__ == '__main__':
    print("\n=== Starting Flask Application ===")
    print("Try these URLs:")
    print("1. http://localhost:5000/test")
    print("2. http://localhost:5000/health")
    print("3. http://localhost:5000/debug")
    print("================================\n")
    
    # Initialize the database
    with app.app_context():
        init_db(app)
    
    app.run(host='0.0.0.0', port=5000, debug=True)