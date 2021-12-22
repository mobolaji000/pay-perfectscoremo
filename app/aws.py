import boto3
import os
import json
from botocore.exceptions import ClientError

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


    def send_email(self, to_address='mo@vensti.com',message='perfectscoremo',subject='perfectscoremo',type=''):

        if type == 'create_transaction_new_client':
            created_or_modified_span = "<span>Your transaction has just been <strong>created</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"
        elif type == 'modify_transaction':
            created_or_modified_span = "<span>Your transaction has just been <strong>modified</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"
        elif type == 'reminder_to_make_payment':
            created_or_modified_span = "<span>This is an automated reminder that your transaction <strong>is due</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"
        elif type == 'create_transaction_existing_client':
            created_or_modified_span = "<span>Your new transaction has been created and <strong>is set to be paid in full using using your method of payment on file</strong>. At any point in the next <strong>72 hours</strong>, you can change your method of payment or change to installment payments. Here are the payment instructions/options to change your method of payment (also sent to your phone number):</span><br><br>"

        SENDER = "Perfect Score Mo <mo@info.perfectscoremo.com>"
        RECIPIENT = to_address
        SUBJECT = subject

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                     "This email was sent with Amazon SES using the "
                     "AWS SDK for Python (Boto). "+message
                     )

        if type == 'student_info':
            link_url = os.environ["url_to_start_reminder"]+"""client_info/"""+message
            BODY_HTML = """<html>
                <head></head>
                <body>
                  <span>Dear parent, </span><br><br>""" \
                    + """<span>Thank you for signing up with us! </span><br><br>""" \
                    + """<span>Regular communication between us, you, and your student is a big part of our process. </span><br>""" \
                    + """<span>To help further that, please go to <strong><a href='"""+link_url+"""'>"""+link_url+"""</a></strong> (also sent to your phone number) to input you and your student's information.</span><br>""" \
                    + """<span>This will be used to setup text message and email updates on your student's regular progress.</span><br>""" \
                    + """
                </body>
                </html>
                            """
        else:
            BODY_HTML = """<html>
                            <head></head>
                            <body>
                              <span>Dear parent, </span><br><br>""" \
                        + created_or_modified_span \
                        + """<span>1. Go to perfectscoremo.com</span><br>""" \
                        + """<span>2. Choose ‘Make A Payment’ from the menu</span><br>""" \
                        + """<span>3. Enter your code: </span>""" + "<strong>" + message + "</strong><br>" \
                        + """<span>4. Read the instructions and transaction and choose a method of payment</span><br>""" \
                        + """<span>5. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free</span><br>""" \
                        + """<span>6. For installment payments, these are accepted: Credit Cards, Debit Cards</span><br>""" \
                        + """<span>7. For full payments, these are accepted: Credit Cards, Debit Cards, ACH</span><br>""" \
                        + """
                            </body>
                            </html>
                                        """


        CHARSET = "UTF-8"
        client = self.getInstance('ses')
        try:
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                    ],
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
                    'mo@perfectscoremo.com',
                ],
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])

