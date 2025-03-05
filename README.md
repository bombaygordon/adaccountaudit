# Ad Account Auditor

A powerful tool for auditing and analyzing Facebook ad accounts using AI-powered insights.

## Features

- Real-time Facebook Ads data analysis
- AI-powered recommendations using OpenAI GPT-4
- Detailed conversion tracking analysis
- Performance metrics and ROAS optimization
- Campaign hierarchy visualization
- Comprehensive audit reports

## Project Structure

```
ad-account-auditor/
├── api/                    # API endpoints
│   ├── __init__.py
│   └── routes.py          # API route handlers
├── analysis/              # Analysis modules
│   ├── __init__.py
│   ├── analyzer.py        # Base analyzer
│   ├── ai_analyzer.py     # AI analysis implementation
│   ├── openai_analyzer.py # OpenAI-specific analyzer
│   └── enhanced_analyzer.py # Enhanced analysis features
├── auth/                  # Authentication
├── connectors/           # Platform connectors
├── web/                  # Web interface
├── static/               # Static assets
├── app.py               # Main application
├── config.py            # Configuration
└── requirements.txt     # Dependencies
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with required credentials:
   ```
   OPENAI_API_KEY=your_openai_key
   FACEBOOK_APP_ID=your_fb_app_id
   FACEBOOK_APP_SECRET=your_fb_app_secret
   FLASK_SECRET_KEY=your_flask_secret
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `FACEBOOK_APP_ID`: Facebook App ID
- `FACEBOOK_APP_SECRET`: Facebook App Secret
- `FLASK_SECRET_KEY`: Flask session secret key
- `FLASK_ENV`: Development/production environment
- `DATABASE_URL`: Database connection string (if using external database)

## API Endpoints

### Facebook Audit
- `POST /api/audit/facebook`
  - Performs AI-powered audit of Facebook ad account
  - Requires Facebook access token and account ID
  - Returns detailed analysis and recommendations

### Campaign Hierarchy
- `POST /api/campaign-hierarchy`
  - Retrieves full campaign structure with performance metrics
  - Includes conversion data and ROAS analysis

## Development

1. Enable debug mode:
   ```bash
   $env:FLASK_DEBUG=1  # PowerShell
   export FLASK_DEBUG=1  # Unix
   python app.py
   ```

2. Run tests:
   ```bash
   python -m pytest test_enhanced_audit.py
   ```

## Dependencies

- Flask 2.3.3
- OpenAI 1.12.0
- Facebook Business SDK 17.0.0
- SQLAlchemy 2.0.25
- Additional dependencies in requirements.txt

## Security Notes

- Store sensitive credentials in environment variables
- Use HTTPS in production
- Implement rate limiting for API endpoints
- Follow Facebook's data usage and privacy guidelines

## License

MIT License - See LICENSE file for details 