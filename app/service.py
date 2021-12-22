from app.config import stripe
from app.aws import AWSInstance
from app.config import Config
from app.models import Transaction, InvoiceToBePaid
from app.dbUtil import AppDBUtil
from flask_login import UserMixin
import time
import datetime
import ast
import math
import traceback

from twilio.rest import Client as TwilioClient
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import ssl
ssl._create_default_https_context =  ssl._create_unverified_context


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
        existing_customer = Transaction.query.filter_by(email=clientSetupData['email']).order_by(Transaction.date_created.desc()).first() or Transaction.query.filter_by(phone_number=clientSetupData['phone_number']).order_by(Transaction.date_created.desc()).first()

        if existing_customer:
            customer = stripe.Customer.retrieve(existing_customer.stripe_customer_id)
            default_card = customer.invoice_settings.default_payment_method
            default_ach = customer.default_source
            print("payment options are: ")
            print(default_ach)
            print(default_card)
            does_customer_payment_info_exist = True if default_card or default_ach else False
        else:
            customer = stripe.Customer.create(email=clientSetupData['email'], name=clientSetupData['first_name'] + " " + clientSetupData['last_name'], phone=clientSetupData['phone_number'])
            does_customer_payment_info_exist = False
        return customer,does_customer_payment_info_exist

    def setUpIntent(self, stripe_info):
        intent = stripe.SetupIntent.create(customer=stripe_info['stripe_customer_id'])
        return intent.client_secret

    def markCustomerAsChargedOutsideofStripe(self, stripe_info):
        transaction_total = int(stripe_info['transaction_total'])

        stripe.InvoiceItem.create(
            customer=stripe_info['stripe_customer_id'],
            quantity=transaction_total,
            price=os.environ.get('price'),
        )
        transaction = stripe.Invoice.create(
            customer=stripe_info['stripe_customer_id'],
            metadata={'transaction_id': stripe_info['transaction_id']},
        )
        stripe.Invoice.pay(transaction.id, paid_out_of_band=True)

        return {'status': 'success'}

    def chargeCustomerViaACH(self, stripe_info, bank_account_token,chosen_mode_of_payment):
        existing_invoice = InvoiceToBePaid.query.filter_by(transaction_id=stripe_info['transaction_id']).first()
        if existing_invoice:
            AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)

        if chosen_mode_of_payment == 'installment-payment-ach':
            for k in range(1, int(stripe_info['installment_counter'])):
                date = datetime.datetime.fromtimestamp(stripe_info['date_' + str(k)])
                amount = stripe_info['amount_' + str(k)]

                stripe.Customer.modify(
                    stripe_info['stripe_customer_id'],
                    source=bank_account_token,
                )

                customer_default_source = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])['default_source']

                installment_amount = int(math.ceil(int(amount) * 1.03))

                stripe.InvoiceItem.create(
                    customer=stripe_info['stripe_customer_id'],
                    quantity=installment_amount,
                    price=os.environ.get('price'),
                )
                stripe_invoice_object = stripe.Invoice.create(
                    customer=stripe_info['stripe_customer_id'],
                    default_source=customer_default_source,
                    metadata={'transaction_id': stripe_info['transaction_id']},
                )

                AppDBUtil.createOrModifyInvoice(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                payment_date=date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])
        else:
            transaction_total = int(stripe_info['transaction_total'])


            stripe.Customer.modify(
                stripe_info['stripe_customer_id'],
                source=bank_account_token,
            )

            customer_default_source = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])['default_source']

            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=transaction_total,
                price=os.environ.get('price'),
            )

            transaction = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                default_source=customer_default_source,
                metadata={'transaction_id': stripe_info['transaction_id']},
            )
            stripe.Invoice.pay(transaction.id)

        return {'status': 'success'}


    def chargeCustomerViaCard(self, stripe_info, chosen_mode_of_payment, payment_id):

        #should you not only delete this after the payment has been successful?
        existing_invoice = InvoiceToBePaid.query.filter_by(transaction_id=stripe_info['transaction_id']).first()
        if existing_invoice:
            AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)

        stripe.PaymentMethod.attach(
            payment_id,
            customer=stripe_info['stripe_customer_id'],
        )

        stripe.Customer.modify(
            stripe_info['stripe_customer_id'],
            invoice_settings={'default_payment_method':payment_id},
        )

        if chosen_mode_of_payment == 'installment-payment-credit-card':

            for k in range(1, int(stripe_info['installment_counter'])):


                date = datetime.datetime.fromtimestamp(stripe_info['date_'+str(k)])
                amount = stripe_info['amount_'+str(k)]


                installment_amount = int(math.ceil(int(amount) * 1.03))
                stripe.InvoiceItem.create(
                    customer=stripe_info['stripe_customer_id'],
                    quantity=installment_amount,
                    price=os.environ.get('price'),
                )
                stripe_invoice_object = stripe.Invoice.create(
                    customer=stripe_info['stripe_customer_id'],
                    default_payment_method=payment_id,
                    auto_advance= False,
                    metadata={'transaction_id': stripe_info['transaction_id']},
                )


                AppDBUtil.createOrModifyInvoice(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                payment_date=date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])

        else:
            transaction_total = int(math.ceil(stripe_info['transaction_total']*1.03))
            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=transaction_total,
                price=os.environ.get('price'),
            )
            invoice = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                default_payment_method=payment_id,
                metadata={'transaction_id': stripe_info['transaction_id']},
            )
            stripe.Invoice.pay(invoice.id)

        return {'status': 'success'}

    def setupAutoPaymentForExistingCustomer(self, stripe_info):
        date = datetime.datetime.today() + datetime.timedelta(days=3)
        amount = stripe_info['transaction_total']

        customer = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])
        default_card = customer.invoice_settings.default_payment_method
        default_ach = customer.default_source

        if default_card:
            adjusted_price = int(math.ceil(int(amount) * 1.03))
            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=adjusted_price,
                price=os.environ.get('price'),
            )
            stripe_invoice_object = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                default_payment_method=default_card,
                auto_advance=False,
                metadata={'transaction_id': stripe_info['transaction_id']},
            )
        elif default_ach:
            adjusted_price = int(amount)
            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=adjusted_price,
                price=os.environ.get('price'),
            )

            stripe_invoice_object = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                default_source=default_ach,
                auto_advance=False,
                metadata={'transaction_id': stripe_info['transaction_id']},
            )
        else:
            print("weird: neither ach nor card was retrieved as default method of payment")
            raise ValueError('weird: neither ach nor card was retrieved as default method of payment')

        AppDBUtil.createOrModifyInvoice(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                        phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                        transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                        payment_date=date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])


class PlaidInstance():
    def __init__(self):
        pass

    @classmethod
    def get_link_token(cls, customer_id):
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

        return link_token

    @classmethod
    def exchange_plaid_for_stripe(cls, plaid_link_public_token, account_id):
        exchange_token_response = Config.plaidClient.Item.public_token.exchange(plaid_link_public_token)
        access_token = exchange_token_response['access_token']

        stripe_response = Config.plaidClient.Processor.stripeBankAccountTokenCreate(access_token, account_id)
        bank_account_token = stripe_response['stripe_bank_account_token']

        return bank_account_token


class SendMessagesToClients():
    awsInstance = AWSInstance()
    account_sid = awsInstance.get_secret("twilio_cred", "TWILIO_ACCOUNT_SID") or os.environ['TWILIO_ACCOUNT_SID']
    auth_token = awsInstance.get_secret("twilio_cred", "TWILIO_AUTH_TOKEN") or os.environ['TWILIO_AUTH_TOKEN']
    twilioClient = TwilioClient(account_sid, auth_token)

    def __init__(self):
        pass

    @classmethod
    def sendEmail(cls, to_addresses='mo@vensti.com', message='perfectscoremo', subject='Payment Instructions/Options', type=''):
        cls.awsInstance.send_email(to_addresses=to_addresses, message=message, subject=subject, type=type)

    @classmethod
    def sendSMS(cls,message='perfectscoremo',from_number='+19564771274',to_number='9725847364',type=''):

        if type == 'create_transaction_new_client':
            created_or_modified_span = "Dear parent,\n\nYour transaction has just been created. Here are the payment instructions/options (also sent to your email address):"
        elif type == 'modify_transaction':
            created_or_modified_span = "Dear parent,\n\nYour transaction has just been modified. Here are the payment instructions/options (also sent to your email address):"
        elif type == 'reminder_to_make_payment':
            created_or_modified_span = "Dear parent,\n\nThis is an automated reminder that your payment is due. Here are the payment instructions/options (also sent to your email address):"
        elif type == 'create_transaction_existing_client':
            created_or_modified_span = "Dear parent,\n\nYour new transaction has been created and is set to be paid in full using using your method of payment on file. At any point in the next 72 hours, you can change your method of payment or change to installment payments. Here are the payment instructions/options to change your method of payment (also sent to your email address):"
        elif type == 'student_info':
            link_url = os.environ["url_to_start_reminder"]+"client_info/"+message
            created_or_modified_span = "Dear parent,\n\nThank you for signing up with us! Regular communication between us, you, and your student is a big part of our process. To help further that, please go to "+link_url+" (also sent to your email address) to input you and your student's information. This will be used to setup text message and email updates on your student's regular progress."


        if type == 'to_mo':
            text_message = message
        elif  type == 'student_info':
            text_message = created_or_modified_span
        else:
            text_message = "\n" + created_or_modified_span + "\n\n" \
                           + """1. Go to perfectscoremo.com\n\n""" \
                           + """2. Choose ‘Make A Payment’ from the menu\n\n""" \
                           + """3. Enter your code: """ + message + "\n\n" \
                           + """4. Read the instructions and transaction and choose a method of payment\n\n""" \
                           + """5. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free\n\n""" \
                           + """6. For installment payments, these are accepted: Credit Cards, Debit Cards\n\n""" \
                           + """7. For full payments, these are accepted: Credit Cards, Debit Cards, ACH\n\n""" \
                           + """### We don't receive messages on this number. If you have any questions, reach out on 972-584-7364 ###\n\n"""



        message = cls.twilioClient.messages .create(
            body=text_message,
            from_=from_number,
            to='+1'+to_number
        )

        print("text sent!")
        print(message.sid)

    @classmethod
    def sendGroupEmail(cls, to_emails=[], type='', message='', subject='Group Email'):
        cls.awsInstance.send_email(to_addresses=to_address, message=message, subject=subject, type=type)

    @classmethod
    def sendGroupSMS(cls, to_numbers=[], type='', message=''):
        # cls.twilioClient.messaging.services('MGd37b2dce09791f42239043b6e949f96b').delete()
        conversations = cls.twilioClient.conversations.conversations.list(limit=50)
        for record in conversations:
            print(record.sid)
            cls.twilioClient.conversations.conversations(record.sid).delete()

        conversation = cls.twilioClient.conversations.conversations.create(messaging_service_sid='MG0faa1995ce52477a642163564295650c', friendly_name='DailyReport')
        print("conversation created!")
        print(conversation.sid)

        cls.twilioClient.conversations.conversations(conversation.sid).participants.create(messaging_binding_projected_address='+19564771274')
        cls.twilioClient.conversations.conversations(conversation.sid).participants.create(messaging_binding_address='+19725847364')

        for to_number in to_numbers:
            cls.twilioClient.conversations.conversations(conversation.sid).participants.create(messaging_binding_address='+1' + to_number)

        if type == 'create_group_chat':
            created_or_modified_span = "Welcome "+message+"!\n\n"+"This group chat is where you will receive regular updates on our progress. Don't be surprised if, on this group chat, you get a message from both 956-477-1274 and 972-584-7364. That said, if you need to speak with me, the number to call is 972-584-7364."

        cls.twilioClient.conversations.conversations(conversation.sid).messages.create(body=created_or_modified_span, author='+19564771274')
        print("group chat created!")

