import sys
import boto3
import s3nake_print
def get_vulnerable_buckets(client,buckets):
    protected_buckets, maybe_vulnerable_buckets,vulnerable_buckets =[],[],[]
    for bucket in buckets:
        try:
            response = client.get_bucket_versioning(Bucket=bucket)
            versioning = response.get('Status', 'Disabled')
            mfa_delete = response.get('MFADelete', 'Disabled')

            if versioning == 'Enabled' and mfa_delete == 'Enabled':
                protected_buckets.append(bucket)
                

            elif versioning == 'Enabled' and mfa_delete != 'Enabled':
                maybe_vulnerable_buckets.append(bucket)
            else:
               vulnerable_buckets.append(bucket)
        except ClientError as error:
            s3nake_print(f'    {error.response["Error"]["Code"]} error running s3:GetBucketVersioning on bucket {bucket}: {error.response["Error"]["Message"]}')
            # Continue on anyways, doesn't mean every bucket will fail
    return protected_buckets, maybe_vulnerable_buckets,vulnerable_buckets

def copy_all_files_to_bucket_(client,src,dst):
    for key in get_s3_keys_as_generator(client,src):
        sys.stdout.write('\r\033[K' + s3nake_print.Dim(key) + '\r')
        s3 = boto3.resource('s3')
        copy_source = {
            'Bucket': src,
            'Key': key
        }
        s3.meta.client.copy(copy_source, dst, key)


def delete_all_objects_from_s3_folder(client,bucket_name):
    """
    This function deletes all files in a folder from S3 bucket
    :return: None
    """
    for key in get_s3_keys_as_generator(client,bucket_name):
        sys.stdout.write('\r\033[K' +  s3nake_print.Dim(key) + '\r')
        s3 = boto3.resource('s3')
        s3.Object(bucket_name, key).delete()

def get_s3_keys_as_generator(client,bucket):
    """Generate all the keys in an S3 bucket."""
    kwargs = {'Bucket': bucket}
    while True:
        resp = client.list_objects_v2(**kwargs)
        if 'Contents' in resp:    #we've got some key in bucket
            for obj in resp['Contents']:
                yield obj['Key']

            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break
        else: #no key -> exit
            break

def get_user_arn(session):
    """
    Return arn of the session user
    """
    mySts = session.client('sts').get_caller_identity()
    myArn = mySts["Arn"]
    return myArn

def create_key_policy(arn):
    """
    Create key policy wich allows everyone to use the key to encrypt and only current user to decrypt
    """
    #TODO: Enable the world to use it for encryption
    policy = '''
    {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "Allowing Access",
            "Effect": "Allow",
            "Principal": {"AWS": [
                "'''+arn+'''"
            ]},
            "Action": "kms:*",
            "Resource": "*"
        }]
    }'''
    return policy