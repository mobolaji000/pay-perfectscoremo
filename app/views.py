from flask import render_template, flash, make_response, redirect, url_for, request, jsonify, Response
from werkzeug.urls import url_parse
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
from app.forms import PaymentForm
from app.service import ValidateLogin
from app.service import User
from flask_login import login_user,login_required,current_user,logout_user
import logging
import ast
import time
import json
import os
from app.service import StripeInstance
from app.service import PlaidInstance
from app.service import SendMessagesToClients
import traceback
from app.config import stripe



from app import server
from app.aws import AWSInstance
from app.dbUtil import AppDBUtil
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'admin_login'

server.config.from_object(Config)
server.logger.setLevel(logging.DEBUG)
db = SQLAlchemy(server)
migrate = Migrate(server, db)
awsInstance = AWSInstance()
stripeInstance = StripeInstance()
plaidInstance = PlaidInstance()


@server.route("/")
def hello():
    #server.logger.debug('Processing default request')
    return ("You have landed on the wrong page")

@server.route("/usercode.html")
def usercode():
    name='Mo'
    return render_template('usercode.html', name=name)

@server.route("/health")
def health():
    print("healthy!")
    return render_template('health.html')


@server.route('/validate_login', methods=['POST'])
def validate_login():
    username = request.form.to_dict()['username']
    password = request.form.to_dict()['password']
    validateLogin = ValidateLogin(username, password)
    if validateLogin.validateUserName() and validateLogin.validatePassword():
        flash('login successful')
        user = User(password)
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('client_setup')
        return redirect(next_page)
    else:
        flash('login failed')
        return redirect('/admin-login')

@server.route('/admin-login',methods=['GET','POST'])
def admin_login():
    return render_template('admin.html')

@server.route('/placeholder',methods=['GET', 'POST'])
def placeholder():
    form = PaymentForm()
    if form.validate_on_submit():
        flash('Your information is being processed')
        return redirect(url_for('success'))
    return render_template('admin.html', form=form)


@server.route('/success')
def success():
    return render_template('success.html')

@server.route('/failure')
def failure():
    return render_template('failure.html')

@server.route('/client_setup')
@login_required
def client_setup():
    return render_template('client_setup.html')

@server.route('/create_invoice',methods=['POST'])
@login_required
def create_invoice():
    client_setup_data = request.form.to_dict()
    customer = stripeInstance.createCustomer(client_setup_data)
    client_setup_data.update({"stripe_customer_id":customer["id"]})
    invoice_code = AppDBUtil.createClient(client_setup_data)

    if client_setup_data.get('mark_as_paid','') == 'yes':
        client_info, products_info = AppDBUtil.getInvoiceDetails(invoice_code)
        stripe_info = parseDataForStripe(client_info)
        stripeInstance.markCustomerAsChargedOutsideofStripe(stripe_info)
        AppDBUtil.updateInvoicePaymentStarted(invoice_code)
        print("marked invoice as paid")

    if client_setup_data.get('send_text_and_email','') == 'yes':
        try:
            SendMessagesToClients.sendEmail(to_address='mo@vensti.com',message=invoice_code,type='create')
            #awsInstance.send_email(to_address=client_setup_data['email'])
            SendMessagesToClients.sendSMS(to_number=client_setup_data['phone_number'],message=invoice_code,type='create')
            flash('Invoice created and email/sms sent to client.')
        except Exception as e:
            traceback.print_exc()
            flash('An error occured while sending an email/sms to the client after creating the invoice.')

    return render_template('generate_invoice_code.html',invoice_code=invoice_code)

@server.route('/search_invoice',methods=['POST'])
@login_required
def search_invoice():
    search_query = str(request.form['search_query'])

    try:
        search_results = AppDBUtil.searchInvoices(search_query)
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error has occured during the search.')
        return redirect(url_for('client_setup'))

    if not search_results:
        flash('No invoice has the detail you searched for.')
        return redirect(url_for('client_setup'))

    #print(search_results)
    return render_template('client_setup.html',search_results=search_results)

@server.route('/modify_invoice',methods=['POST'])
@login_required
def modify_invoice():
    try:
        data_to_modify = ast.literal_eval(request.form['data_to_modify'])
        print(data_to_modify)
        invoice_code = data_to_modify['invoice_code']
        AppDBUtil.modifyInvoiceDetails(data_to_modify)

        if data_to_modify.get('send_text_and_email','') == 'yes':
            try:
                SendMessagesToClients.sendEmail(to_address='mo@vensti.com', message=invoice_code,type='modify')
                # awsInstance.send_email(to_address=client_setup_data['email'])
                SendMessagesToClients.sendSMS(to_number=data_to_modify['phone_number'], message=invoice_code,type='modify')
                flash('Invoice modified and email/sms sent to client.')
            except Exception as e:
                traceback.print_exc()
                flash('An error occured while sending an email/sms to the client after modifying the invoice.')
        else:
            flash('Invoice sucessfully modified.')
        return redirect(url_for('client_setup'))
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error occured while modifying the invoice.')
        return redirect(url_for('client_setup'))

    return render_template('client_setup.html')

@server.route('/delete_invoice',methods=['POST'])
@login_required
def delete_invoice():
    try:
        invoice_code_to_delete = str(request.form['invoice_code_to_delete'])
        print(invoice_code_to_delete)
        AppDBUtil.deleteInvoice(invoice_code_to_delete)
        flash('Invoice sucessfully deleted.')
        return redirect(url_for('client_setup'))
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error occured while deleting the invoice.')
        return redirect(url_for('client_setup'))

    return render_template('client_setup.html')

@server.route('/input_invoice_code',methods=['GET'])
def input_invoice_code():
    return render_template('input_invoice_code.html')


@server.route('/invoice_page',methods=['POST'])
def invoice_page():
    try:
        client_info,products_info = AppDBUtil.getInvoiceDetails(request.form.to_dict()['invoice_code'])
    except Exception as e:
        print(e)
        flash('An error has occured. Contact Mo.')
        return redirect(url_for('input_invoice_code'))

    if not client_info and not products_info:
        flash('You might have put in the wrong code. Try again or contact Mo.')
        return redirect(url_for('input_invoice_code'))

    stripe_info = parseDataForStripe(client_info)

    response = make_response(render_template('invoice_page.html', stripe_info=stripe_info, client_info=client_info,products_info=products_info))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"  # HTTP 1.1.
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0.
    response.headers["Expires"] = "0"  # Proxies.

    return response
    #return render_template('invoice_page.html', stripe_info=stripe_info, client_info=client_info,products_info=products_info)

@login_manager.user_loader
def load_user(password):
    return User(awsInstance.get_secret("vensti_admin", 'password'))

@server.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('admin_login'))

@server.route('/checkout',methods=['POST'])
def checkout():
    payment_data = request.form.to_dict()
    chosen_mode_of_payment = payment_data.get('installment-payment', '') if payment_data.get('installment-payment','') != '' else payment_data.get('full-payment', '') if payment_data.get('full-payment', '') != '' else payment_data.get('payment-options', '') if payment_data.get('payment-options', '') != '' else ''
    stripe_info = ast.literal_eval(payment_data['stripe_info'])
    if chosen_mode_of_payment.__contains__('ach'):
        return render_template('plaid_checkout.html',stripe_info=stripe_info)
    else:
        return render_template('stripe_checkout.html', stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment)


def parseDataForStripe(client_info):
    stripe_info = {}
    stripe_info['name'] = client_info['first_name']+" "+client_info['last_name']
    stripe_info['phone_number'] = client_info['phone_number']
    stripe_info['email'] = client_info['email']
    stripe_info['stripe_customer_id'] = client_info['stripe_customer_id']
    stripe_info['invoice_total'] = client_info['invoice_total']
    stripe_info['deposit'] = client_info.get('deposit','')
    stripe_info['invoice_code'] = client_info.get('invoice_code', '')

    if client_info.get('installments','') != '':
        for index,installment in enumerate(client_info.get('installments','')):
            stripe_info["installment_date"+"_"+str(index+1)] = int(time.mktime(installment["installment_date"].timetuple()))
            stripe_info["installment_amount" + "_" + str(index+1)] = installment["installment_amount"]

    return stripe_info

@server.route('/setup_payment_intent',methods=['POST'])
def setup_payment_intent():
    stripe_info = ast.literal_eval(request.form['stripe_info'])
    client_secret = stripeInstance.setUpIntent(stripe_info)
    return jsonify({'client_secret': client_secret})

@server.route('/execute_card_payment',methods=['POST'])
def execute_card_payment():
    chosen_mode_of_payment = request.form['chosen_mode_of_payment']
    stripe_info = ast.literal_eval(request.form['stripe_info'])
    payment_id = request.form['payment_id']
    result = stripeInstance.chargeCustomerViaCard(stripe_info, chosen_mode_of_payment, payment_id)
    if result['status'] == 'failure':
        print("Failed because customer did not enter a credit card number to pay via installments.")
        flash('Enter a credit card number to pay via installments.')
    else:
        AppDBUtil.updateInvoicePaymentStarted(stripe_info['invoice_code'])

    return jsonify(result)

@server.route("/get_link_token", methods=['POST'])
def get_link_token():
        stripe_info = ast.literal_eval(request.form['stripe_info'])
        link_token = plaidInstance.get_link_token(stripe_info['stripe_customer_id'])
        return jsonify({'link_token': link_token})


@server.route("/exchange_plaid_for_stripe", methods=['POST'])
def exchange_plaid_for_stripe():
    # Change sandbox to development to test with live users and change
    # to production when you're ready to go live!
    stripe_info = ast.literal_eval(request.form['stripe_info'])
    public_token = request.form['public_token']
    account_id = request.form['account_id']
    bank_account_token = plaidInstance.exchange_plaid_for_stripe(public_token,account_id)
    stripeInstance.chargeCustomerViaACH(stripe_info,bank_account_token)

    if result['status'] != 'success':
        print("Attempt to pay via ACH failed")
    else:
        AppDBUtil.updateInvoicePaymentStarted(stripe_info['invoice_code'])

    return jsonify({'status': 200})



@server.route("/stripe_webhook", methods=['POST'])
def stripe_webhook():
    payload = json.dumps(request.json)
    #stripe.api_key = awsInstance.get_secret("stripe_cred", "stripe_api_key_test") or os.environ.get('stripe_api_key_test')
    #print("api key is ",stripe.api_key)
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
        print(event)
    except ValueError as e:
        # Invalid payload
        print(e)
        traceback.print_exc()
        return jsonify({'status': 400})

    # Handle the event

    # handle updating the DB when invoices are paid; these invoices should have invoice codes attahced already
    if event.type == 'invoice.paid':
        paid_invoice = event.data.object
        invoice_code = paid_invoice.metadata['invoice_code']
        amount_paid = paid_invoice.total/100

        AppDBUtil.updateAmountPaidAgainstInvoice(invoice_code,amount_paid)


        print("paid invoice is ", paid_invoice)
        print("invoice code is ", invoice_code)

    # attach invoice code to invoices generated from subscriptions
    elif event.type == 'invoice.created':
        created_invoice = event.data.object
        subscription = created_invoice.get('subscription',None)
        if subscription:
            subscription_schedule = stripe.Subscription.retrieve(subscription)['schedule']
            subscription_schedule_metadata = stripe.SubscriptionSchedule.retrieve(subscription_schedule,).metadata
            invoice_code = subscription_schedule_metadata['invoice_code']
            stripe.Invoice.modify(created_invoice['id'],metadata={"invoice_code":invoice_code},)


            print("created invoice is ",created_invoice)
            print("invoice code is ", invoice_code)

    else:
        print('Unhandled event type {}'.format(event.type))

    return jsonify({'status': 200})
