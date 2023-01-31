import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

server = Flask(__name__)
server.config.from_object(Config)
db = SQLAlchemy(server)
#db = SQLAlchemy(server,engine_options={"pool_pre_ping": True},session_options={'expire_on_commit': False})
from app import views, models
migrate = Migrate(server, db)
bootstrap = Bootstrap(server)


#ADDED TO TURN DOUBLE FLASK LOGGING OFF FLASK LOCAL
from flask.logging import default_handler
server.logger.removeHandler(default_handler)
server.logger.handlers.clear()











