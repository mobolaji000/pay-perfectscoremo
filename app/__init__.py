from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap


print("about to import server")

server = Flask(__name__)
server.config.from_object(Config)
db = SQLAlchemy(server)
from app import views, models
migrate = Migrate(server, db)
bootstrap = Bootstrap(server)






