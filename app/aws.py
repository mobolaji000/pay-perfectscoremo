import boto3
import os
import json
from botocore.exceptions import ClientError

class AWSInstance():
    def __init__(self):
        #self.client = None
        #self.aws_access_key_id=os.environ.get('aws_access_key_id',)

        pass

    def getInstance(self, service_name):
        region_name = "us-east-2"
        # Create a Secrets Manager client

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

            #print(get_secret_value_response)
            if 'SecretString' in get_secret_value_response:
                secret = json.loads(get_secret_value_response['SecretString'])[secret_key]
            else:
                print("secret is not string!")
                #decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])


        return secret
        # Your code goes here.


    def send_email(self, to_address='mo@vensti.com',message='perfectscoremo',subject='perfectscoremo',type=''):

        if type == 'create':
            created_or_modified_span = "<span>Your invoice has just been <strong>created</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"
        elif type == 'modify':
            created_or_modified_span = "<span>Your invoice has just been <strong>modified</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"
        elif type == 'reminder':
            created_or_modified_span = "<span>This is an automated reminder that your invoice <strong>is due</strong>. Here are the payment instructions/options (also sent to your phone number):</span><br><br>"


        # Replace sender@example.com with your "From" address.
        # This address must be verified with Amazon SES.
        #SENDER = "Perfect Score Mo <mo@vensti.com>"
        SENDER = "Perfect Score Mo <mo@info.perfectscoremo.com>"

        # Replace recipient@example.com with a "To" address. If your account
        # is still in the sandbox, this address must be verified.
        RECIPIENT = to_address

        # Specify a configuration set. If you do not want to use a configuration
        # set, comment the following variable, and the
        # ConfigurationSetName=CONFIGURATION_SET argument below.
        #CONFIGURATION_SET = "ConfigSet"

        # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        #AWS_REGION = "us-east-2"

        # The subject line for the email.
        SUBJECT = subject

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                     "This email was sent with Amazon SES using the "
                     "AWS SDK for Python (Boto). "+message
                     )

        # The HTML body of the email.
        #+ """<span>1. Go to pay.perfectscoremo.com/input_invoice_code</span><br>""" \

        BODY_HTML = """<html>
                <head></head>
                <body>
                  <span>Dear parent, </span><br><br>""" \
                    + created_or_modified_span \
                    + """<span>1. Go to perfectscoremo.com</span><br>""" \
                    + """<span>2. Choose ‘Make A Payment’ from the menu</span><br>""" \
                    + """<span>3. Enter your code: </span>""" + "<strong>" + message + "</strong><br>" \
                    + """<span>4. Read the instructions and invoice and choose a method of payment</span><br>""" \
                    + """<span>5. Please pay attention to the mode of payment you choose. Cards come with fees and ACH is free</span><br>""" \
                    + """<span>6. For installment payments, this is accepted: Credit Cards</span><br>""" \
                    + """<span>7. For full payments, these are accepted: Credit Cards, Debit Cards, ACH</span><br>""" \
                    + """
                </body>
                </html>
                            """


        # The character encoding for the email.
        CHARSET = "UTF-8"

        # Create a new SES resource and specify a region.
        #client = boto3.client('ses', region_name=AWS_REGION)
        client = self.getInstance('ses')

        # Try to send the email.
        try:
            # Provide the contents of the email.
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
                # If you are not using a configuration set, comment or delete the
                # following line
                #ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])

