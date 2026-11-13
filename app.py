from flask import Flask
from models.database import crear_tablas
from routes.auth import auth
from routes.dashboard import dashboard

app = Flask(__name__)
app.config['SECRET_KEY'] = 'una-clave-secreta'
app.register_blueprint(auth)
app.register_blueprint(dashboard)

crear_tablas()

if __name__ == "__main__":
    app.run(debug=True, port=8080, ssl_context=('cert.pem', 'key.pem'))