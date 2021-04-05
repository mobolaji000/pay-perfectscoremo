from app.models import Client
from app import db
from datetime import datetime
import math
import uuid
class AppDBUtil():
    def __init__(self):
        pass

    @classmethod
    def createClient(cls,clientData={}):
        invoice_code = str(uuid.uuid4().int>>64)[:4]
        stripe_customer_id = clientData.get('stripe_customer_id','')
        first_name = clientData.get('firstName','')
        last_name = clientData.get('lastName','')
        phone_number = clientData.get('phoneNumber','999')
        email = clientData.get('email','')
        was_diagnostic_purchased = clientData.get('was_diagnostic_purchased', '')
        diag_units = clientData.get('diag_units', 0)
        diag_total = clientData.get('diag_total', 0)
        was_test_prep_purchased = clientData.get('was_test_prep_purchased','')
        tp_product = clientData.get('tp_product','')
        tp_units = clientData.get('tp_units',0)
        tp_total = 0 if clientData.get('tp_total','') == '' else clientData.get('tp_total','')
        was_college_apps_purchased = clientData.get('was_college_apps_purchased', '')
        college_apps_product = clientData.get('college_apps_product','')
        college_apps_units = clientData.get('college_apps_units',0)
        college_apps_total = 0 if clientData.get('college_apps_total','') == '' else clientData.get('college_apps_total','')
        print("client data is  ",clientData)
        turn_on_installments = False if clientData.get('turn_on_installments','') == '' else True
        installment_date_1 = datetime(1,1,1) if clientData.get('installment_date_1','') == '' else datetime.strptime(clientData['installment_date_1'],'%Y-%m-%d')
        installment_date_2 = datetime(1,1,1) if clientData.get('installment_date_2','') == '' else datetime.strptime(clientData['installment_date_2'],'%Y-%m-%d')
        installment_date_3 = datetime(1,1,1) if clientData.get('installment_date_3','') == '' else datetime.strptime(clientData['installment_date_3'],'%Y-%m-%d')
        adjust_total = 0 if clientData.get('adjust_total','') == '' else clientData.get('adjust_total','')
        adjustment_explanation = clientData.get('adjustment_explanation','')
        invoice_total = 0 if clientData.get('invoice_total','') == '' else clientData.get('invoice_total','')

        c = Client(invoice_code=invoice_code, stripe_customer_id=stripe_customer_id, first_name=first_name, last_name=last_name,
                   phone_number=phone_number, email=email, was_diagnostic_purchased=was_diagnostic_purchased, diag_units=diag_units,
                   diag_total=diag_total, was_test_prep_purchased=was_test_prep_purchased, tp_product=tp_product, tp_units=tp_units,
                   tp_total=tp_total, was_college_apps_purchased=was_college_apps_purchased, college_apps_product=college_apps_product,
                   college_apps_units=college_apps_units, college_apps_total=college_apps_total, turn_on_installments=turn_on_installments,
                   installment_date_1=installment_date_1, installment_date_2=installment_date_2, installment_date_3=installment_date_3,
                   adjust_total=adjust_total, adjustment_explanation=adjustment_explanation, invoice_total=invoice_total)

        db.session.add(c)
        db.session.commit()
        return invoice_code


    @classmethod
    def getInvoiceDetails(cls,invoice_code):
        admin_invoice_details = Client.query.filter_by(invoice_code=invoice_code).order_by(Client.date_created.desc()).first()
        #print (admin_invoice_details)
        return cls.computeClientInvoiceDetails(admin_invoice_details)

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
                    print(installment_date)
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




