import boto3
import os
import json
from botocore.exceptions import ClientError

class AWSInstance():
    def __init__(self):
        #self.client = None
        self.aws_access_key_id=os.environ.get('aws_access_key_id',)

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

