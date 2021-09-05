from app.models import Invoice
from app import db
from datetime import datetime
import math
import uuid
from dateutil.parser import parse


class AppDBUtil():
    def __init__(self):
        pass

    @classmethod
    def createOrModifyClient(cls, clientData={}, invoice_code=None, action=''):
        invoice_code = invoice_code if invoice_code else str(uuid.uuid4().int>>64)[:6]
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
        #comeback to make sure no bug here from change
        college_apps_units = 0 if clientData.get('college_apps_units','') == '' else clientData.get('college_apps_units','')
        college_apps_total = 0 if clientData.get('college_apps_total','') == '' else clientData.get('college_apps_total','')
        #print("client data is  ",clientData)
        turn_on_installments = False if clientData.get('turn_on_installments','') == '' else True
        installment_date_1 = datetime(1,1,1) if clientData.get('installment_date_1','') == '' else datetime.strptime(clientData['installment_date_1'],'%Y-%m-%d')
        installment_date_2 = datetime(1,1,1) if clientData.get('installment_date_2','') == '' else datetime.strptime(clientData['installment_date_2'],'%Y-%m-%d')
        installment_date_3 = datetime(1,1,1) if clientData.get('installment_date_3','') == '' else datetime.strptime(clientData['installment_date_3'],'%Y-%m-%d')
        adjust_total = 0 if clientData.get('adjust_total','') == '' else clientData.get('adjust_total','')
        adjustment_explanation = clientData.get('adjustment_explanation','')
        invoice_total = 0 if clientData.get('invoice_total','') == '' else clientData.get('invoice_total','')

        number_of_rows_modified = None
        if action=='create':

            invoice = Invoice(invoice_code=invoice_code, stripe_customer_id=stripe_customer_id, first_name=first_name, last_name=last_name,
                        phone_number=phone_number, email=email, was_diagnostic_purchased=was_diagnostic_purchased, diag_units=diag_units,
                        diag_total=diag_total, was_test_prep_purchased=was_test_prep_purchased, tp_product=tp_product, tp_units=tp_units,
                        tp_total=tp_total, was_college_apps_purchased=was_college_apps_purchased, college_apps_product=college_apps_product,
                        college_apps_units=college_apps_units, college_apps_total=college_apps_total, turn_on_installments=turn_on_installments,
                        installment_date_1=installment_date_1, installment_date_2=installment_date_2, installment_date_3=installment_date_3,
                        adjust_total=adjust_total, adjustment_explanation=adjustment_explanation, invoice_total=invoice_total)

            db.session.add(invoice)

        elif action=='modify':

            #invoice = Invoice.query.filter_by(invoice_code=invoice_code).first()

            #what happens in the unlikely event that 2 rows have the same invoice code?
            number_of_rows_modified = db.session.query(Invoice).filter_by(invoice_code=invoice_code).update\
                ({"stripe_customer_id": stripe_customer_id,"first_name": first_name,"last_name": last_name,"phone_number": phone_number,
                        "email": email,"was_diagnostic_purchased": was_diagnostic_purchased,"diag_units": diag_units,"diag_total": diag_total,
                        "was_test_prep_purchased": was_test_prep_purchased,"tp_product": tp_product,"tp_units": tp_units,"tp_total": tp_total,
                        "was_college_apps_purchased": was_college_apps_purchased,"college_apps_product": college_apps_product,"college_apps_units": college_apps_units,
                        "college_apps_total": college_apps_total,"turn_on_installments": turn_on_installments,"installment_date_1": installment_date_1,
                        "installment_date_2": installment_date_2,"installment_date_3": installment_date_3,"adjust_total": adjust_total,
                        "adjustment_explanation": adjustment_explanation,"invoice_total": invoice_total})

            print("number of rows modified is: ",number_of_rows_modified) #printing of rows modified to logs to help with auditing



        try:
            db.session.commit()
        except:
            # if any kind of exception occurs, rollback transaction
            session.rollback()
            raise
        finally:
            session.close()

        return invoice_code,number_of_rows_modified

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
        except ValueError:
            return False

    @classmethod
    def deleteInvoice(cls, codeOfInvoiceToDelete):
        invoice = Invoice.query.filter_by(invoice_code=codeOfInvoiceToDelete).first()
        db.session.delete(invoice)
        try:
            db.session.commit()
        except:
            # if any kind of exception occurs, rollback transaction
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def modifyInvoiceDetails(cls, data_to_modify):
        return cls.createOrModifyClient(clientData=data_to_modify, invoice_code=data_to_modify['invoice_code'],action='modify')


    @classmethod
    def updateAmountPaidAgainstInvoice(cls,invoice_code,amount_paid):
        invoice = Invoice.query.filter_by(invoice_code=invoice_code).first()
        invoice.amount_from_invoice_paid_so_far = invoice.amount_from_invoice_paid_so_far + amount_paid
        try:
            db.session.commit()
        except:
            # if any kind of exception occurs, rollback transaction
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def findClientsToReceiveReminders(cls):
        invoice_details = Invoice.query.filter_by(payment_started=False).all()
        search_results = []
        for invoice in invoice_details:
            client = {}
            client['first_name'] = invoice.first_name
            client['last_name'] = invoice.last_name
            client['phone_number'] = invoice.phone_number
            client['email'] = invoice.email
            client['invoice_code'] = invoice.invoice_code
            client['payment_started'] = str(invoice.payment_started)
            search_results.append(client)

        return search_results

    @classmethod
    def searchInvoices(cls, search_query):
        if search_query.isdigit():
            if len(search_query) == 6:
                invoice_details = Invoice.query.filter_by(invoice_code=search_query).order_by(Invoice.date_created.desc()).all()
            else:
                invoice_details = Invoice.query.filter_by(phone_number=search_query).order_by(Invoice.date_created.desc()).all()
        elif "@" in search_query:
            invoice_details = Invoice.query.filter_by(email=search_query).order_by(Invoice.date_created.desc()).all()
        elif cls.is_date(search_query):
            #do something to get the date in the right format first
            invoice_details = Invoice.query.filter_by(date_created=search_query).order_by(Invoice.date_created.desc()).all()
        else:
            invoice_details = Invoice.query.filter((Invoice.first_name == search_query.capitalize()) | (Invoice.last_name == search_query.capitalize())
                                                   | (Invoice.first_name == search_query.lower()) | (Invoice.last_name == search_query.lower())
                                                   | (Invoice.first_name == search_query) | (Invoice.last_name == search_query))\
                .order_by(Invoice.date_created.desc()).all()

        search_results = []
        for invoice in invoice_details:
            client = {}
            client['first_name'] = invoice.first_name
            client['last_name'] = invoice.last_name
            client['phone_number'] = invoice.phone_number
            client['email'] = invoice.email
            client['stripe_customer_id'] = invoice.stripe_customer_id
            client['adjust_total'] = invoice.adjust_total
            client['adjustment_explanation'] = invoice.adjustment_explanation
            client['invoice_total'] = invoice.invoice_total
            client['date_created'] = invoice.date_created.strftime("%m/%d/%Y")
            client['invoice_code'] = invoice.invoice_code
            client['was_diagnostic_purchased'] = invoice.was_diagnostic_purchased
            client['diag_units'] = invoice.diag_units
            client['diag_total'] = invoice.diag_total
            client['was_test_prep_purchased'] = invoice.was_test_prep_purchased
            client['tp_units'] = invoice.tp_units
            client['tp_total'] = invoice.tp_total
            client['was_college_apps_purchased'] = invoice.was_college_apps_purchased
            client['college_apps_units'] = invoice.college_apps_units
            client['college_apps_total'] = invoice.college_apps_total
            client['turn_on_installments'] = str(invoice.turn_on_installments)
            client['installment_date_1'] = invoice.installment_date_1.strftime("%m/%d/%Y")
            client['installment_date_2'] = invoice.installment_date_2.strftime("%m/%d/%Y")
            client['installment_date_3'] = invoice.installment_date_3.strftime("%m/%d/%Y")
            client['adjust_total'] = invoice.adjust_total
            client['adjustment_explanation'] = invoice.adjustment_explanation
            client['invoice_total'] = invoice.invoice_total
            client['payment_started'] = str(invoice.payment_started)

            search_results.append(client)

        return search_results

    @classmethod
    def getInvoiceDetails(cls,invoice_code):
        admin_invoice_details = Invoice.query.filter_by(invoice_code=invoice_code).order_by(Invoice.date_created.desc()).first()
        return cls.computeClientInvoiceDetails(admin_invoice_details)

    @classmethod
    def updateInvoicePaymentStarted(cls, invoice_code):
        invoice = Invoice.query.filter_by(invoice_code=invoice_code).order_by(Invoice.date_created.desc()).first()
        invoice.payment_started = True
        try:
            db.session.commit()
        except:
            # if any kind of exception occurs, rollback transaction
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def computeClientInvoiceDetails(cls,admin_invoice_details):
        client_info = {}
        products_info = []
        try:
            client_info['first_name'] = admin_invoice_details.first_name
            client_info['last_name'] = admin_invoice_details.last_name
            client_info['phone_number'] = admin_invoice_details.phone_number
            client_info['email'] = admin_invoice_details.email
            client_info['stripe_customer_id'] = admin_invoice_details.stripe_customer_id
            client_info['turn_on_installments'] = admin_invoice_details.turn_on_installments
            client_info['adjust_total'] = admin_invoice_details.adjust_total
            client_info['adjustment_explanation'] = admin_invoice_details.adjustment_explanation
            client_info['invoice_total'] = admin_invoice_details.invoice_total
            client_info['invoice_code'] = admin_invoice_details.invoice_code
            client_info['payment_started'] = admin_invoice_details.payment_started

            if admin_invoice_details.was_diagnostic_purchased:
                next_product = {}
                next_product['number_of_product_units'] = admin_invoice_details.diag_units
                next_product['per_product_cost'] = 50
                next_product['total_product_cost'] = admin_invoice_details.diag_total
                next_product['product_description'] = "Diagnostic/Consultation"
                products_info.append(next_product)

            if admin_invoice_details.was_test_prep_purchased:
                next_product = {}
                next_product['number_of_product_units'] = admin_invoice_details.tp_units
                next_product['per_product_cost'] = admin_invoice_details.tp_product
                next_product['total_product_cost'] = admin_invoice_details.tp_total

                test_prep_product_code = admin_invoice_details.was_test_prep_purchased.split('-')
                if len(test_prep_product_code) == 4:
                    test_prep_location = test_prep_product_code[1].capitalize()+" "+test_prep_product_code[2].capitalize()
                    test_prep_duration = str(int(test_prep_product_code[3][:2]))+"-Weeks" if int(test_prep_product_code[3][:2])>1 else str(int(test_prep_product_code[3][:2]))+"-Week"
                else:
                    test_prep_location = test_prep_product_code[1].capitalize()
                    test_prep_duration = str(int(test_prep_product_code[2][:2]))+"-Weeks" if int(test_prep_product_code[2][:2])>1 else str(int(test_prep_product_code[2][:2]))+"-Week"

                next_product['product_description'] = test_prep_duration + " " + test_prep_location + " SAT/ACT Prep"
                products_info.append(next_product)

            if admin_invoice_details.was_college_apps_purchased:
                next_product = {}
                next_product['number_of_product_units'] = 1
                next_product['per_product_cost'] = 275
                next_product['total_product_cost'] = 275
                next_product['product_description'] = "Consultation/Advisory Services"
                products_info.append(next_product)

                next_product = {}
                next_product['number_of_product_units'] = admin_invoice_details.college_apps_units
                next_product['per_product_cost'] = admin_invoice_details.college_apps_product
                next_product['total_product_cost'] = admin_invoice_details.college_apps_total

                college_apps_product_code = admin_invoice_details.was_college_apps_purchased

                if college_apps_product_code == 'apps-1':
                    next_product['product_description'] = "Per Essay Scholarships/Applications Package"
                elif college_apps_product_code == 'apps-2':
                    next_product['product_description'] = "1-3 Programs Scholarships/Applications Package"
                elif college_apps_product_code == 'apps-3':
                    next_product['product_description'] = "More Than 3 Programs Scholarships/Applications Package"

                products_info.append(next_product)


            if admin_invoice_details.turn_on_installments:
                client_info['deposit'] = math.ceil(admin_invoice_details.invoice_total/2)
                client_info['turn_on_installments'] = True
                client_info['installments'] = []

                index = 0
                for installment_date in [admin_invoice_details.installment_date_1,admin_invoice_details.installment_date_2,admin_invoice_details.installment_date_3]:
                    next_installment = {}
                    if (installment_date-datetime(1,1,1).date()).days != 0:
                        next_installment['installment_date'] = installment_date
                        if index == 0:
                            next_installment['installment_amount'] = math.ceil(admin_invoice_details.invoice_total/2)
                        if index == 1:
                            client_info['installments'][0]['installment_amount'] = math.ceil(admin_invoice_details.invoice_total/4)
                            next_installment['installment_amount'] = math.ceil(admin_invoice_details.invoice_total/4)
                        if index == 2:
                            client_info['installments'][0]['installment_amount'] = math.ceil(admin_invoice_details.invoice_total / 6)
                            client_info['installments'][1]['installment_amount'] = math.ceil(admin_invoice_details.invoice_total / 6)
                            next_installment['installment_amount'] = math.ceil(admin_invoice_details.invoice_total / 6)

                        index=index+1
                        client_info['installments'].append(next_installment)

        except Exception as e:
            print(e)

        return client_info,products_info




