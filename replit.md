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
- **Process Configuration**: Procfile setup for platform deployment (legacy Heroku)
- **Hostinger Deployment**: Complete build system with NPM scripts for CSS compilation
- **Static Assets**: Compiled CSS (Tailwind), CAIXA fonts, and optimized resources
- **Build Pipeline**: NPM build → Tailwind CSS compilation → Font copying → Production-ready assets

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
- July 26, 2025. Implemented WitePay payment gateway integration for authentic PIX payment generation. Created witepay_gateway.py with complete order creation and charge generation workflow. Updated /pagamento route to use WitePay API with standardized user data (gerarpagamentos@gmail.com email, (11) 98779-0088 phone, "Receita do Amor" product name, R$ 93.40 amount). System now reads CPF data from registration API and generates real PIX payments through WitePay's /v1/order/create and /v1/charge/create endpoints.
- July 26, 2025. Secured WitePay API integration by moving API key to environment variables. The WITEPAY_API_KEY is now stored as a secret and can be configured in Heroku deployment. Fixed QR code display issues by implementing proper field mapping for frontend compatibility (pix_code/qr_code fields). Updated payment status verification to handle WitePay transactions with 'ch_' prefix correctly.
- July 26, 2025. Implemented UTMFY Google Pixel tracking and WitePay postback validation system. Added Google Pixel ID "6859ccee5af20eab22a408ef" to /pagamento page for conversion tracking. Created /witepay-postback endpoint to receive payment status updates from WitePay API and trigger UTMFY conversion events when payments are confirmed (PAID/COMPLETED/APPROVED status). The system stores payment status in session and validates through postback for accurate conversion tracking.
- July 31, 2025. Prepared complete build system for Hostinger deployment. Created package.json with NPM build scripts, tailwind.config.js for CSS compilation, and comprehensive deployment documentation (HOSTINGER_DEPLOY.md). Built static/css/output.css (8.9KB minified) with embedded Tailwind utilities and custom ENCCEJA styling. Established complete file structure ready for production hosting with environment variable configuration (.env.example) and detailed deployment guide including Python dependencies installation and server configuration.

## User Preferences

Preferred communication style: Simple, everyday language.
Deployment preference: Hostinger hosting instead of Heroku, requires NPM build process for static assets.