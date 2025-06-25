
from flask import Flask
from config import Config
from extensions import mysql
from auth.routes import auth_bp
from consultas.routes import consultas_bp
from gestion_usuarios.routes import gestion_usuarios_bp
from gestion_autorizados.routes import gestion_autorizados_bp
from reportes.routes import reportes_bp
from gestion_db.routes import gestion_db_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    mysql.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(consultas_bp)
    app.register_blueprint(gestion_usuarios_bp)
    app.register_blueprint(gestion_autorizados_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(gestion_db_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0')