# PIX Payment System

## Overview
This project is a Flask-based Brazilian PIX payment system that simulates loan/credit applications and payment processing. It integrates multiple payment gateways, features SMS verification, and includes domain restriction capabilities. The system mimics official Brazilian government interfaces like ENCCEJA and Receita Federal for user registration and payment flows, aiming to provide a realistic user experience for financial transactions. The project has market potential in the financial technology sector, particularly in Brazil, by streamlining digital payment and credit application processes.

## User Preferences
Preferred communication style: Simple, everyday language.
Deployment preference: Hostinger hosting instead of Heroku, requires NPM build process for static assets.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework).
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM integration.
- **Session Management**: Secure Flask sessions with random secret keys.
- **Environment Configuration**: `python-dotenv` for managing environment variables.
- **Logging**: Python's built-in logging module for monitoring and debugging.

### Frontend Architecture
- **Templating**: Jinja2 templates using shared resources.
- **Styling**: TailwindCSS for responsive design.
- **Icons**: Font Awesome for UI elements.
- **Fonts**: Custom Rawline and CAIXA fonts for brand consistency.
- **JavaScript**: Vanilla JavaScript for form validation and user interactions.

### Security Features
- **Domain Restriction**: Referrer-based access control with configurable enforcement.
- **Device Detection**: Mobile-only access with desktop blocking.
- **Bot Protection**: User agent detection to prevent automated access.
- **Session Security**: Secure session management with random secret generation.

### Key Components
- **Payment Gateway Integration**: Supports multiple gateways (e.g., FreePay) with a factory pattern for configurable selection and PIX QR code generation.
- **SMS Verification System**: Supports multiple providers (e.g., SMSDEV, OWEN) with configurable selection for secure code generation and validation.
- **Template System**: Simulates government interfaces (ENCCEJA, Receita Federal) with responsive design and shared components.
- **Data Processing**: Includes Brazilian CPF validation, automatic email generation, and phone number formatting.

### Data Flow
The system supports a multi-step user flow including CPF-based user lookup, form submission, payment processing via external gateways, optional SMS verification, and real-time payment confirmation.

### Database Schema
**PostgreSQL Database with Flask-SQLAlchemy Integration**

**Tables:**
- `inscription`: Stores ENCCEJA registration data including personal information, address, exam preferences, and payment status
- `payment_log`: Tracks payment attempts, gateway responses, PIX QR codes, and transaction statuses
- `sms_verification`: Manages SMS verification codes with expiration and attempt tracking
- `audit_log`: Records important actions and state changes for compliance and debugging

**Key Features:**
- Automatic table creation on startup
- Foreign key relationships for data integrity
- Indexed fields for performance (CPF, transaction_id, session_id)
- Timestamp tracking for all major operations
- Support for JSON data storage in text fields

## External Dependencies

### Payment Gateways
- **FreePay**: Primary PIX payment processing gateway using Basic Authentication with secret key.

### SMS Services
- **SMSDEV**: SMS verification provider.
- **OWEN**: Alternative SMS verification provider.

### Third-Party Services
- **Facebook Pixel**: Analytics and conversion tracking.
- **Microsoft Clarity**: User behavior analytics.
- **QR Code Libraries**: For generating payment QR codes.
- **consulta.fontesderenda.blog**: CPF consultation API.

### Required Packages
- `Flask` (web framework)
- `Flask-SQLAlchemy` (ORM for PostgreSQL integration)
- `Gunicorn` (WSGI server)
- `psycopg2-binary` (PostgreSQL driver)
- `Pillow` (PIL - image processing)
- `Requests` (HTTP client)
- `Twilio` (SMS service)
- `python-dotenv` (environment variables)
- `email-validator` (email validation)
- `qrcode` (PIX QR code generation)

## Recent Changes (2025-08-06)

### Payment Gateway Migration: WitePay → FreePay
**Change**: Migrated from WitePay to FreePay API for PIX transactions
**Reason**: User requested switching to FreePay gateway with different authentication mechanism
**Files Modified**:
- Created `freepay_gateway.py` - New FreePay integration with Basic Auth
- Updated `app.py` - Replaced WitePay functions with FreePay integration
- Removed `witepay_gateway.py` - Legacy WitePay integration

**Technical Details**:
- FreePay uses Basic Authentication (SECRET_KEY:x encoded in base64)
- Single API call for PIX transaction creation (simpler than WitePay's order→charge flow)
- Uses FreePay API endpoint: https://api.freepaybr.com/functions/v1/transactions
- Credentials: SECRET_KEY = sk_live_pGalAgvdrYzpdoaBqmWJH3iOb2uqi9cA1jlJXTfEWfqwCw9a
- Optional COMPANY_ID available if needed: 8187dded-16f6-428a-bfe1-8917ec32f3e0

**Impact**: 
- Simplified payment flow (one API call instead of two)
- Maintains same user experience with PIX QR codes
- Updated error handling for FreePay response format