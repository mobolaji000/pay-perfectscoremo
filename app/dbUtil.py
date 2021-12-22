from app.models import Transaction,InstallmentPlan,InvoiceToBePaid,Prospect,Student,LeadInfo
from app import db
from app.config import stripe
from datetime import datetime
import math
import uuid
from dateutil.parser import parse
import logging
import traceback
from sqlalchemy.dialects.postgresql import insert
#from app.service import SendMessagesToClients

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


class AppDBUtil():
    def __init__(self):
        pass

    @classmethod
    def createProspect(cls, prospectData={}):
        prospect_id = "p-"+str(uuid.uuid4().int >> 64)[:6]
        prospect_first_name = prospectData.get('first_name', '')
        prospect_last_name = prospectData.get('last_name', '')
        prospect_phone_number = prospectData.get('phone_number', '999')
        prospect_email = prospectData.get('email', '')
        how_did_you_hear_about_us = prospectData.get('how_did_you_hear_about_us', '')

        existing_prospect = db.session.query(Prospect).filter_by(prospect_email=prospect_email,prospect_phone_number=prospect_phone_number).first()
        if existing_prospect:
            prospect = existing_prospect
        else:
            prospect = Prospect(prospect_id=prospect_id,prospect_first_name=prospect_first_name, prospect_last_name=prospect_last_name,prospect_phone_number=prospect_phone_number, prospect_email=prospect_email, how_did_you_hear_about_us=how_did_you_hear_about_us)
            db.session.add(prospect)
            cls.executeDBQuery()
        return prospect

    @classmethod
    def createOrModifyClientTransaction(cls, clientData={}, transaction_id=None, action=''):
        transaction_id = transaction_id if transaction_id else "t-"+str(uuid.uuid4().int>>64)[:6]
        prospect_id = clientData.get('prospect_id','')
        stripe_customer_id = clientData.get('stripe_customer_id','')
        first_name = clientData.get('first_name','')
        last_name = clientData.get('last_name','')
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
        ask_for_student_info = clientData.get('ask_for_student_info','')
        # client-side counter is always one more; get the actual number here



        number_of_rows_modified = None
        if action=='create':

            transaction = Transaction(transaction_id=transaction_id, prospect_id=prospect_id, stripe_customer_id=stripe_customer_id, first_name=first_name, last_name=last_name,
                                  phone_number=phone_number, email=email, was_diagnostic_purchased=was_diagnostic_purchased, diag_units=diag_units,
                                  diag_total=diag_total, was_test_prep_purchased=was_test_prep_purchased, tp_product=tp_product, tp_units=tp_units,
                                  tp_total=tp_total, was_college_apps_purchased=was_college_apps_purchased, college_apps_product=college_apps_product,
                                  college_apps_units=college_apps_units, college_apps_total=college_apps_total,
                                  adjust_total=adjust_total, adjustment_explanation=adjustment_explanation, transaction_total=transaction_total, installment_counter=installment_counter)


            db.session.add(transaction)

        elif action=='modify':
            #what happens in the unlikely event that 2 rows have the same transaction code?
            number_of_rows_modified = db.session.query(Transaction).filter_by(transaction_id=transaction_id).update\
                ({"stripe_customer_id": stripe_customer_id,"first_name": first_name,"last_name": last_name,"phone_number": phone_number,
                        "email": email,"was_diagnostic_purchased": was_diagnostic_purchased,"diag_units": diag_units,"diag_total": diag_total,
                        "was_test_prep_purchased": was_test_prep_purchased,"tp_product": tp_product,"tp_units": tp_units,"tp_total": tp_total,
                        "was_college_apps_purchased": was_college_apps_purchased,"college_apps_product": college_apps_product,"college_apps_units": college_apps_units,
                        "college_apps_total": college_apps_total,"adjust_total": adjust_total,
                        "adjustment_explanation": adjustment_explanation,"transaction_total": transaction_total, "installment_counter":installment_counter})

            print("number of transaction rows modified is: ",number_of_rows_modified) #printing of rows modified to logs to help with auditing



        cls.executeDBQuery()

        cls.createOrModifyInstallmentPlan(clientData=clientData, transaction_id=transaction_id, action=action)

        return transaction_id,number_of_rows_modified

    @classmethod
    def createOrModifyInvoice(cls, first_name=None, last_name=None, phone_number=None, email=None, transaction_id=None, stripe_customer_id=None, stripe_invoice_id=None, payment_date=None, payment_amount=None):
        #
        invoice = InvoiceToBePaid(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email,
                                  transaction_id=transaction_id, stripe_customer_id=stripe_customer_id,
                                  payment_date=payment_date, payment_amount=payment_amount,
                                  stripe_invoice_id=stripe_invoice_id)

        db.session.add(invoice)
        print("invoice to be paid created is: ", invoice)
        cls.executeDBQuery()


    @classmethod
    def createOrModifyInstallmentPlan(cls, clientData={}, transaction_id=None, action=''):

        if int(clientData['installment_counter']) > 1:
            installments = {}
            print("number of installments is " + str(int(clientData['installment_counter'])-1))
            for k in range(1, int(clientData['installment_counter'])):
                print("current installment being updated is " + str(k))
                installments.update({'date_' + str(k): clientData['date_' + str(k)], 'amount_' + str(k): clientData['amount_' + str(k)]})

            installment_plan = InstallmentPlan(transaction_id=transaction_id, stripe_customer_id=clientData['stripe_customer_id'], first_name=clientData['first_name'], last_name=clientData['last_name'], phone_number=clientData['phone_number'], email=clientData['email'])
            db.session.add(installment_plan)
            print("installment plan created is: ", installment_plan)
            cls.executeDBQuery()

            installment_plan = db.session.query(InstallmentPlan).filter_by(transaction_id=transaction_id)
            number_of_rows_modified = installment_plan.update(installments)
            print("number of installment rows added or modified is: ", number_of_rows_modified)

            cls.executeDBQuery()
        else:
            print("No installment created or modified")

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

        # except Exception as e:
        #     return False
        except ValueError as v:
            #logger.error(v)
            #traceback.print_exc()
            return False

    @classmethod
    def deleteInvoiceToBePaid(cls, invoiceTransactionCode,stripeInvoiceId):
        invoice_to_be_paid = InvoiceToBePaid.query.filter_by(transaction_id=invoiceTransactionCode).first()
        db.session.delete(invoice_to_be_paid)
        cls.executeDBQuery()
        stripe.Invoice.delete(stripeInvoiceId,)

    @classmethod
    def deleteTransaction(cls, codeOfTransactionToDelete):
        transaction = Transaction.query.filter_by(transaction_id=codeOfTransactionToDelete).first()
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
    def updateInvoiceAsPaid(cls, stripe_invoice_id=None):
        invoice = InvoiceToBePaid.query.filter_by(stripe_invoice_id=stripe_invoice_id).first()
        invoice.payment_made = True
        cls.executeDBQuery()

    @classmethod
    def findInvoicesToPay(cls):
        try:
            invoices_to_pay = db.session.query(InvoiceToBePaid).filter((InvoiceToBePaid.payment_made == False) & (InvoiceToBePaid.payment_date <= datetime.today())).all()
            print("invoices_to_pay are: ",invoices_to_pay)
            search_results = []
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
    def findClientsToReceiveReminders(cls):
        try:
            transaction_details = Transaction.query.filter_by(payment_started=False).all()
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
            if len(search_query) == 6:
                transaction_details = Transaction.query.filter_by(transaction_id=search_query).order_by(Transaction.date_created.desc()).all()
            else:
                transaction_details = Transaction.query.filter_by(phone_number=search_query).order_by(Transaction.date_created.desc()).all()
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
            client['first_name'] = transaction.first_name
            client['last_name'] = transaction.last_name
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
            client['adjust_total'] = transaction.adjust_total
            client['installment_counter'] = transaction.installment_counter
            client['adjustment_explanation'] = transaction.adjustment_explanation
            client['transaction_total'] = transaction.transaction_total
            client['payment_started'] = str(transaction.payment_started)

            installment_details = InstallmentPlan.query.filter_by(transaction_id=transaction.transaction_id).first()

            if installment_details:
                installments = {}
                for k in range(1, int(transaction.installment_counter)):
                    installments.update({'date_' + str(k): installment_details.__dict__['date_' + str(k)].strftime("%m/%d/%Y"), 'amount_' + str(k): installment_details.__dict__['amount_' + str(k)]})

                client['installment_details'] = installments

            search_results.append(client)
        print("search results are ",search_results)
        return search_results

    @classmethod
    def getTransactionDetails(cls,transaction_id):
        showACHOverride = False
        if 'ach' in transaction_id.lower():
            showACHOverride = True
            transaction_id = transaction_id.lower().split('ach')[0]

        print("showACHOverride is: ",showACHOverride)

        admin_transaction_details = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        admin_transaction_details.turn_on_installments = True if admin_transaction_details.installment_counter > 1 else False
        return cls.computeClientTransactionDetails(admin_transaction_details,showACHOverride)

    @classmethod
    def updateTransactionPaymentStarted(cls, transaction_id):
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).order_by(Transaction.date_created.desc()).first()
        transaction.payment_started = True
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

            # student = Student( student_id=student_id,prospect_id=prospect_id,student_first_name=student_first_name,student_last_name=student_last_name,student_phone_number=student_phone_number,student_email=student_email,
            #                    parent_1_salutation=parent_1_salutation,parent_1_first_name=parent_1_first_name,parent_1_last_name=parent_1_last_name,parent_1_phone_number=parent_1_phone_number,parent_1_email=parent_1_email,
            #                    parent_2_salutation=parent_2_salutation,parent_2_first_name=parent_2_first_name,parent_2_last_name=parent_2_last_name,parent_2_phone_number=parent_2_phone_number,parent_2_email=parent_2_email)
            #
            # db.session.add(student)

            statement = insert(Student).values(student_id=student_id,prospect_id=prospect_id,student_first_name=student_first_name,student_last_name=student_last_name,student_phone_number=student_phone_number,student_email=student_email,
                               parent_1_salutation=parent_1_salutation,parent_1_first_name=parent_1_first_name,parent_1_last_name=parent_1_last_name,parent_1_phone_number=parent_1_phone_number,parent_1_email=parent_1_email,
                               parent_2_salutation=parent_2_salutation,parent_2_first_name=parent_2_first_name,parent_2_last_name=parent_2_last_name,parent_2_phone_number=parent_2_phone_number,parent_2_email=parent_2_email)

            updated_content = dict(student_id=student_id,prospect_id=prospect_id,student_first_name=student_first_name,student_last_name=student_last_name,student_phone_number=student_phone_number,
                               parent_1_salutation=parent_1_salutation,parent_1_first_name=parent_1_first_name,parent_1_last_name=parent_1_last_name,parent_1_phone_number=parent_1_phone_number,parent_1_email=parent_1_email,
                               parent_2_salutation=parent_2_salutation,parent_2_first_name=parent_2_first_name,parent_2_last_name=parent_2_last_name,parent_2_phone_number=parent_2_phone_number,parent_2_email=parent_2_email)

            statement = statement.on_conflict_do_update(
                index_elements=['student_email'],
                set_=updated_content
            )

            cls.executeDBQuery()
            create_student_data_message = "Student information submitted successfully and group messages (email and text) for regular updates created."

        except Exception as e:
            create_student_data_message = "Error in submitting student information or in creating group messages. Contact Mo. "
            print(e)
            print(traceback.print_exc())
        finally:
            return create_student_data_message


    @classmethod
    def computeClientTransactionDetails(cls,admin_transaction_details,showACHOverride):
        client_info = {}
        products_info = []
        try:
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
            client_info['showACHOverride'] = str(showACHOverride)
            print("client_info_installment_counter is "+str(admin_transaction_details.installment_counter))

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
            lead_info = LeadInfo(lead_id=leadInfo['lead_id'],lead_name=leadInfo['lead_name'],lead_email=leadInfo['lead_email'],lead_phone_number=leadInfo['lead_phone_number'],
                                 what_service_are_they_interested_in=leadInfo['what_service_are_they_interested_in'],what_next=leadInfo['what_next'],
                                 meeting_notes_to_keep_in_mind=leadInfo['meeting_notes_to_keep_in_mind'],how_did_they_hear_about_us=leadInfo['how_did_they_hear_about_us'])

            db.session.add(lead_info)
            cls.executeDBQuery()
            create_lead_info_message = "Lead Info created successfully."

        except Exception as e:
            create_lead_info_message = "Error in submitting lead information."
            print(e)
            print(traceback.print_exc())
        finally:
            return create_lead_info_message

    @classmethod
    def getLeadInfo(cls, search_query,searchStartDate,searchEndDate):
        if search_query.isdigit():
            lead_info = LeadInfo.query.filter_by(lead_phone_number=search_query).order_by(LeadInfo.date_created.desc()).all()
        elif "@" in search_query:
            lead_info = LeadInfo.query.filter_by(lead_email=search_query).order_by(LeadInfo.date_created.desc()).all()
        elif searchStartDate and searchEndDate:
            lead_info = LeadInfo.query.filter_by((LeadInfo.day.between(searchStartDate, searchEndDate))).order_by(LeadInfo.date_created.desc()).all()
        else:
            search = "%{}%".format(search_query)
            lead_info = LeadInfo.query.filter(LeadInfo.lead_name.ilike(search)).order_by(LeadInfo.date_created.desc()).all()

        search_results = []
        for info in lead_info:
            lead = {}
            lead['lead_id'] = info.lead_id
            lead['lead_name'] = info.lead_name
            lead['lead_phone_number'] = info.lead_phone_number
            lead['lead_email'] = info.lead_email
            lead['what_service_are_they_interested_in'] = info.what_service_are_they_interested_in
            lead['what_next'] = info.what_next
            lead['meeting_notes_to_keep_in_mind'] = info.meeting_notes_to_keep_in_mind
            lead['how_did_they_hear_about_us'] = info.how_did_they_hear_about_us
            lead['how_did_they_hear_about_us_details'] = info.how_did_they_hear_about_us_details
            lead['date_created'] = info.date_created.strftime("%m/%d/%Y")

            search_results.append(lead)
        print("search results are ", search_results)
        return search_results

    @classmethod
    def modifyLeadInfo(cls, lead_id, lead_info):

        number_of_rows_modified = db.session.query(LeadInfo).filter_by(lead_id=lead_id).update(lead_info)
        cls.executeDBQuery()
        print("number of lead rows modified is: ", number_of_rows_modified) # printing of rows modified to logs to help with auditing
        return number_of_rows_modified

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




