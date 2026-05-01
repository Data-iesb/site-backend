import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda function to serve team data from DynamoDB
    """
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('DataIESB-TeamMembers')
        
        # Scan the table
        response = table.scan()
        items = response.get('Items', [])
        
        # Process items to ensure consistent structure
        processed_items = []
        for item in items:
            processed_item = {
                'id': item.get('email', ''),
                'name': item.get('name', ''),
                'email': item.get('email', ''),
                'role': item.get('role', ''),
                'category': item.get('category', 'Outros'),
                'active': True
            }
            processed_items.append(processed_item)
        
        logger.info(f"Retrieved {len(processed_items)} team members")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': processed_items
            })
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Database error',
                'message': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Server error',
                'message': str(e)
            })
        }
