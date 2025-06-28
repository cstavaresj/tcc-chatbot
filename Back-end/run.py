import logging
from app import create_app
from waitress import serve

app = create_app()

if __name__ == "__main__":
    logging.info("Flask app started")
    #app.run(host="0.0.0.0", port=8000)
    serve(app, host="0.0.0.0", port=8000)
