import os
from dotenv import load_dotenv
from app import create_app

# Memuat .env sebelum aplikasi dibuat
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Konfigurasi server
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 8021))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print("-" * 30)
    print(f"🚀 API Server is running!")
    print(f"🔗 Local URL: http://localhost:{port}")
    print(f"📄 Documentation: http://localhost:{port}/apidocs/")
    print("-" * 30)
    
    app.run(host=host, port=port, debug=debug)