#!/usr/bin/env python3
"""
Team Data API - Serves team member data from DynamoDB
"""

import json
import boto3
from flask import Flask, jsonify
from flask_cors import CORS
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

class TeamDataAPI:
    def __init__(self):
        """Initialize DynamoDB client"""
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self.table = self.dynamodb.Table('DataIESB-TeamMembers')
            logger.info("DynamoDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DynamoDB: {str(e)}")
            self.table = None

    def get_team_members(self):
        """Get all team members from DynamoDB"""
        if not self.table:
            return {'error': 'Database not available'}
        
        try:
            response = self.table.scan()
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
            return {'success': True, 'data': processed_items}
            
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            return {'error': 'Database error', 'message': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {'error': 'Server error', 'message': str(e)}

# Initialize API
team_api = TeamDataAPI()

@app.route('/api/team', methods=['GET'])
def get_team():
    """API endpoint to get team members"""
    result = team_api.get_team_members()
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Team Data API'
    })

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5001))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Team Data API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
