#!/bin/bash

# Config Rule 생성 (SSH 0.0.0.0/0 인바운드 탐지, 태그 스코프)
cat <<RULE > sg-config-rule.json
{
  "ConfigRuleName": "cnasg-sg-no-public-ssh",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "INCOMING_SSH_DISABLED"
  },
  "Scope": {
    "TagKey": "Lab",
    "TagValue": "cnasg-16"
  }
}
RULE

aws configservice put-config-rule \
  --config-rule file://sg-config-rule.json

echo "Config Rule 생성 완료"

# Remediation 연결 
cat <<REMEDIATION > sg-remediation.json
[
  {
    "ConfigRuleName": "cnasg-sg-no-public-ssh",
    "TargetType": "SSM_DOCUMENT",
    "TargetId": "AWS-DisablePublicAccessForSecurityGroup",
    "Parameters": {
      "GroupId": {
        "ResourceValue": {
          "Value": "RESOURCE_ID"
        }
      },
      "AutomationAssumeRole": {
        "StaticValue": {
          "Values": ["${REMEDIATION_ROLE_ARN}"]
        }
      }
    },
    "Automatic": true,
    "MaximumAutomaticAttempts": 3,
    "RetryAttemptSeconds": 60
  }
]
REMEDIATION

aws configservice put-remediation-configurations \
  --remediation-configurations file://sg-remediation.json

echo "Remediation 연결 완료"
