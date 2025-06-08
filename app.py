from flask import Flask
from api.routes import bp  # импортируем blueprint из routes.py

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.register_blueprint(bp)

if __name__ == '__main__':
    app.run()