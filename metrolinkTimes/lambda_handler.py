"""
AWS Lambda handler for the Metrolink Times FastAPI application.
Uses Mangum to adapt FastAPI for Lambda execution.
"""

import json
import logging
import os

import boto3
from mangum import Mangum

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_tfgm_api_key():
    """Load TfGM API key from SSM Parameter Store"""
    try:
        param_name = os.environ.get('TFG_API_KEY_PARAM', '/metrolink-times/tfgm-api-key')
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to load TfGM API key from SSM: {e}")
        return None

def create_lambda_config():
    """Create configuration for Lambda environment"""
    tfgm_api_key = load_tfgm_api_key()

    if not tfgm_api_key or tfgm_api_key == 'PLACEHOLDER_VALUE':
        logger.warning("TfGM API key not configured. API will not work properly.")
        tfgm_api_key = None

    # Create a temporary config file for the Lambda environment
    config = {
        "Ocp-Apim-Subscription-Key": tfgm_api_key,
        "Access-Control-Allow-Origin": "*",
        "polling_enabled": False  # Force on-demand mode in Lambda
    }

    # Write config to /tmp (only writable directory in Lambda)
    config_path = "/tmp/metrolinkTimes.conf"
    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger.info(f"Created Lambda config at {config_path}")
    return config_path

# Initialize the FastAPI app
try:
    # Set up configuration for Lambda
    create_lambda_config()

    # Import the FastAPI app
    from metrolinkTimes.api import app

    # Create the Mangum handler
    handler = Mangum(app, lifespan="off")

    logger.info("Lambda handler initialized successfully")

except Exception as e:
    logger.error(f"Failed to initialize Lambda handler: {e}")
    raise

def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        logger.info(f"Processing request: {event.get('httpMethod', 'UNKNOWN')} {event.get('path', 'UNKNOWN')}")

        # Use Mangum to handle the request
        response = handler(event, context)

        logger.info(f"Request processed successfully: {response.get('statusCode', 'UNKNOWN')}")
        return response

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
