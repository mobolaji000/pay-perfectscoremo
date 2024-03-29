import boto3
import os
import json
from botocore.exceptions import ClientError

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)

class AWSInstance():
    def __init__(self):
        pass

    def getInstance(self, service_name):
        region_name = "us-east-2"

        aws_access_key_id = os.environ.get('aws_access_key_id','')
        aws_secret_access_key = os.environ.get('aws_secret_access_key', '')

        if aws_access_key_id != '' and aws_secret_access_key != '':
            session = boto3.session.Session(aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
        else:
            session = boto3.session.Session()
        client = session.client(
            service_name=service_name,
            region_name=region_name
        )

        return client

    def get_secret(self, secret_name, secret_key):

        secret_name = secret_name
        client = self.getInstance('secretsmanager')
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = json.loads(get_secret_value_response['SecretString'])[secret_key]
            else:
                print("secret is not string!")


        return secret


    def send_email(self, to_address='mo@prepwithmo.com', message='PrepWithMo', subject='PrepWithMo', message_type='', recipient_name=''):

        if message_type == 'create_transaction_without_auto_pay':
            created_or_modified_span = "<span>Your transaction has just been <strong>created</strong>. Here are the payment/signup instructions/options (also sent to your phone number):</span><br><br>"
        elif message_type == 'modify_transaction_without_auto_pay':
            created_or_modified_span = "<span>Your transaction has just been <strong>modified</strong>. Here are the payment/signup instructions/options (also sent to your phone number):</span><br><br>"
        elif message_type == 'reminder_to_make_payment':
            created_or_modified_span = "<span>This is an automated reminder that your transaction <strong>is due</strong>. Here are the payment/signup instructions/options (also sent to your phone number):</span><br><br>"
        elif message_type == 'create_transaction_with_auto_pay':
            created_or_modified_span = "<span>Your new transaction has been created and setup for auto-payment using your method of payment on file. Here are the instructions to view the transaction details.</span><br><br>"
        elif message_type == 'modify_transaction_with_auto_pay':
            created_or_modified_span = "<span>Your transaction has been modified and setup for auto-payment using your method of payment on file. Here are the instructions to view the transaction details.</span><br><br>"
        elif message_type == 'reminder_about_appointment':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/lead/" + message[2]
            created_or_modified_span = "<span>Dear {},</span><br><br><span>Thank you for signing up for a diagnostic/consultation at PrepWithMo. This is a reminder that your appointment is on  {}. </span><br><br><span> If you have not already done so, please go to {} (also sent to your phone number) to fill out/confirm some basic information. If you have any questions, please respond to this email or call 972-584-7364.</span><br><br><span>We look forward to meeting you.</span><br><br><span>Regards,</span><br><span>Mo</span><br><br>".format(message[0],message[1],link_url)
        elif message_type == 'confirm_lead_appointment':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/lead/" + message[2]
            created_or_modified_span = "<span>Dear {},</span><br><br><span>Thank you for signing up for a diagnostic/consultation at PrepWithMo. This is a confirmation that your appointment is on  {}. </span><br><br><span> Ahead of your appointment, please go to {} (also sent to your phone number) to fill out/confirm some basic information. If you have any questions, please respond to this email or call 972-584-7364.</span><br><br><span>We look forward to meeting you.</span><br><br><span>Regards,</span><br><span>Mo</span><br><br>".format(message[0],message[1],link_url)
        elif message_type == 'notify_mo_to_modify_lead_appointment_completion_status':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/mo/" + message[3]
            created_or_modified_span = "<span>Use the below URL to modify the appointment completion status of a lead from the last hour : </span><br><br><span>{} {} {} {}</span>".format(message[0],message[1],message[2],link_url)
        elif message_type == 'notify_mo_that_lead_has_updated_lead_info':
            link_url = os.environ["url_to_start_reminder"] + "lead_info_by_lead/mo/" + message[1]
            created_or_modified_span = "<span>New update submitted by lead {}. Go check it out here: </span><br><br><span>{}</span>".format(message[0], link_url)
        elif message_type == 'notify_mo_about_suggested_one_on_one_days':
            created_or_modified_span = "<span>{}</span><br><br>".format(message)
        else:
            created_or_modified_span = message


        SENDER = "PrepWithMo <mo@info.perfectscoremo.com>"
        RECIPIENT = [to_address] if isinstance(to_address, str) else to_address
        SUBJECT = subject

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                     "This email was sent with Amazon SES using the "
                     "AWS SDK for Python (Boto)."
                     )

        if message_type == 'ask_for_student_info':
            link_url = os.environ["url_to_start_reminder"]+"""client_info/"""+message
            BODY_HTML = """<html>
                <head></head>
                <body>
                  <span>Dear {}, </span><br><br>""".format(recipient_name) \
                    + """<span>Thank you for signing up with us! </span><br><br>""" \
                    + """<span>Regular communication between us, you, and your student is a big part of our process. </span>""" \
                    + """<span>To help further that, please go to <strong><a href='"""+link_url+"""'>"""+link_url+"""</a></strong> (also sent to your phone number) to input you and your student's information.</span><br>""" \
                    + """<br><br><span>This will be used to setup text message and email updates on your student's regular progress.</span><br>""" \
                        + """<br><span>Regards,</span><br>""" \
                        + """<span>Mo</span><br>""" \
                        + """
                </body>
                </html>
                            """
        elif message_type == 'welcome_new_student':
            BODY_HTML = """<html>
                <head></head>
                <body>
                  <span>Welcome """+message+"""!</span><br><br>""" \
                    + """<span>Regular communication between us all is a big part of our process. </span>""" \
                        + """<span>To help further that, you will receive regular updates on our progress via this group email.</span><br><br>""" \
                    + """<span>You can also reach me at mo@prepwithmo.com</span><br>""" \
                        + """<br><span>Regards,</span><br>""" \
                        + """<span>Mo</span><br>""" \
                        + """
                </body>
                </html>
                            """

        elif message_type in ['create_transaction_without_auto_pay', 'modify_transaction_without_auto_pay', 'reminder_to_make_payment']:
            BODY_HTML = """<html>
                            <head></head>
                            <body>
                              <span>Dear {}, </span><br><br>""".format(recipient_name) \
                        + """<span><strong>PLEASE READ CAREFULLY!!!</strong></span><br><br>""" \
                        + created_or_modified_span \
                        + """<span>1. Go to prepwithmo.com</span><br>""" \
                        + """<span>2. Choose ‘Make A Payment’ from the menu</span><br>""" \
                        + """<span>3. Enter your code: </span>""" + "<strong>" + message + "</strong><br>" \
                        + """<span>4. If required, enter the student's contact information and the days/times that work best for their sessions. This will be used to reserve their slot in our calendar and to setup text message and email updates on their regular progress. </span><br>""" \
                        + """<span>5. Read the instructions and transaction and choose a method of payment</span><br>""" \
                        + """<span>6. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free</span><br>""" \
                        + """<span>7. For installment payments, these are accepted: Credit Cards, Debit Cards</span><br>""" \
                        + """<span>8. For full payments, these are accepted: Credit Cards, Debit Cards, ACH</span><br>""" \
                        + """<br><span>Regards,</span><br>""" \
                        + """<span>Mo</span><br>""" \
                        + """
                            </body>
                            </html>
                                        """
        elif message_type in ['create_transaction_with_auto_pay', 'modify_transaction_with_auto_pay']:
            BODY_HTML = """<html>
                            <head></head>
                            <body>
                              <span>Dear {}, </span><br><br>""".format(recipient_name) \
                        + """<span><strong>PLEASE READ CAREFULLY!!!</strong></span><br><br>""" \
                        + created_or_modified_span \
                        + """<span>1. Go to prepwithmo.com</span><br>""" \
                        + """<span>2. Choose ‘Make A Payment’ from the menu</span><br>""" \
                        + """<span>3. Enter your code: </span>""" + "<strong>" + message + "</strong><br>" \
                        + """<br><span>Regards,</span><br>""" \
                        + """<span>Mo</span><br>""" \
                        + """
                            </body>
                            </html>
                                        """
        elif message_type in ['reminder_about_appointment', 'confirm_lead_appointment','notify_mo_to_modify_lead_appointment_completion_status','notify_mo_about_suggested_one_on_one_days','notify_mo_that_lead_has_updated_lead_info']:
            BODY_HTML = """<html>
                    <head></head>
                    <body>
                       """ + created_or_modified_span + """
                    </body>
                    </html>
                                """


        CHARSET = "UTF-8"
        client = self.getInstance('ses')
        try:
            response = client.send_email(
                Destination={
                    'ToAddresses': RECIPIENT,
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                ReplyToAddresses=[
                    'mo@prepwithmo.com',
                ],
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            logger.debug("Email sent! Message ID:"),
            logger.debug(response['MessageId'])
            logger.debug(("Email message message_type is: {}".format(message_type)))
            logger.debug(BODY_HTML)

