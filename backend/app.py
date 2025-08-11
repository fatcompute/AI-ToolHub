import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from .models import db, User, LLMModel, Dataset, TrainingJob

# --- Application Factory Function ---
def create_app(config_overrides=None):
    """Creates and configures an instance of the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # --- Configuration ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Default to SQLite for dev, but allow override for prod with PostgreSQL
    database_uri = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(basedir, 'datasets'),
        # Change this in production!
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'a-default-dev-secret-key')
    )
    if config_overrides:
        app.config.update(config_overrides)

    # --- Initialize Extensions and Register Blueprints/Routes ---
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app) # Initialize JWT

    # Import services and routes inside the factory
    import backend.llm_service as llm_service
    from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
    from functools import wraps

    # --- Custom Decorators ---
    def admin_required():
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                # This requires that the identity is a dictionary with a 'role' key
                verify_jwt_in_request()
                claims = get_jwt_identity()
                if claims.get('role') == 'admin':
                    return fn(*args, **kwargs)
                else:
                    return jsonify(msg="Admins only!"), 403
            return decorator
        return wrapper

    # Import services and routes inside the factory
    import backend.llm_service as llm_service
    from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
    from functools import wraps

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

        # Make the first registered user an admin
        role = 'admin' if not User.query.first() else 'user'

        new_user = User(
            username=data['username'],
            email=data['email'],
            role=role
        )
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
            # Include user's role and id in the token
            identity = {"id": user.id, "role": user.role}
            access_token = create_access_token(identity=identity)
            return jsonify(access_token=access_token)

        return jsonify({"error": "Invalid credentials"}), 401

    @app.route('/api/v1/auth/profile', methods=['GET'])
    @jwt_required()
    def profile():
        current_user_identity = get_jwt_identity()
        user_id = current_user_identity['id']
        user = User.query.get(user_id)
        if user:
            return jsonify({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            })
        return jsonify({"error": "User not found"}), 404

    @app.route("/api/v1")
    def index():
        return {"message": "Flask backend is running!"}

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

    # Dataset Routes
    @app.route('/api/v1/datasets', methods=['GET'])
    @jwt_required()
    def list_datasets():
        datasets = Dataset.query.all()
        return jsonify([{"id": ds.id, "filename": ds.filename, "created_at": ds.created_at.isoformat()} for ds in datasets])

    @app.route('/api/v1/datasets/upload', methods=['POST'])
    @jwt_required()
    def upload_dataset():
        if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '': return jsonify({"error": "No selected file"}), 400
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath): return jsonify({"error": "File with this name already exists"}), 409
            file.save(filepath)
            new_dataset = Dataset(filename=filename, path=filepath)
            db.session.add(new_dataset)
            db.session.commit()
            return jsonify({"message": "Dataset uploaded", "dataset": {"id": new_dataset.id, "filename": filename}}), 201
        return jsonify({"error": "File upload failed"}), 400

    # Training Job Routes
    @app.route('/api/v1/jobs', methods=['GET'])
    @jwt_required()
    def list_jobs():
        jobs = TrainingJob.query.order_by(TrainingJob.created_at.desc()).all()
        return jsonify([
            {
                "id": job.id, "model_id": job.model_id, "dataset_id": job.dataset_id,
                "status": job.status, "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            } for job in jobs
        ])

    @app.route('/api/v1/jobs/<int:job_id>', methods=['GET'])
    @jwt_required()
    def get_job(job_id):
        job = TrainingJob.query.get_or_404(job_id)
        return jsonify({
            "id": job.id, "status": job.status, "logs": job.logs,
            "metrics": job.metrics, # Return the structured metrics
            "model_name": job.model.name, "dataset_name": job.dataset.filename
        })

    @app.route('/api/v1/jobs/start', methods=['POST'])
    @jwt_required()
    def start_job():
        data = request.get_json()
        if not data or 'model_id' not in data or 'dataset_id' not in data:
            return jsonify({"error": "Missing 'model_id' or 'dataset_id'"}), 400

        job = TrainingJob(model_id=data['model_id'], dataset_id=data['dataset_id'])
        db.session.add(job)
        db.session.commit()

        # Launch the training script in a separate process
        python_executable = os.sys.executable
        script_path = os.path.join(os.path.dirname(__file__), 'training_service.py')
        subprocess.Popen([python_executable, script_path, str(job.id)])

        return jsonify({"message": "Training job started", "job_id": job.id}), 202

    # --- User Management Routes (Admin Only) ---
    @app.route('/api/v1/users', methods=['GET'])
    @admin_required()
    def list_users():
        users = User.query.all()
        return jsonify([
            {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
            for u in users
        ])

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
        # Add a check to prevent admin from deleting themselves
        current_user_id = get_jwt_identity()['id']
        if user.id == current_user_id:
            return jsonify({"error": "Admin cannot delete themselves"}), 403

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user.username} deleted successfully."})

    return app

# --- Main Execution ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
