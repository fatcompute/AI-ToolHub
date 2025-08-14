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
from .models import db, User, LLMModel, Dataset, TrainingJob, CapturedError, Conversation, ChatMessage

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
        UPLOAD_FOLDER=os.path.join(basedir, 'datasets'),
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
    @app.route('/api/v1/auth/session-login', methods=['POST'])
    def session_login():
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if user:
            # User exists, check password
            if not user.check_password(password):
                return jsonify({"error": "Invalid credentials"}), 401
        else:
            # User does not exist, create a new one
            role = 'admin' if not User.query.first() else 'user'
            # A simple email is required by the model, we can generate one.
            email = f"{username.lower()}@localhost.local"

            if User.query.filter_by(email=email).first():
                return jsonify({"error": "A user with a similar generated email already exists."}), 409

            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

        # Issue token for the logged-in or newly created user
        identity = {"id": user.id, "role": user.role}
        access_token = create_access_token(identity=identity)
        return jsonify(access_token=access_token)

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
        return jsonify([{"id": m.id, "name": m.name, "huggingface_id": m.huggingface_id, "status": m.status} for m in models])

    @app.route("/api/v1/models/download", methods=['POST'])
    @jwt_required()
    def download_model_endpoint():
        data = request.get_json()
        if not data or 'huggingface_id' not in data:
            return jsonify({"error": "Missing 'huggingface_id'"}), 400
        try:
            model = llm_service.download_model(data['huggingface_id'])
            return jsonify({"message": "Model downloaded", "model": {"id": model.id, "name": model.name}}), 201
        except (ValueError, IOError) as e:
            return jsonify({"error": str(e)}), 500

    # Chat & Conversation Routes
    @app.route("/api/v1/chat", methods=['POST'])
    @jwt_required()
    def chat_endpoint():
        data = request.get_json()
        if not data or 'model_id' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing 'model_id' or 'prompt'"}), 400
        user_id = get_jwt_identity()['id']
        conversation_id = data.get('conversation_id')
        prompt_text = data['prompt']
        model_id = data['model_id']
        try:
            if conversation_id:
                conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first_or_404()
            else:
                title = prompt_text[:40] + '...' if len(prompt_text) > 40 else prompt_text
                conversation = Conversation(title=title, user_id=user_id, model_id=model_id)
                db.session.add(conversation)
                db.session.flush()
            user_message = ChatMessage(conversation_id=conversation.id, role='user', content=prompt_text)
            db.session.add(user_message)
            bot_response_text = llm_service.generate_text(model_id, prompt_text)
            bot_message = ChatMessage(conversation_id=conversation.id, role='bot', content=bot_response_text)
            db.session.add(bot_message)
            db.session.commit()
            return jsonify({"response": bot_response_text, "conversation_id": conversation.id})
        except (ValueError, RuntimeError) as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/v1/conversations', methods=['GET'])
    @jwt_required()
    def list_conversations():
        user_id = get_jwt_identity()['id']
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()
        return jsonify([{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in conversations])

    @app.route('/api/v1/conversations/<int:conv_id>', methods=['GET'])
    @jwt_required()
    def get_conversation(conv_id):
        user_id = get_jwt_identity()['id']
        conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first_or_404()
        messages = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.created_at.asc()).all()
        return jsonify({"id": conv.id, "title": conv.title, "messages": [{"role": m.role, "content": m.content} for m in messages]})

    @app.route('/api/v1/conversations/<int:conv_id>', methods=['DELETE'])
    @jwt_required()
    def delete_conversation(conv_id):
        user_id = get_jwt_identity()['id']
        conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first_or_404()
        db.session.delete(conv)
        db.session.commit()
        return jsonify({"message": "Conversation deleted successfully."})

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

    # System and Agent Routes
    # ... (System and Agent routes remain the same) ...
    @app.route('/api/v1/system/config', methods=['GET'])
    @admin_required()
    def get_system_config():
        config_data = {"upload_folder": app.config.get('UPLOAD_FOLDER'), "models_dir": llm_service.MODELS_DIR}
        return jsonify(config_data)

    @app.route('/api/v1/agent/errors', methods=['GET'])
    @admin_required()
    def list_captured_errors():
        errors = CapturedError.query.order_by(CapturedError.created_at.desc()).all()
        return jsonify([{"id": e.id, "status": e.status, "file_path": e.file_path, "line_number": e.line_number, "created_at": e.created_at.isoformat()} for e in errors])

    @app.route('/api/v1/agent/errors/<int:error_id>', methods=['GET'])
    @admin_required()
    def get_captured_error(error_id):
        error = CapturedError.query.get_or_404(error_id)
        return jsonify({"id": error.id, "status": error.status, "file_path": error.file_path, "line_number": error.line_number, "created_at": error.created_at.isoformat(), "traceback": error.traceback, "analysis": error.analysis, "proposed_fix": error.proposed_fix})

    # Global Error Handler
    # ... (Error handler remains the same) ...
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
    # Note: db.create_all() is removed from here. Use 'flask db upgrade'.
    # The install.sh script will handle the initial migration.
    app.run(host="0.0.0.0", port=5000, debug=True)
