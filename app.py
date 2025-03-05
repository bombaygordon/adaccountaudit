from flask import Flask, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from extensions import db, migrate, login_manager
from auth.models import User

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object('config.Config')

    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/enhanced_audit.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Enhanced Audit startup')

    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from web.routes import web_bp
    from api.routes import api_bp
    from auth.routes import auth_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('Server Error: %s', error)
        return jsonify({"error": "Internal Server Error", "details": str(error)}), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found", "details": str(error)}), 404

    return app

def init_db(app):
    with app.app_context():
        app.logger.info('Creating database tables...')
        try:
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error('Error creating database tables: %s', e)
            raise

# Create the application instance
app = create_app()

# Initialize the database
with app.app_context():
    init_db(app)

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        with app.app_context():
            return User.query.get(int(user_id))
    except Exception as e:
        app.logger.error(f'Error loading user: {e}')
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)