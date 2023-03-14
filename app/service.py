from app.config import stripe
from app.aws import AWSInstance
from app.config import Config
from app.models import Transaction, InvoiceToBePaid
from app.dbUtil import AppDBUtil
from flask_login import UserMixin
import pytz
import re
import datetime
from sqlalchemy.sql import func
import math
import time

from twilio.rest import Client as TwilioClient
import os

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
formatter =  logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)20s() - %(lineno)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

import ssl
ssl._create_default_https_context =  ssl._create_unverified_context

date_today = datetime.datetime.now(pytz.timezone('US/Central')).date()



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
        existing_customer_total_payment_so_far = Transaction.query.filter(Transaction.email == clientSetupData['email']).with_entities(func.sum(Transaction.amount_from_transaction_paid_so_far).label('sum')).first()[0] or Transaction.query.filter(Transaction.phone_number == clientSetupData['phone_number']).with_entities(func.sum(Transaction.amount_from_transaction_paid_so_far).label('sum')).first()[0]


        if existing_customer:
            logger.info("Existing customer is: {}".format(existing_customer.first_name + ' ' + existing_customer.last_name))
            logger.info("Existing customer total is: {}".format(existing_customer_total_payment_so_far))
            customer = stripe.Customer.retrieve(existing_customer.stripe_customer_id)
            does_customer_payment_info_exist = False
            if existing_customer.does_customer_payment_info_exist == 'yes':
            #if int(existing_customer_total_payment_so_far) > 40000:
                default_card = customer.invoice_settings.default_payment_method
                default_ach = customer.default_source
                print("payment options are: ")
                print("default_ach is ",default_ach)#
                print("default_card is ",default_card)
                if default_card or default_ach:
                    does_customer_payment_info_exist = True
        else:
            customer = stripe.Customer.create(email=clientSetupData['email'], name=clientSetupData['first_name'] + " " + clientSetupData['last_name'], phone=clientSetupData['phone_number'])
            logger.info("New customer is: {}".format(clientSetupData['first_name'] + ' ' + clientSetupData['last_name']))
            does_customer_payment_info_exist = False
        return customer,does_customer_payment_info_exist

    def setUpIntent(self, stripe_info):
        intent = stripe.SetupIntent.create(customer=stripe_info['stripe_customer_id'])
        return intent.client_secret

    def markCustomerAsChargedOutsideofStripe(self, stripe_info, action=None):
        logger.info('Entering method to mark customer as charged outside of Stripe: '+str(stripe_info['transaction_id']))

        if action == 'modify':
            existing_invoices = InvoiceToBePaid.query.filter_by(transaction_id=stripe_info['transaction_id']).all()
            for existing_invoice in existing_invoices:
                #paid_out_of_band updates in stripe invoice but does not update in stripe dashboard
                stripe.Invoice.pay(existing_invoice.stripe_invoice_id, paid_out_of_band=True)
                AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)
            else:
                transaction_total = int(stripe_info['transaction_total'])

                stripe.InvoiceItem.create(
                    customer=stripe_info['stripe_customer_id'],
                    quantity=transaction_total,
                    price=os.environ.get('price'),
                )
                stripe_invoice = stripe.Invoice.create(
                    customer=stripe_info['stripe_customer_id'],
                    metadata={'transaction_id': stripe_info['transaction_id']},
                )
                # paid_out_of_band updates in stripe invoice but does not update in stripe dashboard
                stripe.Invoice.pay(stripe_invoice.id, paid_out_of_band=True)
        elif action == 'create':
            transaction_total = int(stripe_info['transaction_total'])

            stripe.InvoiceItem.create(
                customer=stripe_info['stripe_customer_id'],
                quantity=transaction_total,
                price=os.environ.get('price'),
            )
            stripe_invoice = stripe.Invoice.create(
                customer=stripe_info['stripe_customer_id'],
                metadata={'transaction_id': stripe_info['transaction_id']},
            )
            # paid_out_of_band updates in stripe invoice but does not update in stripe dashboard
            stripe.Invoice.pay(stripe_invoice.id, paid_out_of_band=True)
            logger.info('Leaving method to mark customer as charged outside of Stripe: ' + str(stripe_info['transaction_id']))

            return {'status': 'success'}

    def chargeCustomerViaACH(self, stripe_info=None, bank_account_token=None,chosen_mode_of_payment=None,default_source=None,existing_customer=None):
        try:
            # deleting exisiting invoices seems to account for a situation where we have created an invoice for exsiting customer
            # which is set to be autopayed. If customer then attempts to pay via another methiod, or if we modifgy the invoice,
            # we dont want to double-charge

            existing_invoices = InvoiceToBePaid.query.filter_by(transaction_id=stripe_info['transaction_id']).all()
            for existing_invoice in existing_invoices:
                AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)

            #overwrite any exsiting default_payment_method to ensure that new ach is the default
            stripe.Customer.modify(
                stripe_info['stripe_customer_id'],
                invoice_settings={'default_payment_method': ''},
            )

            if bank_account_token:
                stripe.Customer.modify(
                    stripe_info['stripe_customer_id'],
                    source=bank_account_token,
                )
                customer_default_source = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])['default_source']
            elif default_source:
                customer_default_source = default_source
            else:
                raise Exception('Customer has neither existing nor new ACH details.')

            if existing_customer:
                logger.info('Exisiting customer: ' + str(stripe_info['stripe_customer_id'])+' '+ str(stripe_info['name']))

            if chosen_mode_of_payment == 'installment-payment-ach':
                logger.info('Installment payment ACH: ' + str(stripe_info['transaction_id']) + ' ' + str(stripe_info['name']))
                logger.debug(f"strip_info is {stripe_info}")

                invoice_dates_and_amounts_to_update_due_to_pausing = []

                for k in range(1, int(stripe_info['installment_counter'])):

                    if f'date_{k}' in stripe_info:
                        if stripe_info.get('paused_payment_resumption_date'):
                            if k == 1:
                                invoice_dates_and_amounts_to_update_due_to_pausing.append((datetime.datetime.strptime(stripe_info['paused_payment_resumption_date'], '%Y-%m-%d'), stripe_info[f'amount_{k}']))
                            else:
                                difference_between_this_installment_date_and_previous_installment_date = (datetime.datetime.fromtimestamp(stripe_info[f'date_{k}']) - datetime.datetime.fromtimestamp(stripe_info[f'date_{k - 1}'])).days
                                current_installment_date = invoice_dates_and_amounts_to_update_due_to_pausing[k - 2][0]
                                invoice_dates_and_amounts_to_update_due_to_pausing.append((current_installment_date + datetime.timedelta(days=difference_between_this_installment_date_and_previous_installment_date), stripe_info[f'amount_{k}']))

                        else:
                            invoice_dates_and_amounts_to_update_due_to_pausing.append((datetime.datetime.fromtimestamp(stripe_info[f'date_{k}']), stripe_info[f'amount_{k}']))

                for invoice_date, amount in invoice_dates_and_amounts_to_update_due_to_pausing:
                    payment_date = invoice_date

                    installment_amount = int(math.ceil(int(amount) * 1.00))
                    # switched this from 1.03 to 1.00 because this is ACH and you should not multiply by 1.03

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

                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])

            elif chosen_mode_of_payment == 'full-payment-ach':
                logger.info('Full payment ACH for new customer: ' + str(stripe_info['transaction_id']) + ' ' + str(stripe_info['name']))
                payment_date = date_today

                amount = stripe_info['transaction_total']
                transaction_total = int(stripe_info['transaction_total'])

                if stripe_info['pause_payment'] == 'yes':
                    paused_payment_resumption_date = None if stripe_info.get('paused_payment_resumption_date') == '' else stripe_info.get('paused_payment_resumption_date')
                    if paused_payment_resumption_date:
                        if datetime.datetime.strptime(paused_payment_resumption_date,'%Y-%m-%d').date() > payment_date:
                            payment_date = paused_payment_resumption_date
                            logger.info(f"Payment {stripe_info['transaction_id']} is paused until {payment_date}.")
                    else:
                        payment_date = paused_payment_resumption_date
                        logger.info(f"Payment {stripe_info['transaction_id']} is paused indefinitely.")

                    stripe.InvoiceItem.create(
                        customer=stripe_info['stripe_customer_id'],
                        quantity=transaction_total,
                        price=os.environ.get('price'),
                    )

                    stripe_invoice_object = stripe.Invoice.create(
                        customer=stripe_info['stripe_customer_id'],
                        default_source=customer_default_source,
                        auto_advance=False,
                        metadata={'transaction_id': stripe_info['transaction_id']},
                    )

                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])

                else:
                    transaction_total = int(stripe_info['transaction_total'])

                    stripe.InvoiceItem.create(
                        customer=stripe_info['stripe_customer_id'],
                        quantity=transaction_total,
                        price=os.environ.get('price'),
                    )

                    invoice = stripe.Invoice.create(
                        customer=stripe_info['stripe_customer_id'],
                        default_source=customer_default_source,
                        metadata={'transaction_id': stripe_info['transaction_id']},
                    )
                    stripe.Invoice.pay(invoice.id)

            elif chosen_mode_of_payment == 'recurring-payment-ach':
                logger.info('Recurring payment ach: ' + str(stripe_info['transaction_id']) + ' ' + str(stripe_info['name']))

                recurring_payment_start_date = stripe_info['paused_payment_resumption_date'] if  stripe_info['paused_payment_resumption_date'] and datetime.datetime.strptime(stripe_info['paused_payment_resumption_date'], '%Y-%m-%d').date() >=  datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() else stripe_info['recurring_payment_start_date']

                number_of_days_from_start_of_recurring_payment = abs((datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() - date_today)).days
                recurring_payment_frequency = stripe_info['recurring_payment_frequency']

                transaction_total = int(stripe_info['transaction_total'])
                payment_date = recurring_payment_start_date

                if datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() < date_today:

                    for day_index in range(0, number_of_days_from_start_of_recurring_payment):
                        if day_index % recurring_payment_frequency == 0:
                            payment_date = datetime.datetime.strptime(payment_date, '%Y-%m-%d').date() + datetime.timedelta(days=day_index) if type(payment_date) is str else payment_date + datetime.timedelta(days=day_index)

                            stripe.InvoiceItem.create(
                                customer=stripe_info['stripe_customer_id'],
                                quantity=transaction_total,
                                price=os.environ.get('price'),
                            )
                            stripe_invoice_object = stripe.Invoice.create(
                                customer=stripe_info['stripe_customer_id'],
                                default_source=customer_default_source,
                                auto_advance=False,
                                metadata={'transaction_id': stripe_info['transaction_id']},
                            )
                            AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                                    phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                                    transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                                    payment_date=payment_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])

                else:
                    stripe.InvoiceItem.create(
                        customer=stripe_info['stripe_customer_id'],
                        quantity=transaction_total,
                        price=os.environ.get('price'),
                    )
                    stripe_invoice_object = stripe.Invoice.create(
                        customer=stripe_info['stripe_customer_id'],
                        default_source=customer_default_source,
                        auto_advance=False,
                        metadata={'transaction_id': stripe_info['transaction_id']},
                    )
                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])

            return {'status': 'success'}
        except Exception as e:
            logger.exception(e)
            transaction_name = stripe_info['name'].split()[0] + " " + stripe_info['name'].split()[1]
            if os.environ.get("DEPLOY_REGION") == 'PROD':
                SendMessagesToClients.sendSMS(to_numbers='9725847364', message=f"Transaction setup/payment failed for {transaction_name} of transaction_id {stripe_info['transaction_id']} with error {e}. Go check the logs!", message_type='to_mo')
            return {'status': 'error'}

    def chargeCustomerViaCard(self, stripe_info, chosen_mode_of_payment, payment_id,existing_customer=None):
        try:
            client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(stripe_info['transaction_id'])

            # deleting exisiting invoices seems to account for a situation where we have created an invoice for exsiting customer
            # which is set to be autopayed. If customer then attempts to pay via another methiod, or if we modifgy the invoice,
            # we dont want to double-charge

            existing_invoices = InvoiceToBePaid.query.filter_by(transaction_id=stripe_info['transaction_id']).all()


            for existing_invoice in existing_invoices:
                AppDBUtil.deleteInvoiceToBePaid(existing_invoice.transaction_id, existing_invoice.stripe_invoice_id)

            stripe.PaymentMethod.attach(
                payment_id,
                customer=stripe_info['stripe_customer_id'],
            )

            stripe.Customer.modify(
                stripe_info['stripe_customer_id'],
                invoice_settings={'default_payment_method':payment_id},
            )

            if existing_customer:
                logger.info('Existing customer: ' + str(stripe_info['transaction_id']) + str(stripe_info['stripe_customer_id'])+' '+ str(stripe_info['name']))

            if chosen_mode_of_payment == 'installment-payment-credit-card':
                logger.info('Installment payment credit card: ' + str(stripe_info['transaction_id'])+' '+ str(stripe_info['name']))
                logger.debug(f"strip_info is {stripe_info}")

                invoice_dates_and_amounts_to_update_due_to_pausing = []

                for k in range(1, int(stripe_info['installment_counter'])):

                        if f'date_{k}' in stripe_info:
                            if stripe_info.get('paused_payment_resumption_date'):
                                if k == 1:
                                    invoice_dates_and_amounts_to_update_due_to_pausing.append((datetime.datetime.strptime(stripe_info['paused_payment_resumption_date'],'%Y-%m-%d'),stripe_info[f'amount_{k}']))
                                else:
                                    difference_between_this_installment_date_and_previous_installment_date = (datetime.datetime.fromtimestamp(stripe_info[f'date_{k}']) - datetime.datetime.fromtimestamp(stripe_info[f'date_{k-1}'])).days
                                    current_installment_date = invoice_dates_and_amounts_to_update_due_to_pausing[k - 2][0]
                                    invoice_dates_and_amounts_to_update_due_to_pausing.append((current_installment_date + datetime.timedelta(days=difference_between_this_installment_date_and_previous_installment_date),stripe_info[f'amount_{k}']))

                            else:
                                invoice_dates_and_amounts_to_update_due_to_pausing.append((datetime.datetime.fromtimestamp(stripe_info[f'date_{k}']),stripe_info[f'amount_{k}']))

                for invoice_date,amount in invoice_dates_and_amounts_to_update_due_to_pausing:
                    payment_date = invoice_date

                    # if stripe_info['pause_payment'] == 'yes':
                    #     if stripe_info.get('paused_payment_resumption_date'):
                    #         if datetime.datetime.strptime(stripe_info.get('paused_payment_resumption_date'),'%Y-%m-%d').date() > payment_date:
                    #             payment_date =  stripe_info.get('paused_payment_resumption_date')
                    #     else:
                    #         logger.info(f"Payment {stripe_info['transaction_id']} is paused indefinitely.")
                    #         return {'status': 'success'}

                    # if stripe_info['pause_payment'] == 'yes':
                    #     pauseInstallmentPayment(transaction_id, pause_payment, paused_payment_resumption_date)

                    #amount = stripe_info['amount_'+str(k)]

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


                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])

            elif chosen_mode_of_payment == 'full-payment-credit-card':
                logger.info('Full payment credit card new customer: ' + str(stripe_info['transaction_id']) + ' ' + str(stripe_info['name']))
                payment_date = date_today

                transaction_total = int(math.ceil((stripe_info['transaction_total'] * 1.03) - (client_info['diag_total'] * 0.03)))
                amount = str(transaction_total)

                #(client_info['diag_total'] * 0.03) is added to stop charging extra 3% for diagnostics

                if stripe_info['pause_payment'] == 'yes':
                    paused_payment_resumption_date = None if stripe_info.get('paused_payment_resumption_date') == '' else stripe_info.get('paused_payment_resumption_date')
                    if paused_payment_resumption_date:
                        if datetime.datetime.strptime(paused_payment_resumption_date,'%Y-%m-%d').date() > payment_date:
                            payment_date =  paused_payment_resumption_date
                            logger.info(f"Payment {stripe_info['transaction_id']} is paused until {payment_date}.")
                    else:
                        payment_date = paused_payment_resumption_date
                        logger.info(f"Payment {stripe_info['transaction_id']} is paused indefinitely.")

                    stripe.InvoiceItem.create(
                        customer=stripe_info['stripe_customer_id'],
                        quantity=transaction_total,
                        price=os.environ.get('price'),
                    )

                    stripe_invoice_object = stripe.Invoice.create(
                        customer=stripe_info['stripe_customer_id'],
                        default_payment_method=payment_id,
                        auto_advance=False,
                        metadata={'transaction_id': stripe_info['transaction_id']},
                    )
                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])

                else:
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




                    # if stripe_info['pause_payment'] == 'yes':
                    #     if stripe_info.get('paused_payment_resumption_date'):
                    #         if datetime.datetime.strptime(stripe_info.get('paused_payment_resumption_date'),'%Y-%m-%d').date() > payment_date:
                    #             payment_date = stripe_info.get('paused_payment_resumption_date')
                    #     else:
                    #         logger.info(f"Payment {stripe_info['transaction_id']} is paused indefinitely.")
                    #         payment_date = stripe_info.get('paused_payment_resumption_date')
                    #
                    #     stripe.InvoiceItem.create(
                    #         customer=stripe_info['stripe_customer_id'],
                    #         quantity=transaction_total,
                    #         price=os.environ.get('price'),
                    #     )
                    #
                    #     stripe_invoice_object = stripe.Invoice.create(
                    #         customer=stripe_info['stripe_customer_id'],
                    #         default_payment_method=payment_id,
                    #         auto_advance=False,
                    #         metadata={'transaction_id': stripe_info['transaction_id']},
                    #     )
                    #     AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                    #                                             phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                    #                                             transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                    #                                             payment_date=payment_date, payment_amount=amount, stripe_invoice_id=stripe_invoice_object['id'])
                    #
                    #
                    # else:
                    #     stripe.InvoiceItem.create(
                    #         customer=stripe_info['stripe_customer_id'],
                    #         quantity=transaction_total,
                    #         price=os.environ.get('price'),
                    #     )
                    #     invoice = stripe.Invoice.create(
                    #         customer=stripe_info['stripe_customer_id'],
                    #         default_payment_method=payment_id,
                    #         metadata={'transaction_id': stripe_info['transaction_id']},
                    #     )
                    #     stripe.Invoice.pay(invoice.id)

            elif chosen_mode_of_payment == 'recurring-payment-credit-card':
                logger.info('Recurring payment credit card: ' + str(stripe_info['transaction_id'])+' '+ str(stripe_info['name']))

                recurring_payment_start_date =  stripe_info['paused_payment_resumption_date'] if  stripe_info['paused_payment_resumption_date'] and datetime.datetime.strptime(stripe_info['paused_payment_resumption_date'], '%Y-%m-%d').date() >=  datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() else stripe_info['recurring_payment_start_date']

                number_of_days_from_start_of_recurring_payment = abs((datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() - date_today)).days
                recurring_payment_frequency = stripe_info['recurring_payment_frequency']

                transaction_total = math.ceil(client_info['transaction_total'] * 1.03)
                payment_date = recurring_payment_start_date

                if datetime.datetime.strptime(stripe_info['recurring_payment_start_date'], '%Y-%m-%d').date() < date_today:

                    for day_index in range(0,number_of_days_from_start_of_recurring_payment):
                        if day_index % recurring_payment_frequency == 0:

                            payment_date = datetime.datetime.strptime(payment_date, '%Y-%m-%d').date() + datetime.timedelta(days=day_index) if type(payment_date) is str else payment_date + datetime.timedelta(days=day_index)

                            stripe.InvoiceItem.create(
                                customer=stripe_info['stripe_customer_id'],
                                quantity=transaction_total,
                                price=os.environ.get('price'),
                            )
                            stripe_invoice_object = stripe.Invoice.create(
                                customer=stripe_info['stripe_customer_id'],
                                default_payment_method=payment_id,
                                auto_advance=False,
                                metadata={'transaction_id': stripe_info['transaction_id']},
                            )
                            AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                                    phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                                    transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                                    payment_date=payment_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])

                else:
                    stripe.InvoiceItem.create(
                        customer=stripe_info['stripe_customer_id'],
                        quantity=transaction_total,
                        price=os.environ.get('price'),
                    )
                    stripe_invoice_object = stripe.Invoice.create(
                        customer=stripe_info['stripe_customer_id'],
                        default_payment_method=payment_id,
                        auto_advance=False,
                        metadata={'transaction_id': stripe_info['transaction_id']},
                    )
                    AppDBUtil.createOrModifyInvoiceToBePaid(first_name=stripe_info['name'].split()[0], last_name=stripe_info['name'].split()[1],
                                                            phone_number=stripe_info['phone_number'], email=stripe_info['email'],
                                                            transaction_id=stripe_info['transaction_id'], stripe_customer_id=stripe_info['stripe_customer_id'],
                                                            payment_date=payment_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])

            # if stripe_info['pause_payment'] == 'yes':
                #     if stripe_info.get('paused_payment_resumption_date'):
                #         if datetime.datetime.strptime(stripe_info.get('paused_payment_resumption_date'),'%Y-%m-%d').date() > payment_date:
                #             payment_date = stripe_info.get('paused_payment_resumption_date')
                #     else:
                #         logger.info(f"Payment {stripe_info['transaction_id']} is paused indefinitely.")
                #         return {'status': 'success'}






            return {'status': 'success'}
        except Exception as e:
            logger.exception(e)
            transaction_name = stripe_info['name'].split()[0] + " " + stripe_info['name'].split()[1]
            if os.environ.get("DEPLOY_REGION") == 'PROD':
                SendMessagesToClients.sendSMS(to_numbers='9725847364', message=f"Transaction setup/payment failed for {transaction_name} of transaction_id {stripe_info['transaction_id']} with error {e}. Go check the logs!", message_type='to_mo')
            return {'status': 'error'}

    def setupRecurringPaymentsDueToday(self):
        all_transaction_ids = AppDBUtil.getAllTransactionIds()
        for transaction_id in all_transaction_ids:
            client_info,products_info,showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)

            make_payment_recurring = client_info['make_payment_recurring']
            pause_payment = client_info['pause_payment']


            if (make_payment_recurring == 'yes' and pause_payment == 'no'):

                recurring_payment_start_date = client_info['paused_payment_resumption_date'] if client_info['paused_payment_resumption_date'] and client_info['paused_payment_resumption_date'] >= client_info['recurring_payment_start_date'] else client_info['recurring_payment_start_date']
                recurring_payment_frequency = client_info['recurring_payment_frequency']
                number_of_days_from_start_of_recurring_payment = abs((recurring_payment_start_date - date_today)).days #absolute value to account for timedelta's treatment of negative difference in dates
                logger.info(f"For {transaction_id}, recurring_payment_start_date is {recurring_payment_start_date}, recurring_payment_frequency is {recurring_payment_frequency}, and number_of_days_from_start_of_recurring_payment is {number_of_days_from_start_of_recurring_payment}")

                if recurring_payment_start_date < date_today  and number_of_days_from_start_of_recurring_payment % recurring_payment_frequency == 0:

                    customer = stripe.Customer.retrieve(client_info['stripe_customer_id'])
                    default_card = customer.invoice_settings.default_payment_method
                    default_ach = customer.default_source

                    if default_card:
                        logger.info('Recurring payment credit card: ' + str(client_info['transaction_id']) + ' ' + str(client_info['first_name'])+ " " + str(client_info['last_name']))

                        transaction_total = math.ceil(client_info['transaction_total'] * 1.03)

                        stripe.InvoiceItem.create(
                            customer=client_info['stripe_customer_id'],
                            quantity=transaction_total,
                            price=os.environ.get('price'),
                        )
                        stripe_invoice_object = stripe.Invoice.create(
                            customer=client_info['stripe_customer_id'],
                            default_payment_method=default_card,
                            auto_advance=False,
                            metadata={'transaction_id': client_info['transaction_id']},
                        )
                        AppDBUtil.createOrModifyInvoiceToBePaid(first_name=client_info['first_name'], last_name=client_info['last_name'],
                                                                phone_number=client_info['phone_number'], email=client_info['email'],
                                                                transaction_id=client_info['transaction_id'], stripe_customer_id=client_info['stripe_customer_id'],
                                                                payment_date=recurring_payment_start_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])

                    elif default_ach:
                        logger.info('Recurring payment ACH: ' + str(client_info['transaction_id']) + ' ' + str(client_info['first_name']) + " " + str(client_info['last_name']))

                        transaction_total = math.ceil(client_info['transaction_total'])

                        stripe.InvoiceItem.create(
                            customer=client_info['stripe_customer_id'],
                            quantity=transaction_total,
                            price=os.environ.get('price'),
                        )
                        stripe_invoice_object = stripe.Invoice.create(
                            customer=client_info['stripe_customer_id'],
                            default_source=default_ach,
                            auto_advance=False,
                            metadata={'transaction_id': client_info['transaction_id']},
                        )
                        AppDBUtil.createOrModifyInvoiceToBePaid(first_name=client_info['first_name'], last_name=client_info['last_name'],
                                                                phone_number=client_info['phone_number'], email=client_info['email'],
                                                                transaction_id=client_info['transaction_id'], stripe_customer_id=client_info['stripe_customer_id'],
                                                                payment_date=recurring_payment_start_date, payment_amount=transaction_total, stripe_invoice_id=stripe_invoice_object['id'])


                    else:
                            logger.error("weird: neither ach nor card was retrieved as default method of payment")
                            raise ValueError('weird: neither ach nor card was retrieved as default method of payment')

    def restartPausedPayments(self):
        all_transaction_ids = AppDBUtil.getAllTransactionIds()
        for transaction_id in all_transaction_ids:
            client_info, products_info, showACHOverride = AppDBUtil.getTransactionDetails(transaction_id)

            pause_payment = client_info['pause_payment']
            paused_payment_resumption_date = client_info['paused_payment_resumption_date']


            if (pause_payment == 'yes' and paused_payment_resumption_date and paused_payment_resumption_date <= date_today):
                AppDBUtil.updatePausePaymentStatus(transaction_id,'no',None)
                logger.info(f"Transaction {transaction_id} slated to be unpaused on {paused_payment_resumption_date} and actually unpaused on {date_today}")

    def setupAutoPaymentForExistingCustomer(self, stripe_info):
        logger.info('Inside setupAutoPaymentForExistingCustomer() for ' + str(stripe_info['transaction_id'])+' '+ str(stripe_info['name']))

        customer = stripe.Customer.retrieve(stripe_info['stripe_customer_id'])
        default_card = customer.invoice_settings.default_payment_method
        default_ach = customer.default_source

        if default_card:
            if stripe_info['installment_counter'] > 1:
                chosen_mode_of_payment = 'installment-payment-credit-card'
            elif stripe_info['make_payment_recurring'] == 'yes':
                chosen_mode_of_payment = 'recurring-payment-credit-card'
            else:
                chosen_mode_of_payment = 'full-payment-credit-card'

            self.chargeCustomerViaCard(stripe_info, chosen_mode_of_payment, default_card, existing_customer=True)

        elif default_ach:
            if stripe_info['installment_counter'] > 1:
                chosen_mode_of_payment = 'installment-payment-ach'
            elif stripe_info['make_payment_recurring'] == 'yes':
                chosen_mode_of_payment = 'recurring-payment-ach'
            else:
                chosen_mode_of_payment = 'full-payment-ach'

            self.chargeCustomerViaACH(stripe_info=stripe_info,chosen_mode_of_payment=chosen_mode_of_payment,default_source=default_ach,existing_customer=True)

        else:
            logger.error("weird: neither ach nor card was retrieved as default method of payment")
            raise ValueError('weird: neither ach nor card was retrieved as default method of payment')

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
            'client_name': 'PrepWithMo',
            'country_codes': ['US'],
            'language': 'en',
            'webhook': 'prepwithmo.com',
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
    def sendEmail(cls, to_address='mo@prepwithmo.com', message='PrepWithMo', subject='PrepWithMo', message_type='', recipient_name=''):
        cls.awsInstance.send_email(to_address=to_address, message=message, subject=subject, message_type=message_type, recipient_name=recipient_name)

    @classmethod
    def sendSMS(cls, to_numbers=None, message_type='', message='perfectscoremo', recipient_name=''):

        if message_type == 'create_transaction_without_auto_pay':
            created_or_modified_span = "Dear {},\n\nPLEASE READ CAREFULLY!!!\n\nYour transaction has just been created. Here are the payment/signup instructions/options (also sent to your email address):".format(recipient_name)
        elif message_type == 'modify_transaction_without_auto_pay':
            created_or_modified_span = "Dear {},\n\nPLEASE READ CAREFULLY!!!\n\nYour transaction has just been modified. Here are the payment/signup instructions/options (also sent to your email address):".format(recipient_name)
        elif message_type == 'create_transaction_with_auto_pay':
            created_or_modified_span = "Dear {},\n\nPLEASE READ CAREFULLY!!!\n\nYour new transaction has been created and setup for auto-payment using your method of payment on file. Here are the instructions to view the transaction details.".format(recipient_name)
        elif message_type == 'modify_transaction_with_auto_pay':
            created_or_modified_span = "Dear {},\n\nPLEASE READ CAREFULLY!!!\n\nYour transaction has been modified and setup for auto-payment using your method of payment on file. Here are the instructions to view the transaction details.".format(recipient_name)
        elif message_type == 'ask_for_student_info':
            link_url = os.environ["url_to_start_reminder"]+"client_info/"+message
            created_or_modified_span = "Dear {},\n\nThank you for signing up with us! Regular communication between us, you, and your student is a big part of our process. To help further that, please go to "+link_url+" (also sent to your email address) to input you and your student's information. \n\n This will be used to setup text message and email updates on your student's regular progress.".format(recipient_name)
        elif message_type == 'welcome_new_student':
            created_or_modified_span = "Welcome " + message + "!\n\n" + "I am Mo's automated assistant, and I will be sending reports on your progress via this group chat. Mo (972-584-7364) and his personal assistant (972-503-9573) are on the chat as well to follow up with you on your daily homework/review sessions. If you need to speak with someone, though, please feel free to call Mo. \n\n If you're signed up for tutoring, make sure to have notebook and a pencil for your first session. And if you're signed up for college applications/essays/scholarships, make sure to have your laptop for our first session. \n\n We can't wait to see you succeed!"
        elif message_type == 'questions':
            created_or_modified_span = "I am happy to clarify any questions you might have!"
        elif message_type == 'referral_request':
            created_or_modified_span = "Oh, and one more note to the family...if you have any friends/families looking to raise their SAT/ACT scores or write compelling college application essays, have them check us out at prepwithmo.com or call us at 972-584-7364. We appreciate the referral!"
        elif message_type == 'confirm_lead_appointment':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/lead/" + message[2]
            created_or_modified_span = "Dear {},\n\nThank you for signing up for a diagnostic/consultation at PrepWithMo.\n\nThis is a confirmation that your appointment is on  {}. Ahead of your appointment, please go to {} (also sent to your email address) to fill out/confirm some basic information. If you have any questions, please call 972-584-7364. We look forward to meeting you.\n\nRegards,\n\nMo".format(message[0], message[1], link_url)
        elif message_type == 'reminder_about_appointment':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/lead/" + message[2]
            created_or_modified_span = "Dear {},\n\nThank you for signing up for a diagnostic/consultation at PrepWithMo.\n\nThis is a reminder that your appointment is on  {}. If you have not already done so, please go to {} (also sent to your email address) to fill out/confirm some basic information. If you have any questions, please call 972-584-7364. We look forward to meeting you.\n\nRegards,\n\nMo".format(message[0], message[1], link_url)
        elif message_type == 'reminder_to_make_payment':
            created_or_modified_span = "Dear {},\n\nPLEASE READ CAREFULLY!!!\n\nThis is an automated reminder that your payment is due. Here are the payment instructions/options (also sent to your email address):".format(recipient_name)


        if message_type in ['to_mo']:
            text_message = message
        elif message_type in ['ask_for_student_info', 'welcome_new_student', 'questions', 'referral_request', 'confirm_lead_appointment', 'reminder_about_appointment', 'reminder_to_make_payment']:
            text_message = created_or_modified_span
        elif message_type in ['create_transaction_with_auto_pay', 'modify_transaction_with_auto_pay']:
            text_message = "\n" + created_or_modified_span + "\n\n" \
                           + """1. Go to prepwithmo.com\n\n""" \
                           + """2. Choose ‘Make A Payment’ from the menu\n\n""" \
                           + """3. Enter your code: """ + message + "\n\n" \
                           + """### We don't receive messages on this number. If you have any questions, reach out on 972-584-7364 ###\n\n""" \
                           + """Regards,\n\n""" \
                           + """Mo\n\n"""
        elif message_type in ['create_transaction_without_auto_pay', 'modify_transaction_without_auto_pay']:
            text_message = "\n" + created_or_modified_span + "\n\n" \
                           + """1. Go to prepwithmo.com\n\n""" \
                           + """2. Choose ‘Make A Payment’ from the menu\n\n""" \
                           + """3. Enter your code: """ + message + "\n\n" \
                           + """4. If required, enter the student's contact information and the days/times that work best for their sessions. This will be used to reserve their slot in our calendar and to setup text message and email updates on their regular progress.\n\n""" \
                           + """5. Read the instructions and transaction and choose a method of payment\n\n""" \
                           + """6. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free\n\n""" \
                           + """7. For installment payments, these are accepted: Credit Cards, Debit Cards\n\n""" \
                           + """8. For full payments, these are accepted: Credit Cards, Debit Cards, ACH\n\n""" \
                           + """### We don't receive messages on this number. If you have any questions, reach out on 972-584-7364 ###\n\n""" \
                           + """Regards,\n\n""" \
                           + """Mo\n\n"""

        if type(to_numbers) is str:
            logger.info("Single Recipient SMS!")
            sent_message = cls.twilioClient.messages.create(
            body=text_message,
            from_='+19564771274',
            to='+1' + to_numbers
            )

            logger.info("text sent!")
            logger.info(sent_message.sid)
            logger.info(text_message)
        elif type(to_numbers) is list:
            logger.info("Multiple Recipient SMS!")
            conversations = cls.twilioClient.conversations.conversations.list(limit=50)
            for record in conversations:
                print(record.sid)
                cls.twilioClient.conversations.conversations(record.sid).delete()

            conversation = cls.twilioClient.conversations.conversations.create(
                messaging_service_sid='MG0faa1995ce52477a642163564295650c', friendly_name='PaymentService')
            print("conversation created!")
            print(conversation.sid)

            cls.twilioClient.conversations.conversations(conversation.sid).participants.create(
                messaging_binding_projected_address='+19564771274')
            cls.twilioClient.conversations.conversations(conversation.sid).participants.create(
                messaging_binding_address='+19725847364')

            for recipient in to_numbers:
                print("number to add is :", recipient)
                cls.twilioClient.conversations.conversations(conversation.sid).participants.create(
                    messaging_binding_address='+1' + recipient)

            if message_type == 'welcome_new_student' or message_type == 'referral_request':
                print("adding assistant's number")
                cls.twilioClient.conversations.conversations(conversation.sid).participants.create(
                    messaging_binding_address='+19725039573')

            cls.twilioClient.conversations.conversations(conversation.sid).messages.create(body=text_message,author='+19564771274')
            logger.info("group chat created!")
        else:
            raise Exception("Neither string not list was sent to sendSMS method!")

class MiscellaneousUtils():
    def __init__(self):
        pass

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
