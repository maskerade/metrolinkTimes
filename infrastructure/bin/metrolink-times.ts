#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MetrolinkTimesStack } from '../lib/metrolink-times-stack';
import { AwsSolutionsChecks } from 'cdk-nag';

const app = new cdk.App();

// Create the main stack
const stack = new MetrolinkTimesStack(app, 'MetrolinkTimesStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'FastAPI-based Metrolink Times API deployed on AWS Lambda with API Gateway',
});

// Apply CDK Nag for security best practices
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));