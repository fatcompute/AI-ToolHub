import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
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
        UPLOAD_FOLDER=os.path.join(basedir, 'datasets')
    )
    if config_overrides:
        app.config.update(config_overrides)

    # --- Initialize Extensions and Register Blueprints/Routes ---
    db.init_app(app)
    Migrate(app, db) # Initialize Flask-Migrate

    # Import services and routes inside the factory
    import backend.llm_service as llm_service

    # --- API Routes ---
    @app.route("/api/v1")
    def index():
        return {"message": "Flask backend is running!"}

    # LLM Model Routes
    @app.route("/api/v1/models", methods=['GET'])
    def get_models():
        models = llm_service.list_local_models()
        return jsonify([{"id": m.id, "name": m.name, "huggingface_id": m.huggingface_id, "status": m.status} for m in models])

    @app.route("/api/v1/models/download", methods=['POST'])
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
    def list_datasets():
        datasets = Dataset.query.all()
        return jsonify([{"id": ds.id, "filename": ds.filename, "created_at": ds.created_at.isoformat()} for ds in datasets])

    @app.route('/api/v1/datasets/upload', methods=['POST'])
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
    def get_job(job_id):
        job = TrainingJob.query.get_or_404(job_id)
        return jsonify({
            "id": job.id, "status": job.status, "logs": job.logs,
            "metrics": job.metrics, # Return the structured metrics
            "model_name": job.model.name, "dataset_name": job.dataset.filename
        })

    @app.route('/api/v1/jobs/start', methods=['POST'])
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

    return app

# --- Main Execution ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
