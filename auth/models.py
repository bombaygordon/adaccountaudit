from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    agency_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    facebook_credentials = db.Column(db.JSON)
    
    # Define the relationship with clients
    clients = db.relationship('Client', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    website = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Client {self.name}>'

# You could add more models here for storing audit history
class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(50))
    potential_savings = db.Column(db.Float)
    potential_improvement = db.Column(db.Float)
    report_path = db.Column(db.String(200))
    
    # Relationships
    client = db.relationship('Client', backref=db.backref('audits', lazy=True))
    user = db.relationship('User', backref=db.backref('audits', lazy=True))
    
    def __repr__(self):
        return f'<Audit {self.id} for {self.client.name}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'), nullable=False)
    type = db.Column(db.String(50))
    text = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(50))
    priority = db.Column(db.Integer)
    implemented = db.Column(db.Boolean, default=False)
    
    # Relationship
    audit = db.relationship('Audit', backref=db.backref('recommendations', lazy=True))
    
    def __repr__(self):
        return f'<Recommendation {self.id}>'