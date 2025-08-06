from app import db
from datetime import datetime
from typing import Optional


class Inscription(db.Model):
    """Model for ENCCEJA inscription data"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Address Information
    cep = db.Column(db.String(10))
    street = db.Column(db.String(255))
    number = db.Column(db.String(20))
    complement = db.Column(db.String(255))
    neighborhood = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(2))
    
    # Inscription Details
    exam_areas = db.Column(db.Text)  # JSON string of selected exam areas
    education_level = db.Column(db.String(50))
    birth_date = db.Column(db.Date)
    
    # Payment Information
    payment_amount = db.Column(db.Numeric(10, 2), default=93.40)
    payment_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    transaction_id = db.Column(db.String(100), unique=True, index=True)
    payment_method = db.Column(db.String(20), default='pix')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_completed_at = db.Column(db.DateTime)
    
    # Session tracking
    session_id = db.Column(db.String(255), index=True)
    
    def __repr__(self):
        return f'<Inscription {self.cpf} - {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'cpf': self.cpf,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'cep': self.cep,
            'street': self.street,
            'number': self.number,
            'complement': self.complement,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'state': self.state,
            'exam_areas': self.exam_areas,
            'education_level': self.education_level,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'payment_amount': float(self.payment_amount) if self.payment_amount else None,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'payment_completed_at': self.payment_completed_at.isoformat() if self.payment_completed_at else None
        }


class PaymentLog(db.Model):
    """Model for tracking payment attempts and responses"""
    id = db.Column(db.Integer, primary_key=True)
    
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False, index=True)
    
    # Payment gateway details
    gateway_name = db.Column(db.String(50), nullable=False)  # 'witepay', 'for4', etc.
    gateway_order_id = db.Column(db.String(100))
    gateway_response = db.Column(db.Text)  # JSON string of gateway response
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='BRL')
    status = db.Column(db.String(20), nullable=False)  # created, processing, completed, failed
    
    # QR Code data
    pix_key = db.Column(db.String(255))
    qr_code_data = db.Column(db.Text)
    qr_code_base64 = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    inscription = db.relationship('Inscription', backref=db.backref('payment_logs', lazy=True))
    
    def __repr__(self):
        return f'<PaymentLog {self.transaction_id} - {self.status}>'


class SMSVerification(db.Model):
    """Model for SMS verification codes"""
    id = db.Column(db.Integer, primary_key=True)
    
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # SMS details
    verification_code = db.Column(db.String(10), nullable=False)
    sms_provider = db.Column(db.String(50), nullable=False)  # 'smsdev', 'owen', etc.
    sms_response = db.Column(db.Text)  # JSON string of SMS provider response
    
    # Status and validation
    status = db.Column(db.String(20), default='sent')  # sent, verified, expired, failed
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime)
    
    # Relationship
    inscription = db.relationship('Inscription', backref=db.backref('sms_verifications', lazy=True))
    
    def __repr__(self):
        return f'<SMSVerification {self.phone} - {self.status}>'
    
    def is_expired(self):
        """Check if verification code is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if verification is still valid"""
        return not self.is_expired() and self.status == 'sent' and self.attempts < self.max_attempts


class AuditLog(db.Model):
    """Model for audit logging of important actions"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # 'inscription_created', 'payment_completed', etc.
    entity_type = db.Column(db.String(50), nullable=False)  # 'inscription', 'payment', etc.
    entity_id = db.Column(db.Integer, nullable=False)
    
    # Context
    user_ip = db.Column(db.String(45))  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500))
    session_id = db.Column(db.String(255))
    
    # Data
    old_data = db.Column(db.Text)  # JSON string of previous state
    new_data = db.Column(db.Text)  # JSON string of new state
    
    # Additional context
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} - {self.entity_type}:{self.entity_id}>'