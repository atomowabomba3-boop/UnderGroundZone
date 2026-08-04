"""
Start Flask application for UnderGroundZone
Entry point for Railway deployment
"""

import os
from api import app
from database import init_db

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get configuration from environment
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run application
    app.run(host='0.0.0.0', port=port, debug=debug)
