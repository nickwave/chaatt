from app import create_app, socketio
import os


if __name__ == '__main__':
    app = create_app(debug=False)
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
