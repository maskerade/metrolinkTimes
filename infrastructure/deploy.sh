#!/bin/bash

# Metrolink Times AWS CDK Deployment Script

set -e

echo "🚀 Deploying Metrolink Times to AWS Lambda..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Install CDK dependencies
echo "📦 Installing CDK dependencies..."
npm install

# Build TypeScript
echo "🔨 Building CDK project..."
npm run build

# Bootstrap CDK (if not already done)
echo "🏗️  Bootstrapping CDK (if needed)..."
npx cdk bootstrap

# Deploy the stack
echo "🚀 Deploying stack..."
npx cdk deploy --require-approval never

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update the TfGM API key in SSM Parameter Store:"
echo "   aws ssm put-parameter --name '/metrolink-times/tfgm-api-key' --value 'YOUR_TFGM_API_KEY' --type 'SecureString' --overwrite"
echo ""
echo "2. Test your API using the URL shown above"
echo ""
echo "3. View logs with:"
echo "   aws logs tail /aws/lambda/MetrolinkTimesStack-MetrolinkTimesApi --follow"