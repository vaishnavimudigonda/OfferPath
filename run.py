import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from app.models import db

# Determine environment
env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

# Ensure database tables exist automatically
with app.app_context():
    try:
        db.create_all()
        print("[OfferPath] Database schema verified/initialized successfully.")
    except Exception as e:
        print(f"[OfferPath Warning] Database initialization check: {e}")
        print("[OfferPath Warning] Ensure PostgreSQL is running or verify DATABASE_URL in .env.")

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = env == "development"

    print("=" * 65)
    print(" OFFERPATH – JOB APPLICATION INTELLIGENCE PLATFORM")
    print("=" * 65)
    print(f" * Server running on: http://{host}:{port}/")
    print(f" * API Health Check:  http://{host}:{port}/api/health")
    print(f" * Environment:       {env}")
    print(f" * Database URI:      {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print("=" * 65)
    print(" Press CTRL+C to quit.\n")

    app.run(host=host, port=port, debug=debug)
