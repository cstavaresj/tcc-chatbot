from flask import Flask
from flask_cors import CORS
from app.config import load_configurations, configure_logging

def create_app():
    """
    Cria e configura a instância principal da aplicação Flask.
    Este é o padrão de "Application Factory".
    """
    app = Flask(__name__)    
    
    load_configurations(app)
    configure_logging()
    
    CORS(app, resources={r"/chat": {"origins": "https://chat.tavaresj.com.br"}})
    #CORS(app)
    
    from .views import webhook_blueprint 
    app.register_blueprint(webhook_blueprint)
    
    return app