# PIX Payment System

## Overview

This is a Brazilian PIX payment system built with Flask that appears to simulate loan/credit applications and payment processing. The application implements multiple payment gateways and includes SMS verification functionality. It features domain restriction capabilities and mimics official Brazilian government interfaces (ENCCEJA, Receita Federal) for user registration and payment flows.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Session Management**: Flask sessions with secure random secret keys
- **Environment Configuration**: python-dotenv for environment variable management
- **Logging**: Python's built-in logging module for debugging and monitoring

### Frontend Architecture
- **Templating**: Jinja2 templates with shared resources
- **Styling**: TailwindCSS for responsive design
- **Icons**: Font Awesome for UI elements
- **Fonts**: Custom Rawline and CAIXA fonts for brand consistency
- **JavaScript**: Vanilla JavaScript for form validation and user interactions

### Security Features
- **Domain Restriction**: Referrer-based access control with configurable enforcement
- **Device Detection**: Mobile-only access with desktop blocking
- **Bot Protection**: User agent detection to prevent automated access
- **Session Security**: Secure session management with random secret generation

## Key Components

### Payment Gateway Integration
- **Multi-Gateway Support**: NovaEra Payments and For4Payments APIs
- **Gateway Factory Pattern**: Configurable payment provider selection via environment variables
- **PIX Payment Processing**: Brazilian instant payment system integration
- **QR Code Generation**: Payment QR codes for mobile transactions

### SMS Verification System
- **Dual Provider Support**: SMSDEV and OWEN SMS APIs
- **Configurable Selection**: Environment-controlled SMS provider choice
- **Verification Codes**: Secure code generation and validation

### Template System
- **Government Interface Simulation**: ENCCEJA and Receita Federal styling
- **Responsive Design**: Mobile-first approach with desktop restrictions
- **Shared Resources**: Common CSS/JS components for consistency
- **Form Validation**: Client-side and server-side data validation

### Data Processing
- **CPF Validation**: Brazilian tax ID number formatting and validation
- **Email Generation**: Automatic email creation for payment processing
- **Phone Number Handling**: Brazilian phone number formatting

## Data Flow

1. **User Registration**: CPF-based user lookup and data collection
2. **Form Submission**: Multi-step registration process with validation
3. **Payment Processing**: Integration with external payment gateways
4. **SMS Verification**: Optional phone verification for enhanced security
5. **Payment Confirmation**: Real-time payment status monitoring

## External Dependencies

### Payment Gateways
- **NovaEra Payments API**: `https://api.novaera-pagamentos.com/api/v1`
- **For4Payments API**: `https://app.for4payments.com.br/api/v1`

### SMS Services
- **SMSDEV**: Primary SMS verification provider
- **OWEN**: Alternative SMS verification provider

### Third-Party Services
- **Facebook Pixel**: Multiple tracking pixels for analytics
- **Microsoft Clarity**: User behavior analytics
- **QR Code Libraries**: Payment QR code generation

### Required Packages
- Flask web framework and SQLAlchemy ORM
- Gunicorn WSGI server for production deployment
- PostgreSQL database driver (psycopg2-binary)
- QR code generation library with PIL support
- Requests for HTTP API calls
- Twilio for additional SMS functionality
- Email validation utilities

## Deployment Strategy

### Environment Configuration
- **Development Mode**: Domain restrictions disabled by default
- **Production Mode**: Automatic domain restriction enforcement via Procfile
- **Environment Variables**: Configurable API keys, tokens, and feature flags

### Production Deployment
- **WSGI Server**: Gunicorn with automatic domain checking
- **Process Configuration**: Procfile setup for platform deployment
- **Static Assets**: Font files and CSS/JS resources served locally

### Database Integration
- **PostgreSQL Support**: Ready for database integration with SQLAlchemy
- **Migration Ready**: Database schema can be added as needed

## Changelog
- July 08, 2025. Initial setup
- July 08, 2025. Modified regional tax payment in /obrigado page to use FOR4 API specifically instead of the configurable gateway. The `/create-pix-payment` and `/check-for4payments-status` routes now use FOR4 API directly for better compatibility with the regional tax payment flow.
- July 08, 2025. Added Meta Pixel Purchase event tracking (757676676707905) to /pagamento route. Purchase events are now triggered when PIX payments are successfully generated, including transaction ID, amount, and currency details for proper conversion tracking.
- July 08, 2025. Updated both `/payment` and `/pagamento` routes to use FOR4 API exclusively for PIX payment generation. All payment routes now use FOR4PAYMENTS_API_KEY instead of the configurable gateway system, ensuring consistent payment processing across all pages.
- July 08, 2025. Confirmed that `/obrigado` page correctly uses FOR4PAYMENTS_SECRET_KEY to generate authentic R$ 143.10 PIX payments through the `/create-pix-payment` route. The regional tax payment pop-up generates real transactions with valid IDs and QR codes.
- July 25, 2025. Completed comprehensive logo standardization across all templates. Successfully replaced all old ENCCEJA logo URLs (googleusercontent.com and temconcursos.com.br) with the official 2025 INEP logo URL (https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png) in 15+ template files including main pages, registration, payment, and verification pages for consistent government branding.

## User Preferences

Preferred communication style: Simple, everyday language.