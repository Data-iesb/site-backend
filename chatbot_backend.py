#!/usr/bin/env python3
"""
Amazon Q Business Chatbot Backend
Integrates with Amazon Q Business to provide knowledge-based responses
"""

import os
import json
import boto3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

class QBusinessChatbot:
    def __init__(self):
        """Initialize the Amazon Q Business client"""
        try:
            # Initialize AWS session
            self.session = boto3.Session()
            self.q_business_client = self.session.client('qbusiness')
            
            # Configuration - these should be set as environment variables
            self.application_id = os.getenv('Q_BUSINESS_APPLICATION_ID')
            self.user_id = os.getenv('Q_BUSINESS_USER_ID', 'default-user')
            
            if not self.application_id:
                logger.warning("Q_BUSINESS_APPLICATION_ID not set. Please configure your environment.")
                
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your AWS credentials.")
            self.q_business_client = None
        except Exception as e:
            logger.error(f"Error initializing Q Business client: {str(e)}")
            self.q_business_client = None

    def chat_with_q_business(self, message, conversation_id=None):
        """
        Send a message to Amazon Q Business and get a response
        
        Args:
            message (str): User's message
            conversation_id (str): Optional conversation ID for context
            
        Returns:
            dict: Response from Q Business or error message
        """
        if not self.q_business_client or not self.application_id:
            return {
                'error': 'Amazon Q Business not properly configured',
                'message': 'Please check your AWS credentials and Q Business application ID'
            }
        
        try:
            # Prepare the chat request
            chat_params = {
                'applicationId': self.application_id,
                'userId': self.user_id,
                'userMessage': message
            }
            
            # Add conversation ID if provided for context
            if conversation_id:
                chat_params['conversationId'] = conversation_id
            
            # Call Amazon Q Business
            response = self.q_business_client.chat_sync(**chat_params)
            
            # Extract the response
            return {
                'success': True,
                'response': response.get('systemMessage', 'No response received'),
                'conversationId': response.get('conversationId'),
                'sourceAttributions': response.get('sourceAttributions', [])
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Client Error: {error_code} - {error_message}")
            
            return {
                'error': f'AWS Error: {error_code}',
                'message': error_message
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'error': 'Unexpected error occurred',
                'message': str(e)
            }

# Initialize the chatbot
chatbot = QBusinessChatbot()

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Amazon Q Business Chatbot',
        'configured': bool(chatbot.q_business_client and chatbot.application_id)
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Expects JSON: {"message": "user message", "conversationId": "optional"}
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        conversation_id = data.get('conversationId')
        
        if not user_message:
            return jsonify({
                'error': 'Empty message',
                'message': 'Please provide a non-empty message'
            }), 400
        
        # Get response from Q Business
        response = chatbot.chat_with_q_business(user_message, conversation_id)
        
        if 'error' in response:
            return jsonify(response), 500
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/widget')
def chatbot_widget():
    """Serve the chatbot widget HTML"""
    widget_html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Q Business Chatbot Widget</title>
    <style>
        .chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            z-index: 1000;
        }
        
        .chatbot-header {
            background: #232F3E;
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chatbot-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            max-height: 350px;
        }
        
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
        }
        
        .user-message {
            background: #007DBA;
            color: white;
            margin-left: auto;
        }
        
        .bot-message {
            background: #f1f1f1;
            color: #333;
        }
        
        .chatbot-input {
            display: flex;
            padding: 15px;
            border-top: 1px solid #eee;
        }
        
        .chatbot-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-right: 10px;
        }
        
        .chatbot-input button {
            background: #007DBA;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .chatbot-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #232F3E;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 24px;
            z-index: 1001;
        }
        
        .loading {
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <button class="chatbot-toggle" onclick="toggleChatbot()">💬</button>
    
    <div class="chatbot-container" id="chatbotContainer">
        <div class="chatbot-header">
            <h3>Assistente Q Business</h3>
            <button onclick="toggleChatbot()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
        </div>
        
        <div class="chatbot-messages" id="chatbotMessages">
            <div class="message bot-message">
                Olá! Sou seu assistente baseado no Amazon Q Business. Como posso ajudá-lo com informações sobre nossos parceiros?
            </div>
        </div>
        
        <div class="chatbot-input">
            <input type="text" id="messageInput" placeholder="Digite sua pergunta..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        let conversationId = null;
        
        function toggleChatbot() {
            const container = document.getElementById('chatbotContainer');
            container.style.display = container.style.display === 'none' || container.style.display === '' ? 'flex' : 'none';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show loading
            const messagesContainer = document.getElementById('chatbotMessages');
            messagesContainer.classList.add('loading');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversationId: conversationId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response, 'bot');
                    conversationId = data.conversationId;
                } else {
                    addMessage('Desculpe, ocorreu um erro: ' + (data.message || 'Erro desconhecido'), 'bot');
                }
                
            } catch (error) {
                addMessage('Erro de conexão. Tente novamente.', 'bot');
                console.error('Error:', error);
            } finally {
                messagesContainer.classList.remove('loading');
            }
        }
        
        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('chatbotMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    </script>
</body>
</html>
    """
    return render_template_string(widget_html)

if __name__ == '__main__':
    # Check if running in development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Amazon Q Business Chatbot on port {port}")
    print(f"Debug mode: {debug_mode}")
    print(f"Q Business Application ID: {chatbot.application_id or 'Not configured'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
