---
title: AWS installation
---

You can install authentik to run on AWS with a CloudFormation template.

### Prerequisites

- An AWS account.
- An [AWS Certificate Manager](https://aws.amazon.com/certificate-manager/) certificate. Take note of the ARN of the certificate.

### Installation

Log in to your AWS account and create a CloudFormation stack [with our template](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=authentik&templateURL=https://authentik-cloudformation-templates.s3.amazonaws.com/authentik.ecs.latest.yaml).

Under the **Certificate ARN** input, enter the previously created certificate ARN. You can also configure other settings if needed. You can follow the prompts to create the stack.

This stack will create the following resources:

- AWS SSM secrets for the PostgreSQL user and the authentik secret key
- A VPC for all other resources
- A RDS PostgreSQL Multi-AZ cluster
- An ElastiCache Redis Multi-AZ cluster
- An ECS cluster with two tasks:
    - One for the authentik server
    - One for the authentik worker
- An ALB (Application Load Balancer) pointing to the authentik server ECS task with the configured certificate
- An EFS filesystem mounted on both ECS tasks for media file storage

The stack will output the endpoint of the ALB that to which you can point your DNS records.

### Further customization

If you require further customization, we recommend you install authentik via [Docker Compose](./docker-compose.mdx) or [Kubernetes](./kubernetes.md).
