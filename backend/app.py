import os
import subprocess
import sys
import traceback
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from .models import db, User, LLMModel, Dataset, TrainingJob, CapturedError

# --- Application Factory Function ---
def create_app(config_overrides=None):
    """Creates and configures an instance of the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # --- Configuration ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_uri = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'a-default-dev-secret-key')
    )
    if config_overrides:
        app.config.update(config_overrides)

    # --- Initialize Extensions ---
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    # --- Import Services ---
    from . import llm_service
    from . import agent_service

    # --- Custom Decorators ---
    def admin_required():
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                verify_jwt_in_request()
                claims = get_jwt_identity()
                if claims.get('role') == 'admin':
                    return fn(*args, **kwargs)
                else:
                    return jsonify(msg="Admins only!"), 403
            return decorator
        return wrapper

    # --- API Routes ---
    @app.route("/api/v1")
    def index():
        return {"message": "Flask backend is running!"}

    # --- Auth Routes ---
    @app.route('/api/v1/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing username, email, or password"}), 400
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 409
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already exists"}), 409
        role = 'admin' if not User.query.first() else 'user'
        new_user = User(username=data['username'], email=data['email'], role=role)
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": f"User {new_user.username} created successfully"}), 201

    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing email or password"}), 400
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            identity = {"id": user.id, "role": user.role}
            access_token = create_access_token(identity=identity)
            return jsonify(access_token=access_token)
        return jsonify({"error": "Invalid credentials"}), 401

    @app.route('/api/v1/auth/profile', methods=['GET'])
    @jwt_required()
    def profile():
        current_user_identity = get_jwt_identity()
        user = User.query.get(current_user_identity['id'])
        if user:
            return jsonify({
                "id": user.id, "username": user.username, "email": user.email,
                "role": user.role, "settings": user.settings or {}
            })
        return jsonify({"error": "User not found"}), 404

    @app.route('/api/v1/users/settings', methods=['PUT'])
    @jwt_required()
    def update_user_settings():
        user_id = get_jwt_identity()['id']
        user = User.query.get(user_id)
        data = request.get_json()
        if 'settings' not in data:
            return jsonify({"error": "Missing 'settings' field"}), 400
        current_settings = user.settings or {}
        current_settings.update(data['settings'])
        user.settings = current_settings
        db.session.commit()
        return jsonify({"message": "Settings updated", "settings": user.settings})

    # LLM Model Routes
    @app.route("/api/v1/models", methods=['GET'])
    @jwt_required()
    def get_models():
        models = llm_service.list_local_models()
        return jsonify([{"id": m.id, "name": m.name, "filename": m.filename} for m in models])

    @app.route("/api/v1/models/download", methods=['POST'])
    @jwt_required()
    def download_model_endpoint():
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({"error": "Missing 'filename' in request body"}), 400

        # model_name is optional, can be used for a user-friendly alias
        model_name = data.get('model_name')

        try:
            model = llm_service.download_model(data['filename'], model_name)
            return jsonify({"message": "Model downloaded", "model": {"id": model.id, "name": model.name}}), 201
        except (ValueError, IOError) as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/v1/chat", methods=['POST'])
    @jwt_required()
    def chat_endpoint():
        data = request.get_json()
        if not data or 'model_id' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing 'model_id' or 'prompt'"}), 400
        try:
            response = llm_service.generate_text(data['model_id'], data['prompt'])
            return jsonify({"response": response})
        except (ValueError, RuntimeError) as e:
            return jsonify({"error": str(e)}), 500

    # User Management Routes (Admin Only)
    @app.route('/api/v1/users', methods=['GET'])
    @admin_required()
    def list_users():
        users = User.query.all()
        return jsonify([{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users])

    @app.route('/api/v1/users/<int:user_id>', methods=['PUT'])
    @admin_required()
    def update_user(user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        if 'role' in data:
            if data['role'] not in ['user', 'admin']:
                return jsonify({"error": "Invalid role specified"}), 400
            user.role = data['role']
        db.session.commit()
        return jsonify({"message": f"User {user.username} updated successfully."})

    @app.route('/api/v1/users/<int:user_id>', methods=['DELETE'])
    @admin_required()
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        current_user_id = get_jwt_identity()['id']
        if user.id == current_user_id:
            return jsonify({"error": "Admin cannot delete themselves"}), 403
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user.username} deleted successfully."})

    # System Routes (Admin Only)
    @app.route('/api/v1/system/config', methods=['GET'])
    @admin_required()
    def get_system_config():
        config_data = {
            "upload_folder": app.config.get('UPLOAD_FOLDER'),
            "models_dir": llm_service.MODELS_DIR
        }
        return jsonify(config_data)

    # Agent Routes (Admin Only)
    @app.route('/api/v1/agent/errors', methods=['GET'])
    @admin_required()
    def list_captured_errors():
        errors = CapturedError.query.order_by(CapturedError.created_at.desc()).all()
        return jsonify([{
            "id": e.id, "status": e.status, "file_path": e.file_path,
            "line_number": e.line_number, "created_at": e.created_at.isoformat()
        } for e in errors])

    @app.route('/api/v1/agent/errors/<int:error_id>', methods=['GET'])
    @admin_required()
    def get_captured_error(error_id):
        error = CapturedError.query.get_or_404(error_id)
        return jsonify({
            "id": error.id, "status": error.status, "file_path": error.file_path,
            "line_number": error.line_number, "created_at": error.created_at.isoformat(),
            "traceback": error.traceback, "analysis": error.analysis, "proposed_fix": error.proposed_fix
        })

    # --- Global Error Handler ---
    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e

        tb_str = traceback.format_exc()
        try:
            _, _, tb = sys.exc_info()
            if tb is not None:
                while tb.tb_next:
                    tb = tb.tb_next
                frame = tb.tb_frame
                lineno = tb.tb_lineno
                filename = frame.f_code.co_filename
            else:
                filename, lineno = None, None
        except Exception:
            filename, lineno = None, None

        error_record = CapturedError(traceback=tb_str, file_path=filename, line_number=lineno)
        db.session.add(error_record)
        db.session.commit()

        agent_service.analyze_error_async(error_record.id)

        return jsonify({"error": "An internal server error occurred. The issue has been logged and is being analyzed."}), 500

    return app

# --- Main Execution ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
