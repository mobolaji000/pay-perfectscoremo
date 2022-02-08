from flask import render_template, flash, make_response, redirect, url_for, request, jsonify, Response
from werkzeug.urls import url_parse
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
from app.forms import PaymentForm
from app.service import ValidateLogin
from app.service import User
from flask_login import login_user,login_required,current_user,logout_user
import ast
import time
import json
import os
import math
import uuid
from app.service import StripeInstance
from app.service import PlaidInstance
from app.service import SendMessagesToClients
import traceback
from app.config import stripe
from apscheduler.schedulers.background import BackgroundScheduler

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)

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

@server.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@server.route("/privacy_policy")
def privacy_policy():
    return render_template('privacy_policy.html')

@server.route("/health")
def health():
    print("healthy!")
    return render_template('health.html')

@server.route('/admin-login',methods=['GET','POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin.html')
    elif request.method == 'POST':
        next_page = request.args.get('next')
        username = request.form.to_dict()['username']
        password = request.form.to_dict()['password']
        validateLogin = ValidateLogin(username, password)
        if validateLogin.validateUserName() and validateLogin.validatePassword():
            flash('login successful')
            user = User(password)
            login_user(user)
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('transaction_setup')
            return redirect(next_page)
        else:
            flash('login failed')
            return redirect('/admin-login')

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

@server.route('/error')
def error(error_message):
    return render_template('error.html',error_message=error_message)

@server.route('/failure')
def failure():
    return render_template('failure.html')

@server.route('/transaction_setup')
@login_required
def transaction_setup():
    return render_template('transaction_setup.html')

#keep for when you need to send adhoc student info requests to parents
@server.route('/client_info',defaults={'prospect_id': None}, methods=['GET','POST'])
@server.route('/client_info/<prospect_id>', methods=['GET','POST'])
def client_info(prospect_id):
    if request.method == 'GET':
        print("prospect_id in get is ",prospect_id)
        return render_template('client_info.html',prospect_id=prospect_id)
    elif request.method == 'POST':
        try:
            student_data = request.form.to_dict()
            print("prospect_id in post is ", student_data['prospect_id'])
            print("student data is",student_data)
            AppDBUtil.createStudentData(student_data)
            to_numbers = [number for number in [student_data['parent_1_phone_number'],student_data['parent_2_phone_number'],student_data['student_phone_number']] if number != '']
            SendMessagesToClients.sendGroupSMS(to_numbers=to_numbers, message=student_data['student_first_name'], type='create_group_chat')
            #hold off on sending group emails until you dedcide there is a value add
            #SendMessagesToClients.sendEmail(to_addresses=[student_data['parent_1_email'], student_data['parent_2_email'], student_data['student_email'],'mo@perfectscoremo.com'], message=student_data['student_first_name'], type='create_group_email',subject='Setting Up Group Email')
            #flash("Student information submitted successfully and group messages (email and text) for regular updates created.")
            flash("Student information submitted successfully and text group message for regular updates created.")
        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error in submitting student information and creating group messages for regular updates created. Please contact Mo.")
        return render_template('client_info.html', prospect_id=student_data['prospect_id'])

@server.route('/lead_info', methods=['GET','POST'])
@login_required
def lead_info():
    if request.method == 'GET':
        return render_template('lead_info.html')
    elif request.method == 'POST':
        lead_info_contents = request.form.to_dict()
        print(lead_info_contents)
        action = lead_info_contents['action']

        if action == 'Create':
            try:
                leadInfo = {}
                leadInfo.update({'lead_id': "l-" + str(uuid.uuid4().int >> 64)[:6], 'lead_name': lead_info_contents.get('lead_name', ''), 'lead_email': lead_info_contents.get('lead_email', ''), 'lead_phone_number': lead_info_contents.get('lead_phone_number', ''),
                                 'what_service_are_they_interested_in': lead_info_contents.get('what_service_are_they_interested_in', ''), 'what_next': lead_info_contents.get('what_next', ''),
                                 'meeting_notes_to_keep_in_mind': lead_info_contents.get('meeting_notes_to_keep_in_mind', ''),
                                 'how_did_they_hear_about_us': lead_info_contents.get('how_did_they_hear_about_us', ''), 'how_did_they_hear_about_us_details': lead_info_contents.get('how_did_they_hear_about_us_details', '')})
                AppDBUtil.createLead(leadInfo)
                flash('The lead info was created successfully.')
                return render_template('lead_info.html', action=action)
            except Exception as e:
                print(e)
                traceback.print_exc()
                flash('An error has occured during the creation.')
                return redirect(url_for('lead_info'))

        if action == 'Modify':
            try:
                leadInfo = {}
                leadInfo.update({'lead_name': lead_info_contents.get('lead_name', ''), 'lead_email': lead_info_contents.get('lead_email', ''),
                                 'lead_phone_number': lead_info_contents.get('lead_phone_number', ''),
                                 'what_service_are_they_interested_in': lead_info_contents.get('what_service_are_they_interested_in', ''), 'what_next': lead_info_contents.get('what_next', ''),
                                 'meeting_notes_to_keep_in_mind': lead_info_contents.get('meeting_notes_to_keep_in_mind', ''),
                                 'how_did_they_hear_about_us': lead_info_contents.get('how_did_they_hear_about_us', ''), 'how_did_they_hear_about_us_details': lead_info_contents.get('how_did_they_hear_about_us_details', '')})

                number_of_rows_modified = AppDBUtil.modifyLeadInfo(lead_info_contents.get('lead_id', ''),leadInfo)

                if number_of_rows_modified > 1:
                    print("Somehow ended up with and modified duplicate lead ids")
                    flash('Somehow ended up with and modified duplicate lead ids')

                flash('Lead sucessfully modified.')
                return render_template('lead_info.html', action=action)
            except Exception as e:
                print(e)
                traceback.print_exc()
                flash('An error occured while modifying the lead.')
                return render_template('lead_info.html', action=action)

        if action == 'Search':
            try:
                search_results = {}
                search_results = AppDBUtil.getLeadInfo(lead_info_contents.get('search_query', None), lead_info_contents.get('start_date', None), lead_info_contents.get('end_date', None))
            except Exception as e:
                print(e)
                traceback.print_exc()
                flash('An error has occured during the search.')
                render_template('lead_info.html', action=action)

            if not search_results:
                flash('No lead info has the detail you searched for.')
                render_template('lead_info.html', action=action)

            return render_template('lead_info.html', search_results=search_results, action=action)



@server.route('/create_transaction',methods=['POST'])
@login_required
def create_transaction():
    try:
        transaction_setup_data = request.form.to_dict()
        prospect = AppDBUtil.createProspect(transaction_setup_data)

        customer,does_customer_payment_info_exist = stripeInstance.createCustomer(transaction_setup_data)
        transaction_setup_data.update({"stripe_customer_id":customer["id"],'prospect_id':prospect.prospect_id,'does_customer_payment_info_exist':does_customer_payment_info_exist})
        transaction_id,number_of_rows_modified = AppDBUtil.createOrModifyClientTransaction(transaction_setup_data, action='create')

        client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)
        stripe_info = parseDataForStripe(client_info)

        # stopped using after starting to asking for student info on transaction page
        # if transaction_setup_data.get('ask_for_student_info','') == 'yes':
        #     SendMessagesToClients.sendEmail(to_addresses=transaction_setup_data['email'], message=transaction_setup_data['prospect_id'], subject='New Student Information', type='student_info')
        #     SendMessagesToClients.sendSMS(to_number=transaction_setup_data['phone_number'], message=transaction_setup_data['prospect_id'], type='student_info')
        #     logger.debug('Ask for student info: ' + str(stripe_info['transaction_id']))

        if transaction_setup_data.get('mark_as_paid','') == 'yes':
            stripeInstance.markCustomerAsChargedOutsideofStripe(stripe_info,action='create')
            AppDBUtil.updateTransactionPaymentStarted(transaction_id)
            logger.debug('Mark transaction as paid: '+str(stripe_info['transaction_id']))
        else:
            message_type = ''
            if does_customer_payment_info_exist:
                message_type = 'create_transaction_existing_client'
                logger.debug('Customer info exists so set up autopayment: ' + str(stripe_info['transaction_id']))
                stripeInstance.setupAutoPaymentForExistingCustomer(stripe_info)
            else:
                message_type = 'create_transaction_new_client'

            if transaction_setup_data.get('send_text_and_email', '') == 'yes':
                logger.debug('Send transaction text and email notification: ' + str(stripe_info['transaction_id']))
                try:
                    SendMessagesToClients.sendEmail(to_addresses=transaction_setup_data['email'], message=transaction_id, type=message_type)
                    if message_type == 'create_transaction_existing_client':
                        SendMessagesToClients.sendGroupSMS(to_numbers=[transaction_setup_data['phone_number']], message=transaction_id, type='create_transaction_existing_client')
                        time.sleep(60)
                        SendMessagesToClients.sendGroupSMS(to_numbers=[transaction_setup_data['phone_number']], message=transaction_id, type='questions')
                    else:
                        SendMessagesToClients.sendSMS(to_number=transaction_setup_data['phone_number'], message=transaction_id, type=message_type)
                    flash('Transaction created and email/sms sent to client.')
                except Exception as e:
                    traceback.print_exc()
                    flash('An error occured while sending an email/sms to the client after creating the transaction.')
        return render_template('generate_transaction_id.html',transaction_id=transaction_id,input_transaction_id_url=os.environ.get("url_to_start_reminder")+"input_transaction_id")
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error occured while creating the transaction.')
        return redirect(url_for('transaction_setup'))

@server.route('/search_transaction',methods=['POST'])
@login_required
def search_transaction():
    search_query = str(request.form['search_query'])
    try:
        search_results = AppDBUtil.searchTransactions(search_query)
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error has occured during the search.')
        return redirect(url_for('transaction_setup'))

    if not search_results:
        flash('No transaction has the detail you searched for.')
        return redirect(url_for('transaction_setup'))

    return render_template('transaction_setup.html',search_results=search_results)

@server.route('/modify_transaction',methods=['POST'])
@login_required
def modify_transaction():
    try:
        #print(request.form)
        data_to_modify = ast.literal_eval(request.form['data_to_modify'])
        print(data_to_modify)
        transaction_id = data_to_modify['transaction_id']
        transaction_id_again,number_of_rows_modified=AppDBUtil.modifyTransactionDetails(data_to_modify)

        #stopped using after starting to asking for student info on transaction page
        # if data_to_modify.get('ask_for_student_info','') == 'yes':
        #     SendMessagesToClients.sendEmail(to_addresses=data_to_modify['email'], message=data_to_modify['prospect_id'], subject='New Student Information', type='student_info')
        #     SendMessagesToClients.sendSMS(to_number=data_to_modify['phone_number'], message=data_to_modify['prospect_id'], type='student_info')
        #     logger.debug('Ask for student info: ' + str(data_to_modify['transaction_id']))

        if number_of_rows_modified < 1:
            print("No transaction was modified, perhaps because no transaction code was provided")
            flash('No transaction was modified, perhaps because no transaction code was provided')
            return redirect(url_for('transaction_setup'))

        if number_of_rows_modified > 1:
            print("Somehow ended up with and modified duplicate transaction codes")
            flash('Somehow ended up with and modified duplicate transaction codes')
            return redirect(url_for('transaction_setup'))

        if data_to_modify.get('mark_as_paid', '') == 'yes':
            client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)
            stripe_info = parseDataForStripe(client_info)
            stripeInstance.markCustomerAsChargedOutsideofStripe(stripe_info,action='modify')
            AppDBUtil.updateTransactionPaymentStarted(transaction_id)
            print("marked transaction as paid")

        if data_to_modify.get('send_text_and_email','') == 'yes':
            try:
                SendMessagesToClients.sendEmail(to_addresses=data_to_modify['email'], message=transaction_id, type='modify_transaction')
                SendMessagesToClients.sendSMS(to_number=data_to_modify['phone_number'], message=transaction_id,type='modify_transaction')
                flash('Transaction modified and email/sms sent to client.')
            except Exception as e:
                traceback.print_exc()
                flash('An error occured while sending an email/sms to the client after modifying the transaction.')
        else:
            flash('Transaction sucessfully modified.')
        return redirect(url_for('transaction_setup'))
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error occured while modifying the transaction.')
        return redirect(url_for('transaction_setup'))

    return render_template('transaction_setup.html')

@server.route('/delete_transaction',methods=['POST'])
@login_required
def delete_transaction():
    try:
        transaction_id_to_delete = str(request.form['transaction_id_to_delete'])
        print(transaction_id_to_delete)
        AppDBUtil.deleteTransactionAndInstallmentPlan(transaction_id_to_delete)
        flash('Transaction sucessfully deleted.')
        return redirect(url_for('transaction_setup'))
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error occured while deleting the transaction.')
        return redirect(url_for('transaction_setup'))

    return render_template('transaction_setup.html')

@server.route('/input_transaction_id',methods=['GET'])
def input_transaction_id():
    return render_template('input_transaction_id.html')

@server.route('/transaction_page',methods=['POST'])
def transaction_page():
    try:
        client_info,products_info,showACHOverride = AppDBUtil.getTransactionDetails(request.form.to_dict()['transaction_id'])
    except Exception as e:
        print(e)
        flash('An error has occured. Contact Mo.')
        return redirect(url_for('input_transaction_id'))
    if not client_info and not products_info:
        flash('You might have put in the wrong code. Try again or contact Mo.')
        return redirect(url_for('input_transaction_id'))

    stripe_info = parseDataForStripe(client_info)

    response = make_response(render_template('complete_signup.html', stripe_info=stripe_info, client_info=client_info,products_info=products_info,showACHOverride=showACHOverride,askForStudentInfo=client_info.get('ask_for_student_info','')))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"  # HTTP 1.1.
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0.
    response.headers["Expires"] = "0"  # Proxies.

    return response

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
    stripe_info = ast.literal_eval(payment_data.get('stripe_info', ''))
    stripe_pk = os.environ.get('stripe_pk')
    if chosen_mode_of_payment.__contains__('ach'):
        return render_template('plaid_checkout.html',stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment)
    else:
        return render_template('stripe_checkout.html', stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment,stripe_pk=stripe_pk)


def parseDataForStripe(client_info):
    #rememeber to not add more data here that could  be safely added to client_info or product_info. this seems to have been originally designed
    # to parse specific data in a specifc way that was causing stripe processing to break
    stripe_info = {}
    stripe_info['name'] = client_info['first_name']+" "+client_info['last_name']
    stripe_info['phone_number'] = client_info['phone_number']
    stripe_info['email'] = client_info['email']
    stripe_info['stripe_customer_id'] = client_info['stripe_customer_id']
    stripe_info['transaction_total'] = client_info['transaction_total']
    stripe_info['deposit'] = client_info.get('deposit','')
    stripe_info['transaction_id'] = client_info.get('transaction_id', '')
    stripe_info['installment_counter'] = client_info.get('installment_counter', '')
    stripe_info['ask_for_student_info'] = client_info.get('ask_for_student_info', '')
    stripe_info['does_customer_payment_info_exist'] = client_info.get('does_customer_payment_info_exist', '')
    stripe_info['prospect_id'] = client_info.get('prospect_id', '')

    if client_info.get('installments','') != '':
        for index,installment in enumerate(client_info.get('installments','')):
            stripe_info["date"+"_"+str(index+1)] = int(time.mktime(installment["date"].timetuple()))
            stripe_info["amount" + "_" + str(index+1)] = installment["amount"]

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
    does_customer_payment_info_exist = True if stripe_info.get('does_customer_payment_info_exist','') == 'yes' else False
    result = stripeInstance.chargeCustomerViaCard(stripe_info=stripe_info, chosen_mode_of_payment=chosen_mode_of_payment, payment_id=payment_id,existing_customer=does_customer_payment_info_exist)
    if result['status'] != 'success':
        print("Stripe card payment failed")
        flash('Payment failed. Enter a valid credit/debit card number. Or contact Mo.')
    else:
        AppDBUtil.updateTransactionPaymentStarted(stripe_info['transaction_id'])

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
    chosen_mode_of_payment = request.form['chosen_mode_of_payment']
    bank_account_token = plaidInstance.exchange_plaid_for_stripe(public_token,account_id)
    does_customer_payment_info_exist = True if stripe_info.get('does_customer_payment_info_exist','') == 'yes' else False
    result = stripeInstance.chargeCustomerViaACH(stripe_info=stripe_info,bank_account_token=bank_account_token,chosen_mode_of_payment=chosen_mode_of_payment,existing_customer=does_customer_payment_info_exist)

    if result['status'] != 'success':
        print("Attempt to pay via ACH failed")
        result = {'status': 400}
    else:
        AppDBUtil.updateTransactionPaymentStarted(stripe_info['transaction_id'])
        result = {'status': 200}

    return jsonify(result)



@server.route("/stripe_webhook", methods=['POST'])
def stripe_webhook():
    payload = json.dumps(request.json)
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
        print("Event is: ")
        print(event)
    except ValueError as e:
        # Invalid payload
        print("400 error from calling webhook. Check code and logs")
        print(e)
        traceback.print_exc()
        return jsonify({'status': 400})

    # Handle the event

    # handle updating the DB when transactions are paid; these transactions should have transaction codes attahced already
    try:
        #if necessary, handle charge.succeeded and charge.failed, which are specific to ach
        #https://stripe.com/docs/ach#ach-specific-webhook-notifications
        if event.type == 'invoice.paid':
            paid_invoice = event.data.object
            transaction_id = paid_invoice.metadata['transaction_id']

            payment_type = ''
            if paid_invoice.payment_intent:
                payment_intent = stripe.PaymentIntent.retrieve(paid_invoice.payment_intent,)
                payment_method = stripe.PaymentMethod.retrieve(str(payment_intent['payment_method']),)
                payment_type = str(payment_method['type'])

            # consider replacing above with this if there are further errors
            # payment_intent = stripe.PaymentIntent.retrieve(paid_invoice.payment_intent, ) if paid_invoice.payment_intent else None
            # payment_method = stripe.PaymentMethod.retrieve(payment_intent['payment_method'], ) if payment_intent else None
            # payment_type = payment_method['type'] if payment_method else None

            if payment_type == 'card':
                amount_paid = int(math.floor(paid_invoice.total/103))
            else:
                amount_paid = paid_invoice.total / 100

            AppDBUtil.updateInvoiceAsPaid(paid_invoice.id)
            AppDBUtil.updateAmountPaidAgainstTransaction(transaction_id,amount_paid)
            AppDBUtil.updateTransactionPaymentStarted(transaction_id)

            print("paid transaction is ", paid_invoice)
            print("transaction id is ", transaction_id)

        elif event.type == 'invoice.payment_failed':
            failed_invoice = event.data.object
            try:
                message = "Invoice "+str(failed_invoice.id)+" for "+str(failed_invoice.customer_name)+" failed to pay."
                #SendMessagesToClients.sendEmail(to_addresses='mo@prepwithmo.com', message=message, type='to_mo')
                SendMessagesToClients.sendSMS(to_number='9725847364', message=message, type='to_mo')
                print(message)
            except Exception as e:
                print(e)
                traceback.print_exc()
        else:
            print('Unhandled event type {}'.format(event.type))
    except Exception as e:
        print("500 error from calling webhook. Check code and logs")
        print(e)
        traceback.print_exc()
        return jsonify({'status': 500})

    return jsonify({'status': 200})


@server.before_first_request
def start_background_jobs_before_first_request():
    def reminders_background_job():
        try:
            print("Reminders background job started")
            reminder_last_names = ''
            clientsToReceiveReminders = AppDBUtil.findClientsToReceiveReminders()
            for client in clientsToReceiveReminders:
                SendMessagesToClients.sendEmail(to_addresses=client['email'], message=client['transaction_id'], type='reminder_to_make_payment')
                SendMessagesToClients.sendSMS(to_number=client['phone_number'], message=client['transaction_id'],type='reminder_to_make_payment')
                reminder_last_names = reminder_last_names+client['last_name']+", "
            SendMessagesToClients.sendSMS(to_number='9725847364', message=reminder_last_names, type='to_mo')

        except Exception as e:
            print("Error in sending reminders")
            print(e)
            traceback.print_exc()

    def invoice_payment_background_job():
        print("Invoice payment background job started")
        try:
            invoicesToPay = AppDBUtil.findInvoicesToPay()

            for invoice in invoicesToPay:
                try:
                    invoice_payment_failed = True
                    stripe_invoice_object = stripe.Invoice.pay(invoice['stripe_invoice_id'])
                    if stripe_invoice_object.paid:
                        print("Invoice payment succeeded: ",invoice['last_name'])
                        #might need to come back and handle this via webhook
                        AppDBUtil.updateInvoiceAsPaid(stripe_invoice_id=invoice['stripe_invoice_id'])
                        invoice_payment_failed = False

                except Exception as e:
                    print("Error in attempting to pay invoices")
                    print(e)
                    traceback.print_exc()
                finally:
                    if invoice_payment_failed:
                        print("Invoice payment failed: ", invoice['last_name'])
                        invoice_name = invoice['first_name'] + " " + invoice['last_name'] + ", "
                        #don't send message here as stripe webhook event that is caught sends message
                        #SendMessagesToClients.sendSMS(to_number='9725847364', message="Invoice payments failed for: " + invoice_name, type='to_mo')
        except Exception as e:
            print("Error in finding invoices to pay")
            print(e)
            traceback.print_exc()


    scheduler = BackgroundScheduler(timezone='US/Central')

    if os.environ['DEPLOY_REGION'] == 'local':
        #scheduler.add_job(invoice_payment_background_job, 'cron', second='30')
        #scheduler.add_job(reminders_background_job,'cron',minute='55')
        scheduler.add_job(lambda: print("dummy reminders job for local"), 'cron', minute='55')
    else:
        scheduler.add_job(reminders_background_job, 'cron', hour='19', minute='45')
        #uncomment after Akinyoade payment
        # scheduler.add_job(reminders_background_job, 'cron', day_of_week='sat', hour='19', minute='45')
        # scheduler.add_job(reminders_background_job, 'cron', day_of_week='sun', hour='19', minute='45')

        scheduler.add_job(invoice_payment_background_job, 'cron', hour='23',minute='45')

    print("Reminders background job added")
    print("Invoice payment background job added")

    scheduler.start()


@server.route('/post_signup_checkout',methods=['POST'])
def post_signup_checkout():
    payment_and_signup_data = request.form.to_dict()
    ask_for_student_info = payment_and_signup_data.get('ask_for_student_info','')

    if ask_for_student_info == 'yes':
        try:
            print("prospect_id in post is ", payment_and_signup_data['prospect_id'])
            print("student data is", payment_and_signup_data)
            AppDBUtil.createStudentData(payment_and_signup_data)
            to_numbers = [number for number in [payment_and_signup_data['parent_1_phone_number'], payment_and_signup_data['parent_2_phone_number'], payment_and_signup_data['student_phone_number']] if number != '']
            SendMessagesToClients.sendGroupSMS(to_numbers=to_numbers, message=payment_and_signup_data['student_first_name'], type='create_group_chat')
            message = ""
            for k, v in ast.literal_eval(payment_and_signup_data['all_days_for_one_on_one']).items():
                message = message + " "+k.split('\n')[1].strip()+","
            SendMessagesToClients.sendEmail(message=message, subject="Suggested one-on-one days for "+str(payment_and_signup_data['student_first_name'])+" "+str(payment_and_signup_data['student_last_name']), type='to_mo')
            # hold off on sending group emails until you dedcide there is a value add
            # SendMessagesToClients.sendEmail(to_addresses=[student_data['parent_1_email'], student_data['parent_2_email'], student_data['student_email'],'mo@perfectscoremo.com'], message=student_data['student_first_name'], type='create_group_email',subject='Setting Up Group Email')
        except Exception as e:
            print(e)
            traceback.print_exc()
            return render_template('error.html',error_message="Error in submitting student information and creating group messages for regular updates. Please contact Mo at 972-584-7364.")

    chosen_mode_of_payment = payment_and_signup_data.get('installment-payment', '') if payment_and_signup_data.get('installment-payment','') != '' else payment_and_signup_data.get('full-payment', '') if payment_and_signup_data.get('full-payment', '') != '' else payment_and_signup_data.get('payment-options', '') if payment_and_signup_data.get('payment-options', '') != '' else ''
    stripe_info = ast.literal_eval(payment_and_signup_data['stripe_info'])
    stripe_pk = os.environ.get('stripe_pk')
    if chosen_mode_of_payment.__contains__('ach'):
        return render_template('plaid_checkout.html',stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment)
    else:
        return render_template('stripe_checkout.html', stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment,stripe_pk=stripe_pk)

@server.route('/complete_signup',methods=['POST'])
def complete_signup():
    try:
        client_info,products_info,showACHOverride = AppDBUtil.getTransactionDetails(request.form.to_dict()['transaction_id'])
    except Exception as e:
        print(e)
        flash('An error has occured. Contact Mo.')
        return redirect(url_for('input_transaction_id'))
    if not client_info and not products_info:
        flash('You might have put in the wrong code. Try again or contact Mo.')
        return redirect(url_for('input_transaction_id'))

    stripe_info = parseDataForStripe(client_info)
    response = make_response(render_template('complete_signup.html', stripe_info=stripe_info, client_info=client_info,products_info=products_info,showACHOverride=showACHOverride,askForStudentInfo=client_info.get('ask_for_student_info',''),prospect_id=client_info.get('prospect_id','')))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"  # HTTP 1.1.
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0.
    response.headers["Expires"] = "0"  # Proxies.

    return response