#!/bin/bash

VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=cnasg-VPC" \
  --query 'Vpcs[0].VpcId' \
  --output text)

# 정상 보안그룹 생성 (COMPLIANT 대상)
aws ec2 create-security-group \
  --group-name cnasg-normal-sg \
  --description "Normal SG for Config test" \
  --vpc-id ${VPC_ID} \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Lab,Value=cnasg-16}]"

NORMAL_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=cnasg-normal-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id ${NORMAL_SG_ID} \
  --protocol tcp --port 22 --cidr 192.168.0.0/16

# 취약 보안그룹 생성 (NON_COMPLIANT 대상)
aws ec2 create-security-group \
  --group-name cnasg-vulnerable-sg \
  --description "Vulnerable SG for Config test" \
  --vpc-id ${VPC_ID} \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Lab,Value=cnasg-16}]"

VULN_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=cnasg-vulnerable-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id ${VULN_SG_ID} \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

echo "NORMAL_SG_ID: ${NORMAL_SG_ID}"
echo "VULN_SG_ID: ${VULN_SG_ID}"
echo "Done."
