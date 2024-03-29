from flask import render_template, flash, make_response, redirect, url_for, request, jsonify, Response
from werkzeug.urls import url_parse
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
from app import server
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
from app.service import MiscellaneousUtils
import traceback
from app.config import stripe
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import re
import pytz
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter =  logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)20s() - %(lineno)s - %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

#ADDED TO TURN DOUBLE FLASK LOGGING OFF FLASK LOCAL
from flask.logging import default_handler
server.logger.removeHandler(default_handler)
server.logger.handlers.clear()

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
miscellaneousUtilsInstance = MiscellaneousUtils()


@server.route("/")
def hello():
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

@server.route('/error',defaults={'error_message': None}, methods=['GET'])
@server.route('/error/<error_message>', methods=['GET'])
def error(error_message):
    return render_template('error.html',error_message=error_message)

@server.route('/failure')
def failure():
    return render_template('failure.html')

#@server.route('/transaction_setup',defaults={'search_results': None,'leads':None}, methods=['GET','POST'])
#@server.route('/transaction_setup/<search_results>', methods=['POST'])
# @server.route('/transaction_setup/<leads>', methods=['GET'])
@server.route('/transaction_setup')
@login_required
def transaction_setup():
    leads = AppDBUtil.getAllLeads()
    processed_leads = []
    for lead in leads:
        lead_as_dict = {}
        lead_as_dict['lead_id'] = lead.lead_id
        lead_as_dict['lead_name'] = lead.lead_name
        lead_as_dict['lead_phone_number'] = lead.lead_phone_number
        lead_as_dict['lead_email'] = lead.lead_email
        processed_leads.append(lead_as_dict)

    return render_template('transaction_setup.html', leads=json.dumps(processed_leads))


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
            logger.info(f"prospect_id in post is {student_data['prospect_id']}")
            logger.info(f"student data is {student_data}")
            AppDBUtil.createStudentData(student_data)
            to_numbers = [number for number in [student_data['parent_1_phone_number'],student_data['parent_2_phone_number'],student_data['student_phone_number']] if number != '']
            SendMessagesToClients.sendSMS(to_numbers=to_numbers, message=student_data['student_first_name'], message_type='welcome_new_student')
            time.sleep(5)
            SendMessagesToClients.sendSMS(to_numbers=to_numbers, message_type='referral_request')
            logger.info(f"Student information submitted successfully and text group message for regular updates created for {student_data['student_last_name']}")
            #hold off on sending group emails until you dedcide there is a value add
            #SendMessagesToClients.sendEmail(to_address=[student_data['parent_1_email'], student_data['parent_2_email'], student_data['student_email'],'mo@prepwithmo.com'], message=student_data['student_first_name'], message_type='welcome_new_student',subject='Setting Up Group Email')
            #flash("Student information submitted successfully and group messages (email and text) for regular updates created.")
            flash("Student information submitted successfully and text group message for regular updates created.")
        except Exception as e:
            logger.exception(e)
            #traceback.print_exc()
            flash("Error in submitting student information and creating group messages for regular updates created. Please contact Mo.")
        return render_template('client_info.html', prospect_id=student_data['prospect_id'])


#keep for when you need to send adhoc student info requests to parents
@server.route('/lead_info_by_lead',defaults={'lead_id': None,'is_admin':None}, methods=['GET','POST'])
#@server.route('/lead_info_by_lead/<lead_id>', methods=['GET','POST'])
@server.route('/lead_info_by_lead/<is_admin>/<lead_id>', methods=['GET','POST'])
def lead_info_by_lead(lead_id,is_admin):

    if request.method == 'GET':
        try:
            lead_info_contents = AppDBUtil.getLeadInfo(lead_id)[0]
            logger.info("lead_info_contents in get is: {}".format(lead_info_contents))
            logger.info("lead_id in get is: {}".format(lead_id))

            if is_admin == 'mo':
                what_services_are_you_interested_in=lead_info_contents['what_services_are_they_interested_in']
                details_on_what_service_you_are_interested_in=lead_info_contents['details_on_what_service_they_are_interested_in']
            else:
                what_services_are_you_interested_in= '{}'
                details_on_what_service_you_are_interested_in=''

            return render_template('lead_info_by_lead.html',
                                   lead_id=lead_info_contents['lead_id'],
                                   lead_name=lead_info_contents['lead_name'],
                                   lead_salutation=lead_info_contents['lead_salutation'],
                                   lead_email=lead_info_contents['lead_email'],
                                   lead_phone_number=lead_info_contents['lead_phone_number'],
                                   what_services_are_you_interested_in=what_services_are_you_interested_in,
                                   details_on_what_service_you_are_interested_in=details_on_what_service_you_are_interested_in,
                                   grade_level=lead_info_contents['grade_level'],
                                   recent_test_score=lead_info_contents['recent_test_score'],
                                   miscellaneous_notes=lead_info_contents['miscellaneous_notes'],
                                   how_did_you_hear_about_us=lead_info_contents['how_did_they_hear_about_us'],
                                   details_on_how_you_heard_about_us=lead_info_contents['details_on_how_they_heard_about_us'],
                                   )
        except Exception as e:
            logger.exception(e)
            flash('Error in getting your information. Please contact Mo.')
            return render_template('lead_info_by_lead.html', lead_id=lead_id)


    elif request.method == 'POST':
        try:
            lead_info_contents = request.form.to_dict()
            print("lead_id in post is: {}".format(lead_info_contents['lead_id']) )
            print("lead info contents is: {}".format(lead_info_contents))

            leadInfo = {}

            recent_test_score = -1 if lead_info_contents.get('recent_test_score', '') == '' else lead_info_contents.get('recent_test_score')

            leadInfo.update({'lead_name': lead_info_contents.get('lead_name', ''),'lead_salutation': lead_info_contents.get('lead_salutation', ''),'lead_email': lead_info_contents.get('lead_email', ''),
                             'lead_phone_number': lead_info_contents.get('lead_phone_number', ''),
                             'grade_level': lead_info_contents.get('grade_level',''),'recent_test_score': recent_test_score,'miscellaneous_notes': lead_info_contents.get('miscellaneous_notes', ''),
                             'how_did_they_hear_about_us': lead_info_contents.get('how_did_you_hear_about_us', ''),'details_on_how_they_heard_about_us': lead_info_contents.get('details_on_how_you_heard_about_us', '')})

            #only update if the lead adds new information; otherwise,leave what you put there before
            if lead_info_contents.get('details_on_what_service_you_are_interested_in'):
                leadInfo.update({'details_on_what_service_they_are_interested_in': lead_info_contents.get('details_on_what_service_you_are_interested_in', '')})

            # only update if the lead adds new information; otherwise,leave what you put there before
            if request.form.getlist('what_services_are_you_interested_in'):
                leadInfo.update({'what_services_are_they_interested_in': request.form.getlist('what_services_are_you_interested_in'),})


            number_of_rows_modified = AppDBUtil.modifyLeadInfo(lead_info_contents.get('lead_id', ''), leadInfo)

            if number_of_rows_modified > 1:
                logger.error("Somehow ended up with and modified duplicate lead ids")
                raise Exception("Somehow ended up with and modified duplicate lead ids")

            SendMessagesToClients.sendEmail(to_address='mo@prepwithmo.com', message=[lead_info_contents.get('lead_salutation', '')+ ' '+lead_info_contents.get('lead_name', ''),lead_info_contents['lead_id']], message_type='notify_mo_that_lead_has_updated_lead_info', subject='New Update Submitted By Lead')
            #SendMessagesToClients.sendSMS(to_numbers='9725847364', message="New update submitted by lead {} with lead-id {}. Go check it out.".format(lead_info_contents.get('lead_salutation', '')+ ' '+lead_info_contents.get('lead_name', ''),lead_info_contents['lead_id']), message_type='to_mo')
            flash("Your information has been submitted successfully")
            return render_template('lead_info_by_lead.html', lead_id=lead_id)
        except Exception as e:
            logger.exception(e)
            flash("Error in submitting your information. Please contact Mo.")
            return render_template('lead_info_by_lead.html', lead_id=lead_id)




@server.route('/lead_info_by_mo', methods=['GET','POST'])
@login_required
def lead_info_by_mo():
    if request.method == 'GET':
        return render_template('lead_info_by_mo.html',current_time=datetime.datetime.now(pytz.timezone('US/Central')))
    elif request.method == 'POST':
        lead_info_contents = request.form.to_dict()
        logger.info("lead_info_contents are: {}".format(lead_info_contents))
        action = lead_info_contents['action']

        if action == 'Create':
            try:
                leadInfo = {}
                #appointment_date_and_time = None if lead_info_contents.get('appointment_date_and_time','') == '' else pytz.timezone('US/Central').localize(datetime.datetime.strptime(lead_info_contents.get('appointment_date_and_time'),'%Y-%m-%dT%H:%M'))#lead_info_contents.get('appointment_date_and_time')
                appointment_date_and_time = None if lead_info_contents.get('appointment_date_and_time','') == '' else datetime.datetime.strptime(lead_info_contents.get('appointment_date_and_time'), '%Y-%m-%dT%H:%M').astimezone(pytz.timezone('US/Central'))
                logger.info(appointment_date_and_time)
                recent_test_score = -1 if lead_info_contents.get('recent_test_score','') == '' else lead_info_contents.get('recent_test_score')
                lead_id = "l-" + str(uuid.uuid4().int >> 64)[:6]
                leadInfo.update({'lead_id': lead_id,'lead_salutation': lead_info_contents.get('lead_salutation', ''), 'lead_name': lead_info_contents.get('lead_name', ''), 'lead_email': lead_info_contents.get('lead_email', ''), 'lead_phone_number': lead_info_contents.get('lead_phone_number', ''),
                                 'appointment_date_and_time': appointment_date_and_time,'what_services_are_they_interested_in': request.form.getlist('what_services_are_they_interested_in'), 'details_on_what_service_they_are_interested_in': lead_info_contents.get('details_on_what_service_they_are_interested_in', ''),
                                 'grade_level': lead_info_contents.get('grade_level',''),'recent_test_score': recent_test_score,'appointment_completed':lead_info_contents.get('appointment_completed','no'),
                                 'miscellaneous_notes': lead_info_contents.get('miscellaneous_notes', ''),'how_did_they_hear_about_us': lead_info_contents.get('how_did_they_hear_about_us', ''), 'details_on_how_they_heard_about_us': lead_info_contents.get('details_on_how_they_heard_about_us', ''),'send_confirmation_to_lead':lead_info_contents.get('send_confirmation_to_lead','no')})

                AppDBUtil.createLead(leadInfo)

                if lead_info_contents.get('send_confirmation_to_lead', '') == 'yes':
                    message = lead_info_contents.get('lead_salutation') + ' ' + lead_info_contents.get('lead_name') if lead_info_contents.get('lead_salutation') else 'Parent'

                    if appointment_date_and_time:
                        appointment_date_and_time = datetime.datetime.strptime(lead_info_contents.get('appointment_date_and_time','')+':00', '%Y-%m-%dT%H:%M:%S')
                        appointment_date_and_time = miscellaneousUtilsInstance.clean_up_date_and_time(appointment_date_and_time.astimezone(pytz.timezone('US/Central')))

                    if lead_info_contents.get('lead_phone_number'):
                        SendMessagesToClients.sendSMS(to_numbers=lead_info_contents.get('lead_phone_number'), message=[message, appointment_date_and_time,lead_id], message_type='confirm_lead_appointment')
                    if lead_info_contents.get('lead_email'):
                        SendMessagesToClients.sendEmail(to_address=[lead_info_contents.get('lead_email'), 'mo@prepwithmo.com'], message=[message, appointment_date_and_time,lead_id], message_type='confirm_lead_appointment', subject='Confirming Your Appointment')

                flash('The lead info was created successfully.')
                return render_template('lead_info_by_mo.html', action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))
            except Exception as e:
                logger.exception(e)
                flash('An error has occurred during the creation.')
                return render_template('lead_info_by_mo.html', action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))

        if action == 'Modify':
            try:
                leadInfo = {}
                appointment_date_and_time = None if lead_info_contents.get('appointment_date_and_time','') == '' else datetime.datetime.strptime(lead_info_contents.get('appointment_date_and_time'), '%Y-%m-%dT%H:%M').astimezone(pytz.timezone('US/Central'))
                recent_test_score = -1 if lead_info_contents.get('recent_test_score','') == '' else lead_info_contents.get('recent_test_score')
                lead_id = lead_info_contents.get('lead_id', '')

                leadInfo.update({'lead_name': lead_info_contents.get('lead_name', ''),'lead_salutation': lead_info_contents.get('lead_salutation', ''), 'lead_email': lead_info_contents.get('lead_email', ''),
                                 'lead_phone_number': lead_info_contents.get('lead_phone_number', ''),'appointment_date_and_time': appointment_date_and_time,
                                 'what_services_are_they_interested_in': request.form.getlist('what_services_are_they_interested_in'), 'details_on_what_service_they_are_interested_in': lead_info_contents.get('details_on_what_service_they_are_interested_in', ''),
                                 'grade_level': lead_info_contents.get('grade_level', ''),'recent_test_score': recent_test_score,'appointment_completed':lead_info_contents.get('appointment_completed','no'),
                                 'miscellaneous_notes': lead_info_contents.get('miscellaneous_notes', ''),'send_confirmation_to_lead':lead_info_contents.get('send_confirmation_to_lead','no'),
                                 'how_did_they_hear_about_us': lead_info_contents.get('how_did_they_hear_about_us', ''), 'details_on_how_they_heard_about_us': lead_info_contents.get('details_on_how_they_heard_about_us', '')})


                number_of_rows_modified = AppDBUtil.modifyLeadInfo(lead_info_contents.get('lead_id', ''),leadInfo)

                if number_of_rows_modified > 1:
                    logger.info("Somehow ended up with and modified duplicate lead ids")
                    flash('Somehow ended up with and modified duplicate lead ids')

                if lead_info_contents.get('send_confirmation_to_lead', '') == 'yes':
                    message = lead_info_contents.get('lead_salutation') + ' ' + lead_info_contents.get('lead_name') if lead_info_contents.get('lead_salutation') else 'Parent'

                    if appointment_date_and_time:
                        appointment_date_and_time = datetime.datetime.strptime(lead_info_contents.get('appointment_date_and_time','')+':00', '%Y-%m-%dT%H:%M:%S')
                        appointment_date_and_time = miscellaneousUtilsInstance.clean_up_date_and_time(appointment_date_and_time)
                    if lead_info_contents.get('lead_phone_number'):
                        SendMessagesToClients.sendSMS(to_numbers=lead_info_contents.get('lead_phone_number'),message=[message, appointment_date_and_time, lead_id],message_type='confirm_lead_appointment')
                    if lead_info_contents.get('lead_email'):
                        SendMessagesToClients.sendEmail(to_address=[lead_info_contents.get('lead_email'), 'mo@prepwithmo.com'],message=[message, appointment_date_and_time, lead_id],message_type='confirm_lead_appointment', subject='Confirming Your Appointment')

                flash('Lead sucessfully modified.')
                return render_template('lead_info_by_mo.html', action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))
            except Exception as e:
                logger.exception(e)
                flash('An error occurred while modifying the lead.')
                return render_template('lead_info_by_mo.html', action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))

        if action == 'Search':
            try:
                search_results = {}
                search_results = AppDBUtil.getLeadInfo(lead_info_contents.get('search_query', None), lead_info_contents.get('start_date', None), lead_info_contents.get('end_date', None))
            except Exception as e:
                logger.exception(e)
                flash('An error has occurred during the search.')
                render_template('lead_info_by_mo.html', action=action)

            if not search_results:
                flash('No lead info has the detail you searched for.')
                render_template('lead_info_by_mo.html', action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))

            return render_template('lead_info_by_mo.html', search_results=search_results, action=action,current_time=datetime.datetime.now(pytz.timezone('US/Central')))



@server.route('/create_transaction',methods=['POST'])
@login_required
def create_transaction():

    transaction_setup_data = request.form.to_dict()
    logger.info("transaction_setup_data is {}".format(transaction_setup_data))

    if transaction_setup_data.get('modify_pause_status'):
        try:
            transaction_id_to_pause = transaction_setup_data['transaction_id_to_pause']
            pause_payment = transaction_setup_data.get('pause_payment')
            paused_payment_resumption_date = transaction_setup_data.get('paused_payment_resumption_date')
            AppDBUtil.updatePausePaymentStatus( transaction_id_to_pause, pause_payment, paused_payment_resumption_date)
            #installment_counter = 0 if transaction_setup_data.get('installment_counter', '') == '' else int(transaction_setup_data.get('installment_counter', ''))
            #if installment_counter > 1:
            AppDBUtil.modifyPauseStatusOnInvoicesToBePaid(transaction_id_to_pause, pause_payment, paused_payment_resumption_date)
            flash('Transaction pause status successfully updated')
            return redirect(url_for('transaction_setup'))
        except Exception as e:
            logger.exception(e)
            flash('An error occurred while updating the transaction pause status')
            return redirect(url_for('transaction_setup'))
    else:
        try:

            prospect = AppDBUtil.createProspect(transaction_setup_data)

            customer,does_customer_payment_info_exist = stripeInstance.createCustomer(transaction_setup_data)
            transaction_setup_data.update({"stripe_customer_id":customer["id"],'prospect_id':prospect.prospect_id,'does_customer_payment_info_exist':does_customer_payment_info_exist})
            transaction_id,number_of_rows_modified = AppDBUtil.createOrModifyClientTransaction(transaction_setup_data, action='create')

            client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)
            logger.info('Transaction details (client_info) are: ' + str(client_info))
            logger.info('Transaction details (products_info) are: ' + str(products_info))
            logger.info('Transaction details (showACHOverride) are: ' + str(showACHOverride))

            stripe_info = parseDataForStripe(client_info)
            logger.info('stripe_info is: ' + str(stripe_info))

            flash_message = ''


            if transaction_setup_data.get('mark_as_paid','') == 'yes':
                stripeInstance.markCustomerAsChargedOutsideofStripe(stripe_info,action='create')
                AppDBUtil.updateTransactionPaymentStarted(transaction_id)
                logger.info('Mark transaction as paid: '+str(stripe_info['transaction_id']))
                flash_message = 'Transaction created and marked as paid.'
            else:
                message_type = ''
                if transaction_setup_data.get('pay_automatically', '') == 'yes':
                #if does_customer_payment_info_exist:
                    message_type = 'create_transaction_with_auto_pay'
                    logger.info('Setup auto-payment: ' + str(stripe_info['transaction_id']))
                    stripeInstance.setupAutoPaymentForExistingCustomer(stripe_info)
                    flash_message = 'Transaction created and paid automatically.'
                else:
                    message_type = 'create_transaction_without_auto_pay'
                    flash_message = 'Transaction created.'

                if transaction_setup_data.get('send_text_and_email', '') == 'yes':
                    logger.info('Send transaction text and email notification: ' + str(stripe_info['transaction_id']))
                    try:
                        recipient_name = transaction_setup_data['salutation'] + ' ' + transaction_setup_data['first_name'] + ' ' + transaction_setup_data['last_name']
                        SendMessagesToClients.sendEmail(to_address=transaction_setup_data['email'], message=transaction_id, message_type=message_type, recipient_name=recipient_name)
                        if message_type == 'create_transaction_with_auto_pay':
                            SendMessagesToClients.sendSMS(to_numbers=[transaction_setup_data['phone_number']], message=transaction_id, message_type=message_type, recipient_name=recipient_name)
                            time.sleep(5)
                            SendMessagesToClients.sendSMS(to_numbers=[transaction_setup_data['phone_number']], message=transaction_id, message_type='questions')
                        else:
                            SendMessagesToClients.sendSMS(to_numbers=transaction_setup_data['phone_number'], message=transaction_id, message_type=message_type, recipient_name=recipient_name)
                        flash_message = flash_message+ ' ' + 'Also, email/sms sent to client.'
                    except Exception as e:
                        traceback.print_exc()
                        flash_message = flash_message + ' ' + 'But an error occurred while sending an email/sms to the client after creating the transaction.'
            logger.info('Created transaction: ' + str(stripe_info['transaction_id']))
            flash(flash_message)
            return render_template('generate_transaction_id.html',transaction_id=transaction_id,input_transaction_id_url=os.environ.get("url_to_start_reminder")+"input_transaction_id")
        except Exception as e:
            logger.exception(e)
            flash('An error occurred while creating the transaction.')
            return redirect(url_for('transaction_setup'))

@server.route('/search_transaction',methods=['POST'])
@login_required
def search_transaction():
    search_query = str(request.form['search_query'])
    try:
        leads = AppDBUtil.getAllLeads()
        processed_leads = []
        for lead in leads:
            lead_as_dict = {}
            lead_as_dict['lead_id'] = lead.lead_id
            lead_as_dict['lead_name'] = lead.lead_name
            lead_as_dict['lead_phone_number'] = lead.lead_phone_number
            lead_as_dict['lead_email'] = lead.lead_email
            processed_leads.append(lead_as_dict)

        search_results = AppDBUtil.searchTransactions(search_query)
    except Exception as e:
        print(e)
        traceback.print_exc()
        flash('An error has occurred during the search.')
        return redirect(url_for('transaction_setup'))

    if not search_results:
        flash('No transaction has the detail you searched for.')
        return redirect(url_for('transaction_setup'))

    logger.info('Searched for: ' + str(search_query))
    #return redirect(url_for('transaction_setup',search_results=search_results))
    return render_template('transaction_setup.html',search_results=search_results,leads=json.dumps(processed_leads))

@server.route('/modify_transaction',methods=['POST'])
@login_required
def modify_transaction():
    try:
        data_to_modify = ast.literal_eval(request.form['data_to_modify'])
        logger.info("data_to_modify is {}".format(data_to_modify))
        transaction_id = data_to_modify['transaction_id']
        transaction_id_again,number_of_rows_modified=AppDBUtil.modifyTransactionDetails(data_to_modify)

        if number_of_rows_modified < 1:
            logger.info("No transaction was modified, perhaps because no transaction code was provided")
            flash('No transaction was modified, perhaps because no transaction code was provided')
            return redirect(url_for('transaction_setup'))

        if number_of_rows_modified > 1:
            logger.info("Somehow ended up with and modified duplicate transaction codes")
            flash('Somehow ended up with and modified duplicate transaction codes')
            #return render_template('transaction_setup.html',leads=json.dumps(processed_leads))
            return redirect(url_for('transaction_setup'))

        flash_message = ''

        if AppDBUtil.isTransactionPaymentStarted(transaction_id):
            logger.info(f"{transaction_id} is a started transaction, so modifying the pause status and dates of its unpaid invoices")
            AppDBUtil.modifyTransactionBasedOnPauseUnpauseStatus(clientData=data_to_modify, transaction_id=transaction_id)
            flash_message = 'Pause status and dates of unpaid invoices updated for already started transaction updated.'
        else:
            if data_to_modify.get('mark_as_paid', '') == 'yes':
                client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)
                stripe_info = parseDataForStripe(client_info)
                stripeInstance.markCustomerAsChargedOutsideofStripe(stripe_info,action='modify')
                AppDBUtil.updateTransactionPaymentStarted(transaction_id)
                logger.info("marked transaction as paid")
                flash_message = 'Transaction modified and marked as paid.'
            else:
                customer, does_customer_payment_info_exist = stripeInstance.createCustomer(data_to_modify)
                client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)
                stripe_info = parseDataForStripe(client_info)
                message_type = ''

                
                if data_to_modify.get('pay_automatically', '') == 'yes':
                #if does_customer_payment_info_exist:
                    message_type = 'modify_transaction_with_auto_pay'
                    logger.info('Set up auto-payment: ' + str(stripe_info['transaction_id']))
                    stripeInstance.setupAutoPaymentForExistingCustomer(stripe_info)
                    flash_message = 'Transaction modified and paid automatically.'
                else:
                    message_type = 'modify_transaction_without_auto_pay'
                    flash_message = 'Transaction modified.'


        if data_to_modify.get('send_text_and_email','') == 'yes':
            logger.info('Send modified transaction text and email notification: ' + str(stripe_info['transaction_id']))
            try:
                recipient_name = data_to_modify['salutation'] + ' ' + data_to_modify['first_name'] + ' ' + data_to_modify['last_name']
                SendMessagesToClients.sendEmail(to_address=data_to_modify['email'], message=transaction_id, message_type=message_type)
                if message_type == 'modify_transaction_with_auto_pay':
                    SendMessagesToClients.sendSMS(to_numbers=[data_to_modify['phone_number']], message=transaction_id, message_type=message_type,recipient_name=recipient_name)
                    time.sleep(5)#
                    SendMessagesToClients.sendSMS(to_numbers=[data_to_modify['phone_number']], message=transaction_id, message_type='questions',recipient_name=recipient_name)
                else:
                    SendMessagesToClients.sendSMS(to_numbers=data_to_modify['phone_number'], message=transaction_id, message_type=message_type,recipient_name=recipient_name)

                flash_message = flash_message+ ' ' + 'Also, email/sms sent to client.'
            except Exception as e:
                logger.exception(e)
                flash_message = flash_message + ' ' + 'But an error occurred while sending an email/sms to the client after modifying the transaction.'

        logger.info(f'Modified transaction: {transaction_id}')
        flash(flash_message)
        #return render_template('transaction_setup.html',leads=json.dumps(processed_leads))
        return redirect(url_for('transaction_setup'))
    except Exception as e:
        logger.exception(e)
        flash('An error occurred while modifying the transaction.')
        #return render_template('transaction_setup.html',leads=json.dumps(processed_leads))
        return redirect(url_for('transaction_setup'))

    #return render_template('transaction_setup.html',leads=json.dumps(processed_leads))
    return redirect(url_for('transaction_setup', leads=json.dumps(processed_leads)))

@server.route('/delete_transaction',methods=['POST'])
@login_required
def delete_transaction():
    try:
        transaction_id_to_delete = str(request.form['transaction_id_to_delete'])
        logger.info(transaction_id_to_delete)
        AppDBUtil.deleteTransactionAndInstallmentPlan(transaction_id_to_delete)
        flash('Transaction sucessfully deleted.')
        return redirect(url_for('transaction_setup'))
    except Exception as e:
        logger.exception(e)
        flash('An error occurred while deleting the transaction.')
        return redirect(url_for('transaction_setup'))

    #return render_template('transaction_setup.html')

@server.route('/input_transaction_id',methods=['GET'])
def input_transaction_id():
    return render_template('input_transaction_id.html')

@login_manager.user_loader
def load_user(password):
    return User(awsInstance.get_secret("vensti_admin", 'password'))

@server.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('admin_login'))


def parseDataForStripe(client_info):
    #rememeber to not add more data here that could  be safely added to client_info or product_info. this seems to have been originally designed
    # to parse specific data in a specifc way that was causing stripe processing to break
    stripe_info = {}
    stripe_info['name'] = client_info['first_name']+" "+client_info['last_name']
    stripe_info['phone_number'] = client_info['phone_number']
    stripe_info['email'] = client_info['email']
    stripe_info['stripe_customer_id'] = client_info['stripe_customer_id']
    stripe_info['transaction_total'] = client_info['transaction_total']
    #stripe_info['deposit'] = client_info.get('deposit','')
    stripe_info['transaction_id'] = client_info.get('transaction_id', '')
    stripe_info['installment_counter'] = client_info.get('installment_counter', '')
    stripe_info['ask_for_student_info'] = client_info.get('ask_for_student_info', '')
    stripe_info['ask_for_student_availability'] = client_info.get('ask_for_student_availability', '')
    stripe_info['does_customer_payment_info_exist'] = client_info.get('does_customer_payment_info_exist', '')
    stripe_info['prospect_id'] = client_info.get('prospect_id', '')

    stripe_info['make_payment_recurring'] = client_info.get('make_payment_recurring', '')
    stripe_info['recurring_payment_frequency'] = client_info.get('recurring_payment_frequency', 0)
    stripe_info['recurring_payment_start_date'] = client_info.get('recurring_payment_start_date', None).strftime("%Y-%m-%d") if client_info.get('recurring_payment_start_date', None) else ''
    stripe_info['pause_payment'] = client_info.get('pause_payment', '')
    stripe_info['paused_payment_resumption_date'] = client_info.get('paused_payment_resumption_date', None).strftime("%Y-%m-%d") if client_info.get('paused_payment_resumption_date', None) else ''


    if client_info.get('installments','') != '':
        for index,installment in enumerate(client_info.get('installments','')):
            #logger.info(f"index {index} and installment {installment}")
            stripe_info["date"+"_"+str(index+1)] = int(time.mktime(installment["date"].timetuple()))
            stripe_info["amount" + "_" + str(index+1)] = installment["amount"]

    return stripe_info

@server.route('/setup_payment_intent',methods=['POST'])
def setup_payment_intent():
    try:
        stripe_info = ast.literal_eval(request.form['stripe_info'])
        client_secret = stripeInstance.setUpIntent(stripe_info)
        return jsonify({'client_secret': client_secret})
    except Exception as e:
        logger.error("Error  in /setup_payment_intent")
        print(e)
        traceback.print_exc()



def checkIfDetailsWereChangedOnFrontEnd(stripe_info={}):
    client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(stripe_info['transaction_id'])

    if client_info['transaction_total'] == stripe_info['transaction_total']:
        details_were_changed_from_front_end = False
        for k in range(1, int(stripe_info['installment_counter'])):
            date_from_back_end = client_info['installments'][k - 1]['date']
            amount_from_back_end = client_info['installments'][k - 1]['amount']
            date_from_front_end = datetime.datetime.fromtimestamp(stripe_info['date_' + str(k)]).date()
            amount_from_front_end = stripe_info['amount_' + str(k)]
            if date_from_back_end != date_from_front_end or amount_from_back_end != amount_from_front_end:
                logger.info("date_from_back_end is: {}".format(date_from_back_end))
                logger.info("date_from_front_end is: {}".format(date_from_front_end))
                logger.info("amount_from_back_end is: {}".format(amount_from_back_end))
                logger.info("amount_from_front_end is: {}".format(amount_from_front_end))
                details_were_changed_from_front_end = True
                break
    else:
        details_were_changed_from_front_end = True

    return details_were_changed_from_front_end


@server.route('/execute_card_payment',methods=['POST'])
def execute_card_payment():
    try:
        chosen_mode_of_payment = request.form['chosen_mode_of_payment']
        stripe_info = ast.literal_eval(request.form['stripe_info'])
        payment_id = request.form['payment_id']
        does_customer_payment_info_exist = True if stripe_info.get('does_customer_payment_info_exist','') == 'yes' else False

        details_were_changed_from_front_end = checkIfDetailsWereChangedOnFrontEnd(stripe_info)

        if details_were_changed_from_front_end:
            #return redirect(url_for('error', error_message="Details were changed. Conact Mo."))
            logger.info("Details were changed on the front end.")
            return jsonify({'status':'error','message':'Details were changed. Conact Mo.'})
        result = stripeInstance.chargeCustomerViaCard(stripe_info=stripe_info, chosen_mode_of_payment=chosen_mode_of_payment, payment_id=payment_id,existing_customer=does_customer_payment_info_exist)
        if result['status'] != 'success':
            logger.error("Stripe card payment failed")
            flash('Payment failed. Enter a valid credit/debit card number or check why your bank is blocking your card. Or contact Mo.')
        else:
            AppDBUtil.updateTransactionPaymentStarted(stripe_info['transaction_id'])
            payment_and_signup_data = ast.literal_eval(request.form['payment_and_signup_data'])
            if payment_and_signup_data.get('ask_for_student_info', '') == 'yes':
                result = enterClientInfo(payment_and_signup_data)
                if result['status'] != 'success':
                    logger.error('Attempt to create family information failed. Contact Mo.')
                    return jsonify({'status': 'error', 'message': 'Payment successful, but attempt to create family information failed. Contact Mo.'})

            if payment_and_signup_data.get('ask_for_student_availability', '') == 'yes':
                result = notifyOneOnOneInfo(payment_and_signup_data)
                if result['status'] != 'success':
                    logger.error('Attempt to notify one-on-one info failed. Contact Mo.')
                    return jsonify({'status': 'error', 'message': 'Payment successful, but attempt to create family information failed. Contact Mo.'})

        logger.info(f"Result from execute_card_payment is {jsonify(result)}")
        return jsonify(result)
    except Exception as e:
        logger.exception("Error  in /execute_card_payment")
        flash('Unexpected error. contact Mo.')
        return jsonify(result)

@server.route("/get_link_token", methods=['POST'])
def get_link_token():
    try:
        stripe_info = ast.literal_eval(request.form['stripe_info'])
        link_token = plaidInstance.get_link_token(stripe_info['stripe_customer_id'])
        return jsonify({'link_token': link_token})
    except Exception as e:
        logger.error("Error  in /get_link_token")
        print(e)
        traceback.print_exc()

@server.route("/exchange_plaid_for_stripe", methods=['POST'])
def exchange_plaid_for_stripe():
    try:
        # Change sandbox to development to test with live users and change
        # to production when you're ready to go live!
        stripe_info = ast.literal_eval(request.form['stripe_info'])
        public_token = request.form['public_token']
        account_id = request.form['account_id']
        chosen_mode_of_payment = request.form['chosen_mode_of_payment']
        bank_account_token = plaidInstance.exchange_plaid_for_stripe(public_token,account_id)
        does_customer_payment_info_exist = True if stripe_info.get('does_customer_payment_info_exist','') == 'yes' else False

        details_were_changed_from_front_end = checkIfDetailsWereChangedOnFrontEnd(stripe_info)

        if details_were_changed_from_front_end:
            logger.info("Details were changed on the front end.")
            return jsonify({'status': 'error', 'message': 'Details were changed. Conact Mo.'})

        result = stripeInstance.chargeCustomerViaACH(stripe_info=stripe_info,bank_account_token=bank_account_token,chosen_mode_of_payment=chosen_mode_of_payment,existing_customer=does_customer_payment_info_exist)

        if result['status'] != 'success':
            logger.info("Attempt to pay via ACH failed. Try again, check with your bank on any errors, or contact Mo.")
            flash('Attempt to pay via ACH failed. Try again, check with your bank on any errors, or contact Mo.')
        else:
            AppDBUtil.updateTransactionPaymentStarted(stripe_info['transaction_id'])

            payment_and_signup_data = ast.literal_eval(request.form['payment_and_signup_data'])
            if payment_and_signup_data.get('ask_for_student_info', '') == 'yes':
                result = enterClientInfo(payment_and_signup_data)
                if result['status'] != 'success':
                    logger.error('Attempt to create family information failed. Contact Mo.')
                    return jsonify({'status': 'error', 'message': 'Payment successful, but attempt to create family information failed. Contact Mo.'})
                    # flash('Attempt to create family information failed. Contact Mo.')

            if payment_and_signup_data.get('ask_for_student_availability', '') == 'yes':
                result = notifyOneOnOneInfo(payment_and_signup_data)
                if result['status'] != 'success':
                    logger.error('Attempt to notify one-on-one info failed. Contact Mo.')
                    return jsonify({'status': 'error', 'message': 'Payment successful, but attempt to create family information failed. Contact Mo.'})

        return jsonify(result)
    except Exception as e:
        logger.exception("Error  in /exchange_plaid_for_stripe")
        flash('Unexpected error. contact Mo.')
        return jsonify(result)

def notifyOneOnOneInfo(payment_and_signup_data={}):
    try:
        to_numbers = [number for number in [payment_and_signup_data['parent_1_phone_number'], payment_and_signup_data['parent_2_phone_number'], payment_and_signup_data['student_phone_number']] if number != '']
        SendMessagesToClients.sendSMS(to_numbers=to_numbers, message=payment_and_signup_data['student_first_name'], message_type='welcome_new_student')
        time.sleep(5)
        SendMessagesToClients.sendSMS(to_numbers=to_numbers, message_type='referral_request')
        message = ""
        for k, v in ast.literal_eval(payment_and_signup_data['all_days_for_one_on_one']).items():
            message = message + " " + k.split('\n')[1].strip() + ","
        SendMessagesToClients.sendEmail(message=message, subject="Suggested one-on-one days for " + str(payment_and_signup_data['student_first_name']) + " " + str(payment_and_signup_data['student_last_name']), message_type='notify_mo_about_suggested_one_on_one_days')
        # hold off on sending group emails until you dedcide there is a value add
        # SendMessagesToClients.sendEmail(to_address=[student_data['parent_1_email'], student_data['parent_2_email'], student_data['student_email'],'mo@prepwithmo.com'], message=student_data['student_first_name'], message_type='welcome_new_student',subject='Setting Up Group Email')
        return {'status': 'success'}
    except Exception as e:
        logger.exception(e)
        return {'status': 'failure'}
        #return render_template('error.html', error_message="Error in submitting student information and creating group messages for regular updates. Please contact Mo at 972-584-7364.")


def enterClientInfo(payment_and_signup_data={}):
    try:
        logger.info(f"prospect_id in post is {payment_and_signup_data['prospect_id']}")
        logger.info(f"student data is {payment_and_signup_data}")
        AppDBUtil.createStudentData(payment_and_signup_data)
        logger.info(f"Student information submitted successfully for {payment_and_signup_data['student_last_name']}")
        return {'status': 'success'}
    except Exception as e:
        logger.exception(e)
        return {'status': 'failure'}
        #return render_template('error.html', error_message="Error in submitting student information and creating group messages for regular updates. Please contact Mo at 972-584-7364.")


@server.route("/stripe_webhook", methods=['POST'])
def stripe_webhook():
    # if os.environ['DEPLOY_REGION'] != 'prod':
    #     return json.dumps({'success': True,'message':'dummy success for non-prod environment'}), 200, {'ContentType': 'application/json'}


    payload = json.dumps(request.json)
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        logger.error("400 error from calling webhook. Check code and logs")
        logger.error(e)
        traceback.print_exc()
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'}
    try:
        #using this for successful card payments
        if event.type == 'invoice.paid':
            paid_invoice = event.data.object
            transaction_id = paid_invoice.metadata['transaction_id']

            # payment_type = ''
            # if paid_invoice.payment_intent:
            #     payment_intent = stripe.PaymentIntent.retrieve(paid_invoice.payment_intent,)
            #     payment_method = stripe.PaymentMethod.retrieve(str(payment_intent['payment_method']),)
            #     payment_type = str(payment_method['type'])
            # consider replacing below with this if there are further errors

            payment_intent = stripe.PaymentIntent.retrieve(paid_invoice.payment_intent, ) if paid_invoice.payment_intent else None
            payment_method = stripe.PaymentMethod.retrieve(payment_intent['payment_method'], ) if payment_intent and payment_intent['payment_method'] else stripe.PaymentMethod.retrieve(payment_intent['source'], ) if payment_intent and payment_intent['source'] else None
            payment_type = payment_method['type'] if payment_method else None

            if not payment_type:
                raise Exception('Somehow there is no payment intent, payment method, or payment type')

            if payment_type == 'card':
                amount_paid = int(math.floor(paid_invoice.total / 103))


                AppDBUtil.updateInvoiceAsPaid(paid_invoice.id)
                AppDBUtil.updateAmountPaidAgainstTransaction(transaction_id, amount_paid)
                AppDBUtil.updateTransactionPaymentStarted(transaction_id)
                AppDBUtil.updateTransactionDoesCustomerPaymentInfoExist(transaction_id)

                logger.info(f"Transaction {transaction_id} with stripe invoice id {paid_invoice.id} is paid (VIA Card)")
            # else:
            #     raise Exception(f"Why is payment type not card for {transaction_id} ?")

        # using this for failed card payments and future failed ACH payments
        elif event.type == 'invoice.payment_failed':
            failed_invoice = event.data.object
            try:
                message = "Invoice "+str(failed_invoice.id)+" for "+str(failed_invoice.customer_name)+" failed to pay."
                SendMessagesToClients.sendSMS(to_numbers='9725847364', message=message, message_type='to_mo')
                logger.error(message)
            except Exception as e:
                logger.exception(e)

        elif event.type == 'invoice.finalized':
            finalized_invoice = event.data.object
            transaction_id = finalized_invoice.metadata['transaction_id']

            payment_intent = stripe.PaymentIntent.retrieve(finalized_invoice.payment_intent, ) if finalized_invoice.payment_intent else None
            payment_attempt_status = payment_intent['charges']['data'][0]['outcome']['network_status'] if payment_intent and payment_intent['charges']['data'][0]['outcome'] else None
            logger.info(f"Payment status is {payment_attempt_status} for {transaction_id}")
            #payment_method_details = payment_intent['charges']['data'][0]['payment_method_details']['type'] if payment_intent['charges']['data'][0]['payment_method_details'] else None
            #TODO consider reverting to the above if the below fails
            payment_method_details = payment_intent['charges']['data'][0]['payment_method_details']['type'] if payment_intent['charges']['data'] else None


            if not payment_method_details:
                raise Exception('Somehow there is no payment intent or payment_method_details')

            if payment_method_details == 'ach_debit':
                amount_paid = finalized_invoice.total / 100

                # using this for successful ach payments
                if payment_attempt_status == 'approved_by_network':
                    AppDBUtil.updateInvoiceAsPaid(finalized_invoice.id)
                    AppDBUtil.updateAmountPaidAgainstTransaction(transaction_id,amount_paid)
                    AppDBUtil.updateTransactionPaymentStarted(transaction_id)
                    AppDBUtil.updateTransactionDoesCustomerPaymentInfoExist(transaction_id)

                    logger.info(f"Transaction {transaction_id} with stripe invoice id {finalized_invoice.id} is paid (VIA ACH)")

                # using this for failed ach payments
                else:
                    try:
                        message = "Invoice " + str(finalized_invoice.id) + " for " + str(finalized_invoice.customer_name) + " failed to pay."
                        if os.environ.get("DEPLOY_REGION") == 'PROD':
                            SendMessagesToClients.sendSMS(to_numbers='9725847364', message=message, message_type='to_mo')
                        logger.error(message)
                    except Exception as e:
                        logger.exception(e)
            else:
                pass
                #logger.warning(f"Why is payment method detail not ach_debit for {transaction_id} ? Probably because there this is an instance of a credit card payment, which was already handled under invoice.paid and is now being sent to be finalized, which I do not care for since it has already been updated as paid the under invoice.paid i.e. I only care about updating ach payments through invoice.finalized.")
                #raise Exception("Why is payment method detail not ach_debit for {} ? Probably because there this is an instance of a credit card payment, which was already handled under invoice.paid and is now being sent to be finalized, which I do not care for since it has already been updated as paid the under invoice.paid i.e. I only care about updating ach payments through invoice.finalized.".format(transaction_id))


        elif event.type == 'invoice.created':
            created_invoice = event.data.object
            transaction_id = created_invoice.metadata['transaction_id']
            logger.info(f'Transaction {transaction_id} created in Stripe')
        else:
            logger.info(f'Unhandled event type {event.type}')


    except Exception as e:
        logger.exception("500 error from calling webhook. Check code and logs.\n"+str(e))
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}
        #return jsonify({'status': 500})

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    #return jsonify({'status': 200})

@server.before_first_request
def start_background_jobs_before_first_request():
    def remind_lead_about_appointment_background_job():
        try:
            logger.info("remind_lead_about_appointment_background_job started")
            reminder_last_names = 'The following leads were sent reminders about an upcoming appointment: '
            leadsToReceiveReminders = AppDBUtil.findLeadsToReceiveReminders()
            logger.info("leadsToReceiveReminders are: {}".format(leadsToReceiveReminders))
            leads_eligible_for_reminders = False
            for lead in leadsToReceiveReminders:
                number_of_days_until_appointment = (lead.get('appointment_date_and_time').astimezone(pytz.timezone('US/Central')).date() - datetime.datetime.now(pytz.timezone('US/Central')).date()).days
                appointment_date_and_time = miscellaneousUtilsInstance.clean_up_date_and_time(lead.get('appointment_date_and_time').astimezone(pytz.timezone('US/Central')))

                if number_of_days_until_appointment in [0,1,3]:
                    leads_eligible_for_reminders = True
                    message = lead.get('lead_salutation') + " " + lead.get('lead_name') if lead.get('lead_salutation') else 'Parent'
                    if lead.get('lead_email'):
                        SendMessagesToClients.sendEmail(to_address=[lead.get('lead_email'), 'mo@prepwithmo.com'], message=[message, appointment_date_and_time, lead.get('lead_id')], message_type='reminder_about_appointment', subject='Reminder About Your Appointment')
                    if lead.get('lead_phone_number'):
                        SendMessagesToClients.sendSMS(to_numbers=lead.get('lead_phone_number'), message=[message, appointment_date_and_time, lead.get('lead_id')], message_type='reminder_about_appointment')
                    reminder_last_names = reminder_last_names+lead['lead_name']+" ("+appointment_date_and_time+")"+", "
            if leads_eligible_for_reminders:
                SendMessagesToClients.sendSMS(to_numbers='9725847364', message=reminder_last_names, message_type='to_mo')

        except Exception as e:
            logger.exception("Error in sending reminders: {}".format(e))


    def notify_mo_to_modify_lead_appointment_completion_status_background_job():
        try:
            logger.info("notify_mo_to_modify_lead_appointment_completion_status started")
            #reminder_last_names = 'Use the below URLs to modify the appointment completion status of leads in the last hour : '
            leadsWithAppointmentsInTheLastHour = AppDBUtil.findLeadsWithAppointmentsInTheLastHour()

            for lead in leadsWithAppointmentsInTheLastHour:
                #pass
                SendMessagesToClients.sendEmail(to_address='mo@prepwithmo.com',subject='Update Lead Appointment Completion Status', message=[lead['lead_salutation'],lead['lead_name'],miscellaneousUtilsInstance.clean_up_date_and_time(lead.get('appointment_date_and_time').astimezone(pytz.timezone('US/Central'))),lead['lead_id']],message_type='notify_mo_to_modify_lead_appointment_completion_status')
                #link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/" + message[2]
                #reminder_last_names = reminder_last_names+lead['lead_salutation']+' '+lead['lead_name']+' '+lead['appointment_date_and_time']+' '+''+", ".format(lead['lead_id'])
            # if clientsToReceiveReminders:
            #     SendMessagesToClients.sendSMS(to_numbers='9725847364', message=reminder_last_names, message_type='to_mo')

        except Exception as e:
            logger.exception("Error in sending reminders: {}".format(e))

    def remind_client_about_invoice_background_job():
        try:
            logger.info("remind_client_about_invoice_background_job started")
            reminder_last_names = 'The following clients were sent reminders about an unaddressed transaction: '
            clientsToReceiveReminders = AppDBUtil.findClientsToReceiveReminders()

            for client in clientsToReceiveReminders:
                recipient_name = client['salutation'] + ' ' + client['last_name']
                SendMessagesToClients.sendEmail(to_address=client['email'], message=client['transaction_id'], message_type='reminder_to_make_payment',recipient_name=recipient_name)
                SendMessagesToClients.sendSMS(to_numbers=client['phone_number'], message=client['transaction_id'], message_type='reminder_to_make_payment',recipient_name=recipient_name)
                reminder_last_names = reminder_last_names+client['last_name']+", "
            if clientsToReceiveReminders:
                SendMessagesToClients.sendSMS(to_numbers='9725847364', message=reminder_last_names, message_type='to_mo')

        except Exception as e:
            logger.exception("Error in sending reminders: {}".format(e))

    def pay_invoice_background_job():
        logger.info("pay_invoice_background_job started")
        try:
            invoicesToPay = AppDBUtil.findInvoicesToPay()
            logger.info("Invoices to pay are: {}".format(invoicesToPay))

            for invoice in invoicesToPay:
                try:
                    invoice_payment_failed = True

                    stripe_invoice_ach_charge = stripe.Invoice.retrieve(invoice['stripe_invoice_id']).charge
                    if stripe_invoice_ach_charge:
                        stripe_invoice_ach_charge = stripe.Charge.retrieve(stripe_invoice_ach_charge)
                        if stripe_invoice_ach_charge.status == 'pending' and stripe_invoice_ach_charge.payment_method_details.type == "ach_debit":
                            logger.info("ACH payment already started for: {}".format(invoice['last_name']))
                            continue

                    stripe_invoice_object = stripe.Invoice.pay(invoice['stripe_invoice_id'])
                    # logger.debug()
                    # if stripe_invoice_object.paid or stripe_invoice_object.finalized:
                    #     # if os.environ['DEPLOY_REGION'] == 'local':
                    #     #     os.system("stripe trigger invoice.paid")
                    #     #added finalized because ach payments finalize immediately but do not send 'paid' events for 14 days
                    #     logger.info("Invoice payment succeeded: {}".format(invoice['last_name']))
                    #     #might need to come back and handle this via webhook
                    #     AppDBUtil.updateInvoiceAsPaid(stripe_invoice_id=invoice['stripe_invoice_id'])
                    #     invoice_payment_failed = False

                except Exception as e:
                    invoice_name = invoice['first_name'] + " " + invoice['last_name'] + ", "
                    logger.exception("Error in invoice payment failed for: ".format(invoice_name))
                    if os.environ.get("DEPLOY_REGION") == 'PROD':
                        SendMessagesToClients.sendSMS(to_numbers='9725847364', message=f"Exception: Exception in invoice payment for {invoice_name} with error {e}. Go check the logs!", message_type='to_mo')
                finally:
                    if invoice_payment_failed:
                        pass
                        #logger.error("Invoice payment failed: ".format(invoice['last_name']))
                        #invoice_name = invoice['first_name'] + " " + invoice['last_name'] + ", "

        except Exception as e:
            logger.exception("Error in finding invoices to pay: {}".format(e))

    def setup_recurring_payments_due_today_background_job():
        logger.info("setup_recurring_payments_due_today_background_job started")
        try:
            stripeInstance.setupRecurringPaymentsDueToday()
        except Exception as e:
            logger.exception("Error in setting up recurring payments: {}".format(e))

    def restart_paused_payments_background_job():
        logger.info("restart_paused_payments_background_job started")
        try:
            stripeInstance.restartPausedPayments()
        except Exception as e:
            logger.exception("Error in restarting paused payments: {}".format(e))


    scheduler = BackgroundScheduler(timezone='US/Central')

    if os.environ['DEPLOY_REGION'] == 'local':
        #scheduler.add_job(remind_client_about_invoice_background_job, 'cron', day_of_week='0-6/2', hour='16-16', minute='55-55', start_date=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d'))
        #scheduler.add_job(remind_lead_about_appointment_background_job, 'cron', hour='22', minute='5')

        rpp_minute = datetime.datetime.now().minute+2
        srp_minute = rpp_minute + 1
        pi_minute = srp_minute + 1
        for i in range(1,5):
            rpp_hour = datetime.datetime.now().hour if rpp_minute < 60 else datetime.datetime.now().hour + 1
            srp_hour = datetime.datetime.now().hour if srp_minute < 60 else datetime.datetime.now().hour + 1
            pi_hour = datetime.datetime.now().hour if pi_minute < 60 else datetime.datetime.now().hour + 1
            logger.info(f"dummy background job times are rpp_minute - {rpp_hour}:{rpp_minute%60}, srp_minute - {srp_hour}:{srp_minute%60}, pi_minute - {pi_hour}:{pi_minute%60}" )
            scheduler.add_job(restart_paused_payments_background_job, 'cron', hour=rpp_hour, minute=rpp_minute%60)
            scheduler.add_job(setup_recurring_payments_due_today_background_job, 'cron', hour=srp_hour, minute=srp_minute%60)
            scheduler.add_job(pay_invoice_background_job, 'cron', hour=pi_hour, minute=pi_minute%60)
            rpp_minute = pi_minute + 1
            srp_minute = rpp_minute + 1
            srp_minute = rpp_minute + 1
            pi_minute = srp_minute + 1

        #scheduler.add_job(notify_mo_to_modify_lead_appointment_completion_status_background_job, 'interval', hours=1)
        logger.info("all local background jobs added")

    elif os.environ['DEPLOY_REGION'] == 'dev':
        scheduler.add_job(remind_client_about_invoice_background_job, 'cron', day_of_week='0-6/2', hour='16-16', minute='55-55', start_date=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d'))
        scheduler.add_job(remind_lead_about_appointment_background_job, 'cron', hour='22', minute='5')
        scheduler.add_job(restart_paused_payments_background_job, 'cron', hour='13', minute='55')
        scheduler.add_job(setup_recurring_payments_due_today_background_job, 'cron', hour='14', minute='55')
        scheduler.add_job(pay_invoice_background_job, 'cron', hour='15', minute='55')
        scheduler.add_job(notify_mo_to_modify_lead_appointment_completion_status_background_job, 'interval', hours=111)
        logger.info("all dev background jobs added")


    elif os.environ['DEPLOY_REGION'] == 'prod':
        #BE EXTREMELY CAREFULY WITH THE CRON JOB AND COPIOUSLY TEST. IF YOU GET IT WRONG, YOU CAN EASILY ANNOY A CUSTOMER BY SENDING A MESSAGE EVERY MINUTE OR EVERY SECOND
        scheduler.add_job(remind_client_about_invoice_background_job, 'cron', day_of_week='0-6/2', hour='16-16', minute='55-55',start_date=datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(days=1),'%Y-%m-%d'))
        scheduler.add_job(remind_lead_about_appointment_background_job, 'cron', hour='22', minute='5')
        scheduler.add_job(restart_paused_payments_background_job, 'cron', hour='13', minute='55')
        scheduler.add_job(setup_recurring_payments_due_today_background_job, 'cron', hour='14', minute='55')
        scheduler.add_job(pay_invoice_background_job, 'cron', hour='15', minute='55')
        scheduler.add_job(notify_mo_to_modify_lead_appointment_completion_status_background_job, 'interval', hours=1)
        logger.info("all prod background jobs added")



        #scheduler.add_job(remind_client_about_invoice_background_job, 'cron', hour='16', minute='00')
        # scheduler.add_job(remind_client_about_invoice_background_job, 'cron', day_of_week='sun', hour='19', minute='45')

    # logger.info("remind_client_about_invoice_background_job added")
    # logger.info("remind_lead_about_appointment_background_job added")
    # logger.info("pay_invoice_background_job added")

    # logger.info('Current time with timezone is: {}'.format(datetime.datetime.now().astimezone()))
    # day1 = datetime.datetime.now(pytz.timezone('US/Central'))
    # day2 = datetime.datetime.now(pytz.timezone('US/Central')).date()
    # day3 = pytz.timezone('US/Central').localize(datetime.datetime.now()).strftime('%Y-%m-%d---%H-%M')
    # logger.info('day1 is: {}'.format(day1))
    # logger.info('day2 is: {}'.format(day2))
    # logger.info('day3 is: {}'.format(day3))


    #THE KEY TO GETTING TIMEZONE RIGHT IS SETTING IT AS AN ENVIRONMENT VARIABLE ON DIGITAL OCEAN SERVER
    # import datetime,time
    # stamp = int(datetime.datetime.now().timestamp())
    # date = datetime.datetime.fromtimestamp(stamp)
    # print("1. ",date)
    # print("2. timezone info is: ",datetime.datetime.today().astimezone().tzinfo)
    # print("3. ",datetime.datetime.today())
    # print("4. ",datetime.datetime.fromtimestamp(int(time.mktime(datetime.datetime.today().timetuple()))))

    scheduler.start()


@server.route('/post_signup_checkout',methods=['POST'])
def post_signup_checkout():
    payment_and_signup_data = request.form.to_dict()

    chosen_mode_of_payment = payment_and_signup_data.get('installment-payment', '') if payment_and_signup_data.get('installment-payment', '') != '' else payment_and_signup_data.get('full-payment', '') if payment_and_signup_data.get('full-payment', '') != '' else payment_and_signup_data.get('payment-options', '') if payment_and_signup_data.get('payment-options', '') != '' else ''
    logger.info("payment_and_signup_data[stripe_info] is {}".format(payment_and_signup_data['stripe_info']))
    stripe_info = ast.literal_eval(payment_and_signup_data['stripe_info'])
    stripe_pk = os.environ.get('stripe_pk')
    if chosen_mode_of_payment.__contains__('ach'):
        return render_template('plaid_checkout.html', stripe_info=stripe_info, chosen_mode_of_payment=chosen_mode_of_payment, payment_and_signup_data=payment_and_signup_data)
    else:
        return render_template('stripe_checkout.html', stripe_info=stripe_info, chosen_mode_of_payment=chosen_mode_of_payment, stripe_pk=stripe_pk, payment_and_signup_data=payment_and_signup_data)


@server.route('/complete_signup',methods=['POST'])
def complete_signup():
    try:
        client_info,products_info,showACHOverride = AppDBUtil.getTransactionDetails(request.form.to_dict()['transaction_id'])
    except Exception as e:
        print(e)
        flash('An error has occurred. Contact Mo.')
        return redirect(url_for('input_transaction_id'))
    if not client_info and not products_info:
        flash('You might have put in the wrong code. Try again or contact Mo.')
        return redirect(url_for('input_transaction_id'))

    stripe_info = parseDataForStripe(client_info)
    response = make_response(render_template('complete_signup.html', stripe_info=stripe_info, client_info=client_info,products_info=products_info,showACHOverride=showACHOverride,askForStudentInfo=client_info.get('ask_for_student_info',''),askForStudentAvailability=client_info.get('ask_for_student_availability',''),prospect_id=client_info.get('prospect_id','')))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"  # HTTP 1.1.
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0.
    response.headers["Expires"] = "0"  # Proxies.

    return response