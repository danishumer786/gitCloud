from app import app
import os

# This file is for Azure App Service deployment
# The 'app' variable is what gunicorn looks for

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)