import os
from app.aws import AWSInstance
import stripe
import plaid
basedir = os.path.abspath(os.path.dirname(__file__))
awsInstance = AWSInstance()
class Config(object):
    try:
        flask_secret_key = awsInstance.get_secret("vensti_admin","flask_secret_key") or os.environ.get('flask_secret_key')
        SECRET_KEY = awsInstance.get_secret("vensti_admin","flask_secret_key") or os.environ.get('flask_secret_key')
        dbUserName = awsInstance.get_secret("do_db_cred", "username") or os.environ.get('dbUserName')
        dbPassword = awsInstance.get_secret("do_db_cred", "password") or os.environ.get('dbPassword')
        SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://'+str(dbUserName)+':'+str(dbPassword)+'@app-36443af6-ab5a-4b47-a64e-564101e951d6-do-user-9096158-0.b.db.ondigitalocean.com:25060/db'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        stripe.api_key = awsInstance.get_secret("stripe_cred", "stripe_api_key") or os.environ.get('stripe_api_key')
        plaid_client_id = awsInstance.get_secret("plaid_cred", "plaid_client_id") or os.environ.get('plaid_client_id')
        plaid_secret = awsInstance.get_secret("plaid_cred", "plaid_secret") or os.environ.get('plaid_secret')
        plaidClient = plaid.Client(client_id=plaid_client_id, secret=plaid_secret, environment='sandbox')

    except Exception as e:
        print("error in initialization")
        print(e)
        #trigger10

