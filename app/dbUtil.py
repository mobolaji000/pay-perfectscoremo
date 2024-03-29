from app.models import Transaction,InstallmentPlan,InvoiceToBePaid,Prospect,Student,Lead
from app import db
from app.config import stripe
from datetime import datetime,timedelta
import re
import pytz
import uuid
from dateutil.parser import parse
import logging
import traceback
from sqlalchemy.dialects.postgresql import insert

#from app.service import SendMessagesToClients

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter =  logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)20s() - %(lineno)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

#ADDED TO TURN DOUBLE FLASK LOGGING OFF FLASK LOCAL
from app import server
from flask.logging import default_handler
server.logger.removeHandler(default_handler)
server.logger.handlers.clear()


class AppDBUtil():
    def __init__(self):
        pass

    @classmethod
    def createProspect(cls, prospectData={}):
        prospect_id = "p-"+str(uuid.uuid4().int >> 64)[:6]
        prospect_salutation = prospectData.get('salutation', '')
        prospect_first_name = prospectData.get('first_name', '')
        prospect_last_name = prospectData.get('last_name', '')
        prospect_phone_number = prospectData.get('phone_number', '999')
        prospect_email = prospectData.get('email', '')
        how_did_they_hear_about_us = prospectData.get('how_did_they_hear_about_us', '')
        details_on_how_they_heard_about_us = prospectData.get('details_on_how_they_heard_about_us', '')
        recent_test_score = -1 if prospectData.get('recent_test_score', '') == '' else prospectData.get('recent_test_score')
        grade_level = prospectData.get('grade_level', '')
        lead_id = prospectData.get('leadSearchResults','')

        existing_prospect = db.session.query(Prospect).filter_by(prospect_phone_number=prospect_phone_number).first() or db.session.query(Prospect).filter_by(prospect_email=prospect_email).first()

        if existing_prospect:
            prospect = existing_prospect
        else:
            prospect = Prospect(prospect_id=prospect_id,prospect_salutation=prospect_salutation,prospect_first_name=prospect_first_name, prospect_last_name=prospect_last_name,prospect_phone_number=prospect_phone_number, prospect_email=prospect_email,
                                how_did_they_hear_about_us=how_did_they_hear_about_us,details_on_how_they_heard_about_us=details_on_how_they_heard_about_us,recent_test_score=recent_test_score,grade_level=grade_level,lead_id=lead_id)
            db.session.add(prospect)
            cls.executeDBQuery()

        # if lead_id != '':
        #     cls.modifyLeadInfo(lead_id, {'appointment_completed': 'yes'})

        return prospect

    @classmethod
    def createOrModifyClientTransaction(cls, clientData={}, transaction_id=None, action=''):
        existing_transaction_ids = AppDBUtil.getAllTransactionIds()
        if transaction_id:
            transaction_id = transaction_id
        else:
            transaction_id = "t-"+str(uuid.uuid4().int>>64)[:6]
            while transaction_id in  existing_transaction_ids:
                logger.info("Transaction id {} already exists".format(transaction_id))
                transaction_id = "t-" + str(uuid.uuid4().int >> 64)[:6]

        prospect_id = clientData.get('prospect_id','')
        stripe_customer_id = clientData.get('stripe_customer_id','')
        first_name = clientData.get('first_name','')
        last_name = clientData.get('last_name','')
        salutation = clientData.get('salutation','')
        phone_number = clientData.get('phone_number','999')
        email = clientData.get('email','')
        was_diagnostic_purchased = clientData.get('was_diagnostic_purchased', '')
        diag_units = 0 if clientData.get('diag_units','') == '' else clientData.get('diag_units','')
        diag_total = 0 if clientData.get('diag_total','') == '' else clientData.get('diag_total','')
        was_test_prep_purchased = clientData.get('was_test_prep_purchased','')
        tp_product = clientData.get('tp_product','')
        tp_units = 0 if clientData.get('tp_units','') == '' else clientData.get('tp_units','')
        tp_total = 0 if clientData.get('tp_total','') == '' else clientData.get('tp_total','')
        was_college_apps_purchased = clientData.get('was_college_apps_purchased', '')
        college_apps_product = clientData.get('college_apps_product','')
        college_apps_units = 0 if clientData.get('college_apps_units','') == '' else clientData.get('college_apps_units','')
        college_apps_total = 0 if clientData.get('college_apps_total','') == '' else clientData.get('college_apps_total','')
        adjust_total = 0 if clientData.get('adjust_total','') == '' else clientData.get('adjust_total','')
        adjustment_explanation = clientData.get('adjustment_explanation','')
        transaction_total = 0 if clientData.get('transaction_total','') == '' else clientData.get('transaction_total','')
        installment_counter = 0 if clientData.get('installment_counter','') == '' else int(clientData.get('installment_counter',''))#-1
        # client-side counter is always one more; get the actual number here
        ask_for_student_info = clientData.get('ask_for_student_info','')
        ask_for_student_availability = clientData.get('ask_for_student_availability', '')
        make_payment_recurring = clientData.get('make_payment_recurring')
        recurring_payment_frequency = 0 if clientData.get('recurring_payment_frequency','') == '' else clientData.get('recurring_payment_frequency','')
        recurring_payment_start_date = None if clientData.get('recurring_payment_start_date', '') == '' else clientData.get('recurring_payment_start_date')
        pause_payment = clientData.get('pause_payment')
        paused_payment_resumption_date = None if clientData.get('paused_payment_resumption_date', '') == '' else clientData.get('paused_payment_resumption_date')
        does_customer_payment_info_exist = 'yes' if clientData.get('does_customer_payment_info_exist',None) else 'no'
        pay_automatically = 'yes' if clientData.get('pay_automatically', None) else 'no'



        number_of_rows_modified = None
        if action=='create':

            transaction = Transaction(transaction_id=transaction_id, prospect_id=prospect_id, stripe_customer_id=stripe_customer_id, first_name=first_name, last_name=last_name,salutation=salutation,
                                  phone_number=phone_number, email=email, was_diagnostic_purchased=was_diagnostic_purchased, diag_units=diag_units,
                                  diag_total=diag_total, was_test_prep_purchased=was_test_prep_purchased, tp_product=tp_product, tp_units=tp_units,
                                  tp_total=tp_total, was_college_apps_purchased=was_college_apps_purchased, college_apps_product=college_apps_product,
                                  college_apps_units=college_apps_units, college_apps_total=college_apps_total,adjust_total=adjust_total, adjustment_explanation=adjustment_explanation,
                                transaction_total=transaction_total, installment_counter=installment_counter,ask_for_student_info=ask_for_student_info,ask_for_student_availability=ask_for_student_availability,
                                      does_customer_payment_info_exist=does_customer_payment_info_exist,make_payment_recurring=make_payment_recurring,recurring_payment_frequency=recurring_payment_frequency,
                                      recurring_payment_start_date=recurring_payment_start_date,pause_payment=pause_payment,paused_payment_resumption_date=paused_payment_resumption_date,pay_automatically=pay_automatically)


            db.session.add(transaction)

        elif action=='modify':
            #what happens in the unlikely event that 2 rows have the same transaction code?
            number_of_rows_modified = db.session.query(Transaction).filter_by(transaction_id=transaction_id).update\
                ({"stripe_customer_id": stripe_customer_id,"first_name": first_name,"last_name": last_name,"phone_number": phone_number,"salutation":salutation,
                        "email": email,"was_diagnostic_purchased": was_diagnostic_purchased,"diag_units": diag_units,"diag_total": diag_total,
                        "was_test_prep_purchased": was_test_prep_purchased,"tp_product": tp_product,"tp_units": tp_units,"tp_total": tp_total,
                        "was_college_apps_purchased": was_college_apps_purchased,"college_apps_product": college_apps_product,"college_apps_units": college_apps_units,
                        "college_apps_total": college_apps_total,"adjust_total": adjust_total,"adjustment_explanation": adjustment_explanation,
                  "transaction_total": transaction_total, "installment_counter":installment_counter, "does_customer_payment_info_exist":does_customer_payment_info_exist,
                  "ask_for_student_info":ask_for_student_info,"ask_for_student_availability":ask_for_student_availability,"make_payment_recurring":make_payment_recurring,"recurring_payment_frequency":recurring_payment_frequency,
                  "recurring_payment_start_date":recurring_payment_start_date,"pause_payment":pause_payment,"paused_payment_resumption_date":paused_payment_resumption_date,"pay_automatically":pay_automatically})

            logger.info(f"Number of transaction rows modified is: {number_of_rows_modified}") #printing of rows modified to logs to help with auditing

        cls.executeDBQuery()

        if not cls.isTransactionPaymentStarted(transaction_id):
            cls.createOrModifyInstallmentPlan(clientData=clientData, transaction_id=transaction_id)

        return transaction_id,number_of_rows_modified


    @classmethod
    def modifyTransactionBasedOnPauseUnpauseStatus(cls,clientData,transaction_id):
        pause_payment = clientData.get('pause_payment')
        paused_payment_resumption_date = None if clientData.get('paused_payment_resumption_date', '') == '' else clientData.get('paused_payment_resumption_date')
        recurring_payment_start_date = None if clientData.get('recurring_payment_start_date', '') == '' else clientData.get('recurring_payment_start_date')

        if (int(clientData['installment_counter']) > 1) and cls.isTransactionPaymentStarted(transaction_id):
            cls.modifyPauseStatusOnInvoicesToBePaid(transaction_id, pause_payment, paused_payment_resumption_date)
            #cls.pauseInstallmentPaymentInvoices(transaction_id, pause_payment, paused_payment_resumption_date)
        elif (clientData.get('recurring_payment_start_date')):
            pass
            #cls.pauseRecurringPayment(transaction_id, pause_payment, paused_payment_resumption_date, recurring_payment_start_date)

    @classmethod
    def createOrModifyInvoiceToBePaid(cls, first_name=None, last_name=None, phone_number=None, email=None, transaction_id=None, stripe_customer_id=None, stripe_invoice_id=None, payment_date=None, payment_amount=None):
        #
        invoice = InvoiceToBePaid(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email,
                                  transaction_id=transaction_id, stripe_customer_id=stripe_customer_id,
                                  payment_date=payment_date, payment_amount=payment_amount,
                                  stripe_invoice_id=stripe_invoice_id)

        db.session.add(invoice)
        print("invoice to be paid created is: ", invoice)
        cls.executeDBQuery()

    @classmethod
    def modifyPauseStatusOnInvoicesToBePaid(cls, transaction_id=None, pause_payment=None, paused_payment_resumption_date=None):
        try:
            if pause_payment == 'yes':
                invoices_to_pause = cls.findInvoicesToPause(transaction_id)

                if invoices_to_pause:
                    logger.info(f'Running pauseInstallmentPaymentInvoices on {invoices_to_pause[0].transaction_id} for which invoices have been created for customer.')
                    if paused_payment_resumption_date:
                        invoice_payment_dates_to_update = []

                        for k, invoice in enumerate(invoices_to_pause):
                            if k == 0:
                                invoice_payment_dates_to_update.append(datetime.strptime(paused_payment_resumption_date, '%Y-%m-%d').date())
                            else:
                                difference_between_this_invoice_date_and_previous_invoice_date = (invoices_to_pause[k].payment_date - invoices_to_pause[k - 1].payment_date).days
                                invoice_payment_dates_to_update.append(invoice_payment_dates_to_update[k-1] + timedelta(days=difference_between_this_invoice_date_and_previous_invoice_date))


                        for k, invoice in enumerate(invoices_to_pause):
                            logger.info(f'Modifying payment date on {invoice.id}.')
                            invoice.payment_date = invoice_payment_dates_to_update[k]
                            db.session.add(invoice)

                    else:
                        for invoice in invoices_to_pause:
                            logger.info(f'Modifying payment date on {invoice.id}.')
                            invoice.payment_date = datetime.strptime(paused_payment_resumption_date, '%Y-%m-%d').date()
                            db.session.add(invoice)

                    cls.executeDBQuery()
        except Exception as e:
            # if any kind of exception occurs, rollback transaction
            db.session.rollback()
            traceback.print_exc()
        finally:
            db.session.close()

    @classmethod
    def createOrModifyInstallmentPlan(cls, clientData={}, transaction_id=None):

        existing_installment_plan = db.session.query(InstallmentPlan).filter_by(transaction_id=transaction_id).first()
        if existing_installment_plan:
            db.session.delete(existing_installment_plan)
            cls.executeDBQuery()

        if int(clientData['installment_counter']) > 1:
            installment_plan = InstallmentPlan(transaction_id=transaction_id, stripe_customer_id=clientData['stripe_customer_id'], first_name=clientData['first_name'], last_name=clientData['last_name'], phone_number=clientData['phone_number'],
                                               email=clientData['email'])
            db.session.add(installment_plan)
            print("installment plan created is: ", installment_plan)
            cls.executeDBQuery()

            installments = {}
            print("number of installments is " + str(int(clientData['installment_counter']) - 1))

            for k in range(1, int(clientData['installment_counter'])):
                print("current installment being updated is " + str(k))
                installments.update({'date_' + str(k): clientData['date_' + str(k)], 'amount_' + str(k): clientData['amount_' + str(k)]})

            installment_plan = db.session.query(InstallmentPlan).filter_by(transaction_id=transaction_id)
            number_of_rows_modified = installment_plan.update(installments)
            print("number of installment rows added or modified is: ", number_of_rows_modified)
            cls.executeDBQuery()

        else:
            print("No installment dates created/modified")

            # date_and_amount_index = 1
            # for k in range(1, 13):
            #     print("current installment being updated is " + str(k))
            #     if 'date_' + str(k) in clientData:
            #         installments.update({'date_' + str(date_and_amount_index): clientData[f'date_{k}'] + timedelta(days=difference_in_installment_dates_due_to_pause), 'amount_' + str(date_and_amount_index): clientData[f'amount_{k}']})
            #         date_and_amount_index = date_and_amount_index + 1



    @classmethod
    def is_date(cls,string_date, fuzzy=False):
        """
        Return whether the string can be interpreted as a date.

        :param string: str, string to check for date
        :param fuzzy: bool, ignore unknown tokens in string if True
        """
        try:
            parse(string_date, fuzzy=fuzzy)
            return True

        except ValueError as v:
            return False

    @classmethod
    def deleteInvoiceToBePaid(cls, invoiceTransactionCode,stripeInvoiceId):
        invoice_to_be_paid = InvoiceToBePaid.query.filter_by(transaction_id=invoiceTransactionCode).first()
        db.session.delete(invoice_to_be_paid)
        cls.executeDBQuery()
        #you might have to chnage the delete to the stripe version of "make inactive" because if an existing method on file was attempted
        # and it failed, you might not be able to delete that invoice, eventhough you can create a new one to charge
        stripe.Invoice.delete(stripeInvoiceId,)

    @classmethod
    def deleteTransactionAndInstallmentPlan(cls, transaction_id_to_delete):
        existing_invoices = InvoiceToBePaid.query.filter_by(transaction_id=transaction_id_to_delete).all()
        for existing_invoice in existing_invoices:
            AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)

        existing_installment_plan = db.session.query(InstallmentPlan).filter_by(transaction_id=transaction_id_to_delete).first()
        if existing_installment_plan:
            db.session.delete(existing_installment_plan)

        transaction = Transaction.query.filter_by(transaction_id=transaction_id_to_delete).first()
        db.session.delete(transaction)

        cls.executeDBQuery()

    @classmethod
    def modifyTransactionDetails(cls, data_to_modify):
        return cls.createOrModifyClientTransaction(clientData=data_to_modify, transaction_id=data_to_modify['transaction_id'], action='modify')


    @classmethod
    def updateAmountPaidAgainstTransaction(cls,transaction_id,amount_paid):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        transaction.amount_from_transaction_paid_so_far = transaction.amount_from_transaction_paid_so_far + amount_paid
        cls.executeDBQuery()
        return transaction

    @classmethod
    def updatePausePaymentStatus(cls, transaction_id, pause_payment, paused_payment_resumption_date):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        transaction.pause_payment = pause_payment
        transaction.paused_payment_resumption_date =  paused_payment_resumption_date
        cls.executeDBQuery()
        return transaction

    @classmethod
    def updateInvoiceAsPaid(cls, stripe_invoice_id=None):
        invoice = InvoiceToBePaid.query.filter_by(stripe_invoice_id=stripe_invoice_id).first()
        if invoice:
            invoice.payment_made = True
            cls.executeDBQuery()

    @classmethod
    def findInvoicesToPay(cls):
        try:

            invoices_to_pay = db.session.query(
                InvoiceToBePaid
            ).join(
                Transaction, InvoiceToBePaid.transaction_id == Transaction.transaction_id
            ).filter(
                ((Transaction.pause_payment == "no" ) & (InvoiceToBePaid.payment_made == False) & (InvoiceToBePaid.payment_date <= datetime.today()))
            ).all()

            #invoices_to_pay = db.session.query(InvoiceToBePaid).filter((InvoiceToBePaid.payment_made == False) & (InvoiceToBePaid.payment_date <= datetime.today())).all()

            # for transaction in result:
            #     logger.info("results are: {}".format(result))
            #     logger.info("eligible transactions for automatic invoice payment are: {}".format(transaction))
            # for invoices_to_pay in result:
            logger.info("invoices_to_pay are: {}".format(invoices_to_pay))
            search_results = []
            if invoices_to_pay:
                for invoice in invoices_to_pay:
                    invoice_details = {}
                    invoice_details['first_name'] = invoice.first_name
                    invoice_details['last_name'] = invoice.last_name
                    invoice_details['payment_amount'] = invoice.payment_amount
                    invoice_details['stripe_invoice_id'] = invoice.stripe_invoice_id
                    print(invoice_details)
                    print(" ")
                    search_results.append(invoice_details)
            return search_results
        except Exception as e:
            # if any kind of exception occurs, rollback transaction
            db.session.rollback()
            traceback.print_exc()
        finally:
            db.session.close()

    @classmethod
    def findInvoicesToPause(cls,transaction_id):
        try:
            invoices_to_pause = db.session.query(
                InvoiceToBePaid
            ).join(
                Transaction, InvoiceToBePaid.transaction_id == Transaction.transaction_id
            ).filter(
                ((Transaction.pause_payment == "yes") & (InvoiceToBePaid.payment_made == False) & (Transaction.transaction_id == transaction_id))

            ).order_by(InvoiceToBePaid.payment_date).all()

            return invoices_to_pause
        except Exception as e:
            # if any kind of exception occurs, rollback transaction
            db.session.rollback()
            traceback.print_exc()
        finally:
            db.session.close()



    @classmethod
    def findLeadsToReceiveReminders(cls):
        try:
            leadsToReceiveReminders = Lead.query.filter((Lead.appointment_completed != 'yes') & (Lead.appointment_date_and_time != None)).all()

            logger.info("Leads to receive reminders are: {}".format(leadsToReceiveReminders))
            search_results = []
            for lead in leadsToReceiveReminders:
                lead_details = {}
                lead_details['lead_id'] = lead.lead_id
                lead_details['lead_salutation'] = lead.lead_salutation
                lead_details['lead_name'] = lead.lead_name
                lead_details['lead_phone_number'] = lead.lead_phone_number
                lead_details['lead_email'] = lead.lead_email
                lead_details['appointment_date_and_time'] = lead.appointment_date_and_time.astimezone(pytz.timezone('US/Central'))
                search_results.append(lead_details)


                # logger.info("Time before conversion is: {}".format(lead.appointment_date_and_time))
                # logger.info("Time after conversion is: {}".format(lead.appointment_date_and_time.astimezone(pytz.timezone('US/Central'))))

            return search_results
        except Exception as e:
            # if any kind of exception occurs, rollback lead
            db.session.rollback()
            traceback.print_exc()
        finally:
            db.session.close()

    @classmethod
    def findLeadsWithAppointmentsInTheLastHour(cls):
        try:
            searchEndDate = datetime.now()#datetime.now(pytz.timezone('US/Central'))
            logger.info("searchEndDate: {}".format(searchEndDate.strftime('%Y-%m-%dT%H:%M:%S')))
            searchStartDate = datetime.now() - timedelta(hours=1)#datetime.now(pytz.timezone('US/Central')) - timedelta(hours=1)
            logger.info("searchStartDate: {}".format(searchStartDate.strftime('%Y-%m-%dT%H:%M:%S')))
            leadsWithAppointmentsInTheLastHour = Lead.query.filter(Lead.appointment_completed != 'yes').filter(Lead.appointment_date_and_time <= searchEndDate).filter(Lead.appointment_date_and_time >= searchStartDate).order_by(Lead.appointment_date_and_time.desc()).all()


            logger.info("Leads with appointments in the last hour are: {}".format(leadsWithAppointmentsInTheLastHour))
            search_results = []
            for lead in leadsWithAppointmentsInTheLastHour:
                lead_details = {}
                lead_details['lead_id'] = lead.lead_id
                lead_details['lead_salutation'] = lead.lead_salutation
                lead_details['lead_name'] = lead.lead_name
                lead_details['appointment_date_and_time'] = lead.appointment_date_and_time.astimezone(pytz.timezone('US/Central'))
                search_results.append(lead_details)
                logger.info("Individual lead is: {}".format(lead_details))

            return search_results
        except Exception as e:
            # if any kind of exception occurs, rollback lead
            db.session.rollback()
            logger.exception(e)
        finally:
            db.session.close()


    @classmethod
    def findClientsToReceiveReminders(cls):
        try:
            transaction_details = Transaction.query.filter((Transaction.pause_payment == "no") & (Transaction.payment_started == False)).all()

            search_results = []
            for transaction in transaction_details:
                client = {}
                client['first_name'] = transaction.first_name
                client['last_name'] = transaction.last_name
                client['phone_number'] = transaction.phone_number
                client['email'] = transaction.email
                client['transaction_id'] = transaction.transaction_id
                client['payment_started'] = str(transaction.payment_started)
                search_results.append(client)

            return search_results
        except Exception as e:
            # if any kind of exception occurs, rollback transaction
            db.session.rollback()
            traceback.print_exc()
        finally:
            db.session.close()

    @classmethod
    def searchTransactions(cls, search_query):
        if search_query.isdigit():
            transaction_details = Transaction.query.filter_by(phone_number=search_query).order_by(Transaction.date_created.desc()).all()
        elif search_query.startswith("t-"):
            transaction_details = Transaction.query.filter_by(transaction_id=search_query).order_by(Transaction.date_created.desc()).all()
        elif "@" in search_query:
            transaction_details = Transaction.query.filter_by(email=search_query).order_by(Transaction.date_created.desc()).all()
        elif cls.is_date(search_query):
            #do something to get the date in the right format first
            transaction_details = Transaction.query.filter_by(date_created=search_query).order_by(Transaction.date_created.desc()).all()
        else:
            transaction_details = Transaction.query.filter((Transaction.first_name == search_query.capitalize()) | (Transaction.last_name == search_query.capitalize())
                                                       | (Transaction.first_name == search_query.lower()) | (Transaction.last_name == search_query.lower())
                                                       | (Transaction.first_name == search_query) | (Transaction.last_name == search_query))\
                .order_by(Transaction.date_created.desc()).all()




        search_results = []
        for transaction in transaction_details:
            client = {}
            client['salutation'] = transaction.salutation
            client['first_name'] = transaction.first_name
            client['last_name'] = transaction.last_name
            client['salutation'] = transaction.salutation
            client['phone_number'] = transaction.phone_number
            client['email'] = transaction.email
            client['stripe_customer_id'] = transaction.stripe_customer_id
            client['adjust_total'] = transaction.adjust_total
            client['adjustment_explanation'] = transaction.adjustment_explanation
            client['transaction_total'] = transaction.transaction_total
            client['date_created'] = transaction.date_created.strftime("%m/%d/%Y")
            client['transaction_id'] = transaction.transaction_id
            client['was_diagnostic_purchased'] = transaction.was_diagnostic_purchased
            client['diag_units'] = transaction.diag_units
            client['diag_total'] = transaction.diag_total
            client['was_test_prep_purchased'] = transaction.was_test_prep_purchased
            client['tp_units'] = transaction.tp_units
            client['tp_total'] = transaction.tp_total
            client['was_college_apps_purchased'] = transaction.was_college_apps_purchased
            client['college_apps_units'] = transaction.college_apps_units
            client['college_apps_total'] = transaction.college_apps_total
            client['installment_counter'] = transaction.installment_counter
            client['payment_started'] = str(transaction.payment_started)
            client['prospect_id'] = str(transaction.prospect_id)
            client['ask_for_student_info'] = transaction.ask_for_student_info
            client['ask_for_student_availability'] = transaction.ask_for_student_availability
            client['does_customer_payment_info_exist'] = transaction.does_customer_payment_info_exist
            client['pay_automatically'] = transaction.pay_automatically

            client['make_payment_recurring'] = transaction.make_payment_recurring
            client['recurring_payment_frequency'] = transaction.recurring_payment_frequency if transaction.recurring_payment_frequency else 'null'
            client['recurring_payment_start_date'] = transaction.recurring_payment_start_date.strftime("%Y-%m-%d") if transaction.recurring_payment_start_date else ''
            client['pause_payment'] = transaction.pause_payment
            client['paused_payment_resumption_date'] = transaction.paused_payment_resumption_date.strftime("%Y-%m-%d") if transaction.paused_payment_resumption_date else ''

            prospect_details = Prospect.query.filter_by(prospect_id=transaction.prospect_id).first()
            client['how_did_they_hear_about_us'] = prospect_details.how_did_they_hear_about_us
            client['details_on_how_they_heard_about_us'] = prospect_details.details_on_how_they_heard_about_us
            client['recent_test_score'] = '' if prospect_details.recent_test_score == -1 else prospect_details.recent_test_score
            client['grade_level'] = prospect_details.grade_level
            client['lead_id'] = prospect_details.lead_id


            installment_details = InstallmentPlan.query.filter_by(transaction_id=transaction.transaction_id).first()

            if installment_details:
                logger.info(f"installment_details is {installment_details.__dict__}")
                installments = {}
                for k in range(1, int(transaction.installment_counter)):
                    installments.update({'date_' + str(k): installment_details.__dict__['date_' + str(k)].strftime("%m/%d/%Y"), 'amount_' + str(k): installment_details.__dict__['amount_' + str(k)]})

                client['installment_details'] = installments


            search_results.append(client)
        logger.info(f"Search results are {search_results}")
        return search_results

    @classmethod
    def getTransactionDetails(cls,transaction_id):
        showACHOverride = False
        transaction_id = transaction_id.strip().lower()
        if 'ach' in transaction_id:
            showACHOverride = True
            transaction_id = transaction_id.split('ach')[0]

        admin_transaction_details = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        admin_transaction_details.turn_on_installments = True if admin_transaction_details.installment_counter > 1 else False
        return cls.computeClientTransactionDetails(admin_transaction_details,showACHOverride)

    @classmethod
    def updateTransactionPaymentStarted(cls, transaction_id):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        transaction.payment_started = True
        cls.executeDBQuery()

    @classmethod
    def updateTransactionDoesCustomerPaymentInfoExist(cls, transaction_id):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        transaction.does_customer_payment_info_exist = 'yes'
        cls.executeDBQuery()

    @classmethod
    def isTransactionPaymentStarted(cls, transaction_id):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        return transaction.payment_started

    # @classmethod
    # def pauseOneTimePayment(cls, transaction_id, pause_payment, paused_payment_resumption_date):
    #     transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
    #     transaction.pause_payment = pause_payment
    #     transaction.paused_payment_resumption_date = paused_payment_resumption_date
    #
    #     cls.executeDBQuery()

    @classmethod
    def pauseRecurringPayment(cls, transaction_id, pause_payment, paused_payment_resumption_date, recurring_payment_start_date):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        if pause_payment == 'yes':
            payment_date = recurring_payment_start_date
            if paused_payment_resumption_date:
                if paused_payment_resumption_date > payment_date:
                    payment_date = paused_payment_resumption_date

            transaction.recurring_payment_start_date = payment_date
            cls.executeDBQuery()

    @classmethod
    def pauseInstallmentPaymentInvoices(cls, transaction_id, pause_payment, paused_payment_resumption_date):

        if pause_payment == 'yes':
            existing_invoices = InvoiceToBePaid.query.filter_by(transaction_id=transaction_id).order_by(InvoiceToBePaid.payment_date.asc()).all()#.filter_by(payment_made=False)
            if existing_invoices:
                logger.info(f'Running pauseInstallmentPaymentInvoices on {transaction_id} for which invoices have been created for customer.')
                if paused_payment_resumption_date:
                    index_of_earliest_unpaid_invoice = 0
                    invoice_dates_to_update = [None] * len(existing_invoices)

                    for i,e in enumerate(existing_invoices):
                        if not e.payment_made:
                            index_of_earliest_unpaid_invoice = i if index_of_earliest_unpaid_invoice == 0 else index_of_earliest_unpaid_invoice
                            if index_of_earliest_unpaid_invoice == i:
                                invoice_dates_to_update[i] = paused_payment_resumption_date
                            else:
                                difference_between_this_payment_date_and_previous_payment_date = (existing_invoices[i].payment_date - existing_invoices[i-1].payment_date).days
                                invoice_dates_to_update[i] = invoice_dates_to_update[i-1] + timedelta(days=difference_between_this_payment_date_and_previous_payment_date)
                        else:
                            invoice_dates_to_update[i] = e.payment_date

                    installment_dates_to_update_as_dict = {}
                    for i,e in enumerate(existing_invoices):
                        e.payment_date = invoice_dates_to_update[i]
                        #installment_dates_to_update_as_dict.update({'date_' + str(int(i+1)): installment_dates_to_update[i]})

                    # existing_installment_plan = db.session.query(InstallmentPlan).filter_by(transaction_id=transaction_id).first()
                    # number_of_rows_modified = existing_installment_plan.update(installment_dates_to_update_as_dict)
                    # logger.info(f"number of installment rows with pause status modified is: {number_of_rows_modified}")

                else:
                    for i,e in enumerate(existing_invoices):
                        e.payment_date = paused_payment_resumption_date
            else:
                logger.info(f'Ran pauseInstallmentPaymentInvoices for {transaction_id} for which NO invoices have been created for customer.')


            cls.executeDBQuery()
    @classmethod
    def createStudentData(cls, studentData):
        try:
            student_id = "s-" + str(uuid.uuid4().int >> 64)[:6]
            prospect_id = studentData.get('prospect_id', '')
            student_first_name = studentData.get('student_first_name', '')
            student_last_name = studentData.get('student_last_name', '')
            student_phone_number = studentData.get('student_phone_number', '999')
            student_email = studentData.get('student_email', '')
            parent_1_salutation = studentData.get('parent_1_salutation', '')
            parent_1_first_name = studentData.get('parent_1_first_name', '')
            parent_1_last_name = studentData.get('parent_1_last_name', '')
            parent_1_phone_number = studentData.get('parent_1_phone_number', '')
            parent_1_email = studentData.get('parent_1_email', '')
            parent_2_salutation = studentData.get('parent_2_salutation', '')
            parent_2_first_name = studentData.get('parent_2_first_name', '')
            parent_2_last_name = studentData.get('parent_2_last_name', '')
            parent_2_phone_number = studentData.get('parent_2_phone_number', '')
            parent_2_email = studentData.get('parent_2_email', '')

            recent_test_score = -1 if studentData.get('recent_test_score', '') == '' else studentData.get('recent_test_score')
            grade_level = studentData.get('grade_level', '')

            statement = insert(Student).values(student_id=student_id,prospect_id=prospect_id,student_first_name=student_first_name,student_last_name=student_last_name,student_phone_number=student_phone_number,student_email=student_email,
                               parent_1_salutation=parent_1_salutation,parent_1_first_name=parent_1_first_name,parent_1_last_name=parent_1_last_name,parent_1_phone_number=parent_1_phone_number,parent_1_email=parent_1_email,recent_test_score=recent_test_score,grade_level=grade_level,
                               parent_2_salutation=parent_2_salutation,parent_2_first_name=parent_2_first_name,parent_2_last_name=parent_2_last_name,parent_2_phone_number=parent_2_phone_number,parent_2_email=parent_2_email)

            updated_content = dict(student_id=student_id,prospect_id=prospect_id,student_first_name=student_first_name,student_last_name=student_last_name,student_phone_number=student_phone_number,recent_test_score=recent_test_score,grade_level=grade_level,
                               parent_1_salutation=parent_1_salutation,parent_1_first_name=parent_1_first_name,parent_1_last_name=parent_1_last_name,parent_1_phone_number=parent_1_phone_number,parent_1_email=parent_1_email,
                               parent_2_salutation=parent_2_salutation,parent_2_first_name=parent_2_first_name,parent_2_last_name=parent_2_last_name,parent_2_phone_number=parent_2_phone_number,parent_2_email=parent_2_email)

            statement = statement.on_conflict_do_update(
                index_elements=['student_email'],
                set_=updated_content
            )

            db.session.execute(statement)
            cls.executeDBQuery()

        except Exception as e:
            logger.exception(e)
            raise e



    @classmethod
    def computeClientTransactionDetails(cls,admin_transaction_details,showACHOverride):
        client_info = {}
        products_info = []
        try:
            client_info['salutation'] = admin_transaction_details.salutation
            client_info['first_name'] = admin_transaction_details.first_name
            client_info['last_name'] = admin_transaction_details.last_name
            client_info['phone_number'] = admin_transaction_details.phone_number
            client_info['email'] = admin_transaction_details.email
            client_info['prospect_id'] = admin_transaction_details.prospect_id
            client_info['stripe_customer_id'] = admin_transaction_details.stripe_customer_id
            client_info['adjust_total'] = admin_transaction_details.adjust_total
            client_info['adjustment_explanation'] = admin_transaction_details.adjustment_explanation
            client_info['transaction_total'] = admin_transaction_details.transaction_total
            client_info['transaction_id'] = admin_transaction_details.transaction_id
            client_info['payment_started'] = admin_transaction_details.payment_started
            client_info['installment_counter'] = admin_transaction_details.installment_counter
            client_info['ask_for_student_info'] = admin_transaction_details.ask_for_student_info
            client_info['ask_for_student_availability'] = admin_transaction_details.ask_for_student_availability
            client_info['showACHOverride'] = str(showACHOverride)
            client_info['does_customer_payment_info_exist'] = admin_transaction_details.does_customer_payment_info_exist

            client_info['make_payment_recurring'] = admin_transaction_details.make_payment_recurring
            client_info['recurring_payment_frequency'] = admin_transaction_details.recurring_payment_frequency
            client_info['recurring_payment_start_date'] = admin_transaction_details.recurring_payment_start_date
            client_info['pause_payment'] = admin_transaction_details.pause_payment
            client_info['paused_payment_resumption_date'] = admin_transaction_details.paused_payment_resumption_date


            #added to get data fro not charging clients for credit card payment for diagnostics
            client_info['diag_total'] = admin_transaction_details.diag_total

            #logger.info(f"transaction id {admin_transaction_details.transaction_id} with showACHOverride value {showACHOverride} has {int(admin_transaction_details.installment_counter)-1} installments")

            if admin_transaction_details.was_diagnostic_purchased:
                next_product = {}
                next_product['number_of_product_units'] = admin_transaction_details.diag_units
                next_product['per_product_cost'] = 50
                next_product['total_product_cost'] = admin_transaction_details.diag_total
                next_product['product_description'] = "Diagnostic/Consultation"
                products_info.append(next_product)

            if admin_transaction_details.was_test_prep_purchased:
                next_product = {}
                next_product['number_of_product_units'] = admin_transaction_details.tp_units
                next_product['per_product_cost'] = admin_transaction_details.tp_product
                next_product['total_product_cost'] = admin_transaction_details.tp_total

                test_prep_product_code = admin_transaction_details.was_test_prep_purchased.split('-')
                if len(test_prep_product_code) == 4:
                    test_prep_location = test_prep_product_code[1].capitalize()+" "+test_prep_product_code[2].capitalize()
                    test_prep_duration = str(int(test_prep_product_code[3][:2]))+"-Weeks" if int(test_prep_product_code[3][:2])>1 else str(int(test_prep_product_code[3][:2]))+"-Week"
                else:
                    test_prep_location = test_prep_product_code[1].capitalize()
                    test_prep_duration = str(int(test_prep_product_code[2][:2]))+"-Weeks" if int(test_prep_product_code[2][:2])>1 else str(int(test_prep_product_code[2][:2]))+"-Week"

                next_product['product_description'] = test_prep_duration + " " + test_prep_location + " SAT/ACT Prep"
                products_info.append(next_product)

            if admin_transaction_details.was_college_apps_purchased:
                next_product = {}
                next_product['number_of_product_units'] = 1
                next_product['per_product_cost'] = 275
                next_product['total_product_cost'] = 275
                next_product['product_description'] = "Consultation/Advisory Services"
                products_info.append(next_product)

                next_product = {}
                next_product['number_of_product_units'] = admin_transaction_details.college_apps_units
                next_product['per_product_cost'] = admin_transaction_details.college_apps_product
                next_product['total_product_cost'] = admin_transaction_details.college_apps_total

                college_apps_product_code = admin_transaction_details.was_college_apps_purchased

                if college_apps_product_code == 'apps-1':
                    next_product['product_description'] = "Per Essay Scholarships/Applications Package"
                elif college_apps_product_code == 'apps-2':
                    next_product['product_description'] = "1-3 Programs Scholarships/Applications Package"
                elif college_apps_product_code == 'apps-3':
                    next_product['product_description'] = "More Than 3 Programs Scholarships/Applications Package"

                products_info.append(next_product)


            if admin_transaction_details.turn_on_installments:
                #client_info['deposit'] = math.ceil(admin_transaction_details.transaction_total/2)
                client_info['turn_on_installments'] = True
                client_info['installments'] = []

                installment_details = InstallmentPlan.query.filter_by(transaction_id=admin_transaction_details.transaction_id).first()


                for k in range(1, int(admin_transaction_details.installment_counter)):
                    next_installment = {}
                    next_installment.update({'date': installment_details.__dict__['date_' + str(k)], 'amount': installment_details.__dict__['amount_' + str(k)]})
                    client_info['installments'].append(next_installment)

        except Exception as e:
            print(e)
            traceback.print_exc()

        return client_info,products_info,showACHOverride

    @classmethod
    def createLead(cls, leadInfo):
        try:
            lead_info_by_mo = Lead(lead_id=leadInfo['lead_id'], lead_salutation=leadInfo['lead_salutation'],lead_name=leadInfo['lead_name'], lead_email=leadInfo['lead_email'], lead_phone_number=leadInfo['lead_phone_number'],appointment_date_and_time=leadInfo['appointment_date_and_time'],
                             what_services_are_they_interested_in=leadInfo['what_services_are_they_interested_in'], details_on_what_service_they_are_interested_in=leadInfo['details_on_what_service_they_are_interested_in'],send_confirmation_to_lead=leadInfo['send_confirmation_to_lead'],
                             miscellaneous_notes=leadInfo['miscellaneous_notes'], how_did_they_hear_about_us=leadInfo['how_did_they_hear_about_us'],details_on_how_they_heard_about_us=leadInfo['details_on_how_they_heard_about_us'],appointment_completed=leadInfo['appointment_completed'])

            db.session.add(lead_info_by_mo)
            cls.executeDBQuery()
            create_lead_info_message = "Lead Info created successfully."

        except Exception as e:
            create_lead_info_message = "Error in submitting lead information."
            raise e
        # finally:
        #     return create_lead_info_message

    @classmethod
    def getLeadInfo(cls, search_query=None,searchStartDate=None,searchEndDate=None):
        try:
            if search_query:
                if search_query.isdigit():
                    lead_info = Lead.query.filter_by(lead_phone_number=search_query).order_by(Lead.appointment_date_and_time.desc()).all()
                elif search_query.startswith("l-"):
                    lead_info = Lead.query.filter_by(lead_id=search_query).order_by(Lead.appointment_date_and_time.desc()).all()
                elif "@" in search_query:
                    lead_info = Lead.query.filter_by(lead_email=search_query).order_by(Lead.appointment_date_and_time.desc()).all()
                else:
                    search = "%{}%".format(search_query)
                    lead_info = Lead.query.filter(Lead.lead_name.ilike(search)).order_by(Lead.appointment_date_and_time.desc()).all()

            elif searchStartDate and searchEndDate:
                lead_info = Lead.query.filter(Lead.appointment_date_and_time <= searchEndDate).filter(Lead.appointment_date_and_time >= searchStartDate).order_by(Lead.appointment_date_and_time.desc()).all()
                #changed way of searching lead_info because previous one was neither inclusive of start/end dates nor intuitive
                #lead_info = Lead.query.filter(Lead.date_created.between(searchStartDate, searchEndDate)).order_by(Lead.date_created.desc()).all()


            search_results = []
            for info in lead_info:
                lead = {}
                lead['lead_id'] = info.lead_id
                lead['lead_salutation'] = info.lead_salutation
                lead['lead_name'] = info.lead_name
                lead['lead_phone_number'] = info.lead_phone_number
                lead['lead_email'] = info.lead_email
                lead['what_services_are_they_interested_in'] = info.what_services_are_they_interested_in
                lead['details_on_what_service_they_are_interested_in'] = info.details_on_what_service_they_are_interested_in
                lead['miscellaneous_notes'] = info.miscellaneous_notes
                lead['how_did_they_hear_about_us'] = info.how_did_they_hear_about_us
                lead['details_on_how_they_heard_about_us'] = info.details_on_how_they_heard_about_us
                lead['appointment_date_and_time'] = cls.clean_up_date_and_time(info.appointment_date_and_time.astimezone(pytz.timezone('US/Central'))) if info.appointment_date_and_time else 'null'
                lead['send_confirmation_to_lead'] = info.send_confirmation_to_lead
                lead['date_created'] = info.date_created.strftime("%m/%d/%Y")
                #lead['completed_appointment'] = 'true' if info.completed_appointment else 'false'
                lead['appointment_completed'] = info.appointment_completed
                lead['grade_level'] = info.grade_level
                lead['recent_test_score'] = '' if info.recent_test_score == -1 else info.recent_test_score
                #'appointment_completed':lead_info_contents.get('appointment_completed','no'),

                search_results.append(lead)
            logger.info(f"Search results are {search_results}")
            return search_results
        except Exception as e:
            raise e

    #TODO repeating method that exists in service class to avoid ciruclar import error. Think about cleaner way of accomplishing
    @classmethod
    def clean_up_date_and_time(cls,date_and_time=None):
        date_and_time = date_and_time.strftime("%c %p")

        res = re.search(r'\s[0-9]{1,2}[:]', date_and_time)
        start = res.start()
        end = res.end()

        hour_as_24 = date_and_time[start:end].split()[0].split(':')[0]
        hour_as_24 = '0' + str(int(hour_as_24) % 12) if int(hour_as_24) % 12 < 10 else str(int(hour_as_24) % 12)
        # logger.info("2. " + hour_as_24)
        date_and_time = date_and_time[:start] + ' ' + hour_as_24 + ':' + date_and_time[start + 4:]
        date_and_time = date_and_time[:16] + " " + date_and_time[24:] + ' CST'
        date_and_time = date_and_time.replace("00:00", "00:00")

        # logger.info("3. " + date_and_time[:15])
        # logger.info("4. " + date_and_time[24:])

        return date_and_time

    @classmethod
    def modifyLeadInfo(cls, lead_id, lead_info):
        try:
            number_of_rows_modified = db.session.query(Lead).filter_by(lead_id=lead_id).update(lead_info)
            cls.executeDBQuery()
            print("number of lead rows modified is: ", number_of_rows_modified) # printing of rows modified to logs to help with auditing
            return number_of_rows_modified
        except Exception as e:
            raise e

    @classmethod
    def getAllTransactionIds(cls):
        transactions = Transaction.query.all()
        transaction_ids = []
        for transaction in transactions:
            transaction_ids.append(transaction.transaction_id)
        return transaction_ids

    @classmethod
    def getAllLeads(cls):
        allLeads = Lead.query.order_by(Lead.date_created.desc()).all()
        return allLeads


    @classmethod
    def executeDBQuery(cls):
        try:
            db.session.commit()
        except Exception as e:
            # if any kind of exception occurs, rollback transaction
            db.session.rollback()
            traceback.print_exc()
            raise e
        finally:
            db.session.close()




