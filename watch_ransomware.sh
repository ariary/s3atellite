#!/bin/bash

OBJECT=$(aws s3api list-objects --bucket $1 --query 'Contents[0].Key')

# echo  ${OBJETCS[0]}
OBJECT=$(echo $OBJECT|cut -d '"' -f 2)
watch -d -n 5 aws s3api head-object --bucket $1 --key $OBJECT 