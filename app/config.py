import os
from app.aws import AWSInstance
import stripe
import plaid
basedir = os.path.abspath(os.path.dirname(__file__))
awsInstance = AWSInstance()
class Config(object):
    try:
        if os.environ['DEPLOY_REGION'] == 'local':

            os.environ["stripe_pk"] = 'pk_test_51Hlgy6DbpRMio7qjWV9YNuBPiQIgD6PrBwO7oek37OEafhZiRjkfs42owvLto0eO8c6CCaiSAOUrXn0uPEJdai6Z00DUYXi551'
            os.environ["price"] = "price_1KDfOQDbpRMio7qjiBfLpZ9g"
            os.environ["product"] = "prod_KtSJDRtkxqsmbr"
            os.environ["url_to_start_reminder"] = "http://127.0.0.1:5002/"
            flask_secret_key = os.environ.get('flask_secret_key')
            SECRET_KEY = os.environ.get('flask_secret_key')
            dbUserName = os.environ.get('dbUserNameLocal')
            dbPassword = os.environ.get('dbPasswordLocal')
            SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://'+str(dbUserName)+':'+str(dbPassword)+'@host/mobolajioo'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            stripe.api_key = os.environ.get('stripe_api_key_test')
            plaid_client_id = os.environ.get('dev_plaid_client_id')
            plaid_secret = os.environ.get('dev_plaid_secret')
            plaidClient = plaid.Client(client_id=plaid_client_id, secret=plaid_secret, environment='sandbox')

        elif os.environ['DEPLOY_REGION'] == 'dev':

            os.environ["stripe_pk"] = 'pk_test_51Hlgy6DbpRMio7qjWV9YNuBPiQIgD6PrBwO7oek37OEafhZiRjkfs42owvLto0eO8c6CCaiSAOUrXn0uPEJdai6Z00DUYXi551'
            os.environ["price"] = "price_1KDfOQDbpRMio7qjiBfLpZ9g"
            os.environ["product"] = "prod_KtSJDRtkxqsmbr"
            os.environ["url_to_start_reminder"] = "https://dev-pay-perfectscoremo-7stpz.ondigitalocean.app/"
            flask_secret_key = awsInstance.get_secret("vensti_admin", "flask_secret_key")
            SECRET_KEY = awsInstance.get_secret("vensti_admin", "flask_secret_key")
            dbUserName = awsInstance.get_secret("do_db_cred", "dev_username")
            dbPassword = awsInstance.get_secret("do_db_cred", "dev_password")
            SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://'+str(dbUserName)+':'+str(dbPassword)+'@app-27fee962-3fa3-41cb-aecc-35d29dbd568e-do-user-9096158-0.b.db.ondigitalocean.com:25060/db'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            stripe.api_key = awsInstance.get_secret("stripe_cred", "stripe_api_key_test")
            plaid_client_id = awsInstance.get_secret("plaid_cred", "dev_plaid_client_id")
            plaid_secret = awsInstance.get_secret("plaid_cred", "dev_plaid_secret")
            plaidClient = plaid.Client(client_id=plaid_client_id, secret=plaid_secret, environment='sandbox')

        elif os.environ['DEPLOY_REGION'] == 'prod':

            os.environ["stripe_pk"] = 'pk_live_51Hlgy6DbpRMio7qjB3uZkis2sPMKb6HmXUI8k5PNKvYgOK1jv2XfzqG5fNaRbEO68wJ7VaXXvISCKIF7Yj2rT01t00GFzi1FkX'
            os.environ["price"] = "price_1I3joBDbpRMio7qj78mNjIDr"
            os.environ["product"] = "prod_If3w0tfPuQpn52"
            os.environ["url_to_start_reminder"] = "https://pay.perfectscoremo.com/"
            flask_secret_key = awsInstance.get_secret("vensti_admin", "flask_secret_key")
            SECRET_KEY = awsInstance.get_secret("vensti_admin", "flask_secret_key")
            dbUserName = awsInstance.get_secret("do_db_cred", "username")
            dbPassword = awsInstance.get_secret("do_db_cred", "password")
            SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://' + str(dbUserName) + ':' + str(dbPassword) + '@app-36443af6-ab5a-4b47-a64e-564101e951d6-jul-29-backup-do-user.b.db.ondigitalocean.com:25060/defaultdb'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            stripe.api_key = awsInstance.get_secret("stripe_cred", "stripe_api_key_prod")
            plaid_client_id = awsInstance.get_secret("plaid_cred", "plaid_client_id")
            plaid_secret = awsInstance.get_secret("plaid_cred", "plaid_secret")
            plaidClient = plaid.Client(client_id=plaid_client_id, secret=plaid_secret, environment='development')

    except Exception as e:
        print("error in initialization")
        print(e)
        #trigger10

