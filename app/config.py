import os
from app.aws import AWSInstance
import stripe
import plaid
basedir = os.path.abspath(os.path.dirname(__file__))
awsInstance = AWSInstance()
class Config(object):
    try:
        flask_secret_key = awsInstance.get_secret("vensti_admin","flask_secret_key") or None
        SECRET_KEY = awsInstance.get_secret("vensti_admin","flask_secret_key") or os.environ.get('flask_secret_key')
        dbUserName = awsInstance.get_secret("rds_cred", "username") or os.environ.get('dbUserName')
        dbPassword = awsInstance.get_secret("rds_cred", "password") or os.environ.get('dbPassword')
        SQLALCHEMY_DATABASE_URI = os.environ.get('local_sql_lite','') + os.path.join(basedir, 'app.db') if os.environ.get('local_sql_lite','') != ''  else 'postgresql+psycopg2://'+str(dbUserName)+':'+str(dbPassword)+'@crypto-tech.cq3vpja6t0sd.us-east-2.rds.amazonaws.com:5432/cryptoTechDB'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        stripe.api_key = awsInstance.get_secret("stripe_cred", "stripe_api_key") or os.environ.get('stripe_api_key')
        plaid_client_id = awsInstance.get_secret("plaid_cred", "plaid_client_id") or os.environ.get('plaid_client_id')
        plaid_secret = awsInstance.get_secret("plaid_cred", "plaid_secret") or os.environ.get('plaid_secret')
        plaidClient = plaid.Client(client_id=plaid_client_id,secret=plaid_secret,environment='development')
    except Exception as e:
        print("error in initialization")
        print(e)
        #trigger10

