from flask_sqlalchemy import SQLAlchemy

# Initialize the database extension
db = SQLAlchemy()

# --- Database Models ---

class User(db.Model):
    """Represents a user of the application."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    def __repr__(self): return f'<User {self.username}>'

class LLMModel(db.Model):
    """Represents a downloaded Large Language Model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    huggingface_id = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    path = db.Column(db.String(300), nullable=True)
    def __repr__(self): return f'<LLMModel {self.name}>'

class Dataset(db.Model):
    """Represents an uploaded dataset for training."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    path = db.Column(db.String(300), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    def __repr__(self): return f'<Dataset {self.filename}>'

class TrainingJob(db.Model):
    """Represents a fine-tuning job for an LLM."""
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('llm_model.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    logs = db.Column(db.Text, nullable=True)
    metrics = db.Column(db.JSON, nullable=True) # To store structured metrics
    model = db.relationship('LLMModel', backref=db.backref('training_jobs', lazy=True))
    dataset = db.relationship('Dataset', backref=db.backref('training_jobs', lazy=True))
    def __repr__(self): return f'<TrainingJob {self.id}>'
