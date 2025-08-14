from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database extension
db = SQLAlchemy()

# --- Database Models ---

class User(db.Model):
    """Represents a user of the application."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # e.g., 'user', 'admin'
    settings = db.Column(db.JSON, nullable=True) # To store user-specific settings

    def set_password(self, password):
        """Creates a hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self): return f'<User {self.username}>'

class LLMModel(db.Model):
    """Represents a downloaded Large Language Model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    # This will now store the GPT4All model filename, not a Hugging Face ID
    filename = db.Column(db.String(200), unique=True, nullable=False)
    path = db.Column(db.String(300), nullable=True)
    def __repr__(self): return f'<LLMModel {self.name}>'

class CapturedError(db.Model):
    """Represents a runtime error captured by the application."""
    id = db.Column(db.Integer, primary_key=True)
    traceback = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    line_number = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='new') # new, analyzing, analyzed, fixed
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    analysis = db.Column(db.Text, nullable=True) # Explanation from the LLM
    proposed_fix = db.Column(db.Text, nullable=True) # Diff from the LLM

    def __repr__(self):
        return f'<CapturedError {self.id} at {self.file_path}:{self.line_number}>'

class Conversation(db.Model):
    """Represents a single chat conversation."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('llm_model.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('conversations', lazy=True, cascade="all, delete-orphan"))
    model = db.relationship('LLMModel', backref=db.backref('conversations', lazy=True))
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'

class ChatMessage(db.Model):
    """Represents a single message within a conversation."""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<ChatMessage {self.id} from {self.role}>'
