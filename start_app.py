#!/usr/bin/env python3
"""
Simple script to start the Tickety app with proper output
"""

if __name__ == "__main__":
    print("🚀 Starting Tickety App...")
    
    try:
        import app
        print("✅ App module imported successfully")
        
        print("🌐 Starting Flask server...")
        print("📍 URL: http://localhost:5000")
        print("🔧 Debug mode: ON")
        print("⏹️  Press Ctrl+C to stop")
        print("-" * 50)
        
        # Start the Flask app
        app.app.run(host="127.0.0.1", port=5000, debug=True)
        
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        print(f"Error type: {type(e)}")
    finally:
        print("🛑 App stopped")
