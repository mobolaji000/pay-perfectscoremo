from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap



server = Flask(__name__)
server.config.from_object(Config)
db = SQLAlchemy(server,engine_options={"pool_pre_ping": True})
from app import views, models
migrate = Migrate(server, db)
bootstrap = Bootstrap(server)






