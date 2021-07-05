from app.config import stripe
from app.aws import AWSInstance
from app.config import Config
from flask_login import UserMixin
from app.models import Invoice
import time
import datetime
import ast
import math


import sendgrid
from twilio.rest import Client as TwilioClient
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class ValidateLogin():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.awsInstance = AWSInstance()

    def validateUserName(self):
        return True if self.username == self.awsInstance.get_secret("vensti_admin", "username") else False

    def validatePassword(self):
        return True if self.password == self.awsInstance.get_secret("vensti_admin", "password") else False


class User(UserMixin):
    def __init__(self, password):
        self.password = password
        self.awsInstance = AWSInstance()

    def is_authenticated(self):
        return True
        # return True if self.password == self.awsInstance.get_secret("vensti_admin","password") else False

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.awsInstance.get_secret("vensti_admin", "password"))


class StripeInstance():
    def __init__(self, ):
        pass

    def createCustomer(self, clientSetupData):
        #reverse to chcek for existing customer after testing
        existing_customer = Invoice.query.filter_by(email=clientSetupData['email']).order_by(Invoice.date_created.desc()).first() or Invoice.query.filter_by(phone_number=clientSetupData['phone_number']).order_by(Invoice.date_created.desc()).first()
        print("existing customer is ",existing_customer)
        customer = stripe.Customer.retrieve(existing_customer.stripe_customer_id) if existing_customer else stripe.Customer.create(email=clientSetupData['email'],name=clientSetupData['first_name'] + " " + clientSetupData['last_name'],phone=clientSetupData['phone_number'])
        print("new customer is ",customer)
        return customer

    def setUpIntent(self, stripe_info):
        intent = stripe.SetupIntent.create(customer=stripe_info['stripe_customer_id'])
        return intent.client_secret

    def markCustomerAsChargedOutsideofStripe(self, stripe_info):
        invoice_total = int(stripe_info['invoice_total'])

        stripe.InvoiceItem.create(
            customer=stripe_info['stripe_customer_id'],
            quantity=invoice_total,
            price=os.environ.get('price'),
        )
        invoice = stripe.Invoice.create(
            customer=stripe_info['stripe_customer_id'],
            metadata={'invoice_code': stripe_info['invoice_code']},
        )
        stripe.Invoice.pay(invoice.id,paid_out_of_band=True)

        return {'status': 'success'}

    def chargeCustomerViaACH(self, stripe_info, bank_account_token):
        invoice_total = int(stripe_info['invoice_total'])

        # source = stripe.Source.create(
        #     type='ach_debit',
        #     token=bank_account_token,
        # )

        # bank_account_token_id = stripe.Token.retrieve(bank_account_token,)['bank_account']['id']


        stripe.Customer.modify(
            stripe_info['stripe_customer_id'],
            source=bank_account_token,
            #default_source=bank_account_token,
            #invoice_settings={'default_payment_method': None},
        )

        customer_default_source = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])['default_source']

        stripe.InvoiceItem.create(
            customer=stripe_info['stripe_customer_id'],
            quantity=invoice_total,
            price=os.environ.get('price'),
        )

        #
        invoice = stripe.Invoice.create(
            customer=stripe_info['stripe_customer_id'],
            #payment_settings={"payment_method_types": ['ach_debit',]},
            default_source=customer_default_source,
            metadata={'invoice_code': stripe_info['invoice_code']},
        )
        stripe.Invoice.pay(invoice.id)

        return {'status': 'success'}

    def chargeCustomerViaCard(self, stripe_info, chosen_mode_of_payment, payment_id):
        #stripe_info = ast.literal_eval(stripe_info)

        stripe.PaymentMethod.attach(
            payment_id,
            customer=stripe_info['stripe_customer_id'],
        )

        stripe.Customer.modify(
            stripe_info['stripe_customer_id'],
            #default_source=None,
            invoice_settings={'default_payment_method':payment_id},
        )

        # stripe.PaymentMethod.modify(
        #     payment_id,
        #    type="card",
        # )
        #

        if chosen_mode_of_payment == 'installment-payment-credit-card':

            payment_method = stripe.PaymentMethod.retrieve(
                payment_id,
            )
            print("payment_method is ",payment_method['card']['funding'])

            # if payment_method['card']['funding'] != 'credit':
            #     stripe.PaymentMethod.detach(
            #         payment_id,
            #     )
            #     return {'status': 'failure'}

            deposit = int(stripe_info.get('deposit', 0) * 103)
            today = int(time.mktime((datetime.datetime.today() + datetime.timedelta(seconds=1)).timetuple()))
            installment_1 = [int(stripe_info.get('installment_amount_1', 0) * 103),stripe_info.get('installment_date_1', 0)]
            installment_2 = [int(stripe_info.get('installment_amount_2', 0) * 103),stripe_info.get('installment_date_2', 0)]
            installment_3 = [int(stripe_info.get('installment_amount_3', 0) * 103),stripe_info.get('installment_date_3', 0)]
            phase1 = phase2 = phase3 = last_phase = None

            for index, installment in enumerate([[deposit, today], installment_1, installment_2, installment_3]):
                if (installment[0] != 0 and installment[1] != 0):
                    # print(index)
                    # print(installment)
                    one_day = 86400
                    if index == 1:
                        end_of_phase = installment_1[1]
                        phase1 = self.getPhases(deposit, end_of_phase, interval='day',interval_count=int(math.ceil((installment_1[1] - today) / one_day)))
                        end_of_phase = installment_1[1] + one_day
                        last_phase = self.getPhases(installment_1[0], end_of_phase, interval='day', interval_count=1)
                        # print(colored(phase1, 'red'), colored(last_phase, 'blue'))
                    elif index == 2:
                        end_of_phase = installment_1[1]
                        phase1 = self.getPhases(deposit, end_of_phase, interval='day',interval_count=int(math.ceil((installment_1[1] - today) / one_day)))
                        end_of_phase = installment_2[1]
                        phase2 = self.getPhases(installment_1[0], end_of_phase, interval='day', interval_count=int(math.ceil((installment_2[1] - installment_1[1]) / one_day)))
                        end_of_phase = installment_2[1] + one_day
                        last_phase = self.getPhases(installment_2[0], end_of_phase, interval='day', interval_count=1)
                    elif index == 3:
                        end_of_phase = installment_1[1]
                        phase1 = self.getPhases(deposit, end_of_phase, interval='day',interval_count=int(math.ceil((installment_1[1] - today) / one_day)))
                        end_of_phase = installment_2[1]
                        phase2 = self.getPhases(installment_1[0], end_of_phase, interval='day', interval_count=int(math.ceil((installment_2[1] - installment_1[1]) / one_day)))
                        end_of_phase = installment_3[1]
                        phase3 = self.getPhases(installment_2[0], end_of_phase, interval='day', interval_count=int(math.ceil((installment_3[1] - installment_2[1]) / one_day)))
                        end_of_phase = installment_3[1] + one_day
                        last_phase = self.getPhases(installment_3[0], end_of_phase, interval='day', interval_count=1)

            phases = [phase1, phase2, phase3, last_phase]
            stripe.SubscriptionSchedule.create(
                customer=stripe_info['stripe_customer_id'],
                start_date='now',
                end_behavior='cancel',
                phases=[x for x in phases if x is not None],
                default_settings={"default_payment_method": payment_id,},
                metadata={'invoice_code': stripe_info['invoice_code']},
            )
        else:
            invoice_total = int(math.ceil(stripe_info['invoice_total']*1.03))
            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=invoice_total,
                price=os.environ.get('price'),
            )
            invoice = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                default_payment_method=payment_id,
                #payment_settings={"payment_method_types": ['card',]},
                metadata={'invoice_code': stripe_info['invoice_code']},
            )
            stripe.Invoice.pay(invoice.id)

            # invoice = stripe.Invoice.finalize_invoice(invoice.id)

        return {'status': 'success'}


    def getPhases(self, installment_amount, installment_end_date, interval='day', interval_count=1):
        phase = {
            'items': [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product': os.environ.get('product'),
                        'recurring': {
                            'interval': interval,
                            'interval_count': interval_count
                        },
                        'unit_amount': installment_amount
                    },
                },
            ],
            'end_date': installment_end_date,
            'proration_behavior': 'none',
        }
        return phase


class PlaidInstance():
    def __init__(self):
        pass

    @classmethod
    def get_link_token(cls, customer_id):
        # Create a link_token for the given user
        response = Config.plaidClient.LinkToken.create({
            'user': {
                'client_user_id': customer_id,
            },
            'products': ['auth'],
            'client_name': 'PerfectScoreMo',
            'country_codes': ['US'],
            'language': 'en',
            'webhook': 'perfectscoremo.com',
        })
        link_token = response['link_token']

        # Send the data to the client
        return link_token
        # return jsonify(response)

    @classmethod
    def exchange_plaid_for_stripe(cls, plaid_link_public_token, account_id):
        exchange_token_response = Config.plaidClient.Item.public_token.exchange(plaid_link_public_token)
        access_token = exchange_token_response['access_token']

        stripe_response = Config.plaidClient.Processor.stripeBankAccountTokenCreate(access_token, account_id)
        bank_account_token = stripe_response['stripe_bank_account_token']

        return bank_account_token


class SendMessagesToClients():
    #static variable
    awsInstance = AWSInstance()
    def __init__(self):
        pass

    @classmethod
    def sendEmail(cls, to_address='mo@vensti.com',message='perfectscoremo',subject='Payment Instructions/Options',type=''):
        SendMessagesToClients.awsInstance.send_email(to_address=to_address,message=message,subject=subject,type=type)

    @classmethod
    def sendSMS(cls,message='perfectscoremo',from_number='+19564771274',to_number='9725847364',type=''):

        # Your Account Sid and Auth Token from twilio.com/console
        # and set the environment variables. See http://twil.io/secure

        if type == 'create':
            created_or_modified_span = "Dear parent,\n\nYour invoice has just been created. Here are the payment instructions/options (also sent to your email address):"
        elif type == 'modify':
            created_or_modified_span = "Dear parent,\n\nYour invoice has just been modified. Here are the payment instructions/options (also sent to your email address):"
        elif type == 'reminder':
            created_or_modified_span = "Dear parent,\n\nThis is an automated reminder that your invoice is overdue. Here are the payment instructions/options (also sent to your email address):"

        # + """1. Go to pay.perfectscoremo.com/input_invoice_code\n\n""" \

        text_message = "\n"+created_or_modified_span+"\n\n" \
                    + """1. Go to perfectscoremo.com\n\n""" \
                    + """2. Choose ‘Make A Payment’ from the menu\n\n""" \
                    + """3. Enter your code: """ + message +"\n\n" \
                    + """4. Read the instructions and invoice and choose a method of payment\n\n""" \
                    + """5. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free\n\n""" \
                    + """6. For installment payments, this is accepted: Credit Cards\n\n""" \
                    + """7. For full payments, these are accepted: Credit Cards, Debit Cards, ACH\n\n""" \
                    + """### We don't receive messages on this number. If you have any questions, reach out on 972-584-7364 ###\n\n""" \

        account_sid = SendMessagesToClients.awsInstance.get_secret("twilio_cred", "TWILIO_ACCOUNT_SID") or os.environ['TWILIO_ACCOUNT_SID']
        auth_token = SendMessagesToClients.awsInstance.get_secret("twilio_cred", "TWILIO_AUTH_TOKEN") or os.environ['TWILIO_AUTH_TOKEN']
        twilioClient = TwilioClient(account_sid, auth_token)

        message = twilioClient.messages .create(
            body=text_message,
            from_=from_number,
            to='+1'+to_number
        )

        print("text sent!")
        print(message.sid)

