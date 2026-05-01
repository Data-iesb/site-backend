#!/usr/bin/env python3
"""
Test script for Amazon Q Business Chatbot
Tests the backend functionality and AWS connectivity
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def load_environment():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env file")
    else:
        print("⚠️  No .env file found")

def test_aws_credentials():
    """Test AWS credentials and connectivity"""
    print("\n🔐 Testing AWS Credentials...")
    
    try:
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ AWS credentials valid")
        print(f"   Account: {identity.get('Account')}")
        print(f"   User/Role: {identity.get('Arn')}")
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print("   Run 'aws configure' to set up credentials")
        return False
    except Exception as e:
        print(f"❌ AWS error: {str(e)}")
        return False

def test_qbusiness_config():
    """Test Q Business configuration"""
    print("\n📋 Testing Q Business Configuration...")
    
    app_id = os.getenv('Q_BUSINESS_APPLICATION_ID')
    user_id = os.getenv('Q_BUSINESS_USER_ID', 'default-user')
    
    if not app_id or app_id == 'your-q-business-application-id-here':
        print("❌ Q Business Application ID not configured")
        print("   Please set Q_BUSINESS_APPLICATION_ID in .env file")
        return False
    
    print(f"✅ Application ID: {app_id}")
    print(f"✅ User ID: {user_id}")
    
    # Test Q Business connectivity
    try:
        session = boto3.Session()
        qbusiness = session.client('qbusiness')
        
        # Try to get application info (this will fail if app doesn't exist)
        # Note: There's no direct "describe application" API, so we'll try a chat request
        print("🔍 Testing Q Business connectivity...")
        
        response = qbusiness.chat_sync(
            applicationId=app_id,
            userId=user_id,
            userMessage="Hello, this is a test message."
        )
        
        print("✅ Q Business connectivity successful")
        print(f"   Response received: {len(response.get('systemMessage', ''))} characters")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Q Business application not found: {app_id}")
            print("   Please check your Application ID")
        elif error_code == 'AccessDeniedException':
            print("❌ Access denied to Q Business")
            print("   Please check your AWS permissions")
        else:
            print(f"❌ Q Business error: {error_code} - {error_message}")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_backend_server():
    """Test if the backend server is running"""
    print("\n🖥️  Testing Backend Server...")
    
    port = os.getenv('PORT', '5000')
    url = f"http://localhost:{port}"
    
    try:
        response = requests.get(f"{url}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Configured: {data.get('configured')}")
            return True
        else:
            print(f"❌ Backend server returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend server at {url}")
        print("   Make sure to run './start-chatbot.sh' first")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {str(e)}")
        return False

def test_chat_functionality():
    """Test the chat functionality"""
    print("\n💬 Testing Chat Functionality...")
    
    port = os.getenv('PORT', '5000')
    url = f"http://localhost:{port}/chat"
    
    test_message = "Hello, can you tell me about the available partners?"
    
    try:
        response = requests.post(
            url,
            json={"message": test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Chat functionality working")
                print(f"   Response: {data.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Chat error: {data.get('message')}")
                return False
        else:
            print(f"❌ Chat request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Chat request timed out")
        print("   This might indicate Q Business is taking too long to respond")
        return False
    except Exception as e:
        print(f"❌ Error testing chat: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Amazon Q Business Chatbot Test Suite")
    print("=" * 50)
    
    load_environment()
    
    tests = [
        ("AWS Credentials", test_aws_credentials),
        ("Q Business Config", test_qbusiness_config),
        ("Backend Server", test_backend_server),
        ("Chat Functionality", test_chat_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your chatbot is ready to use.")
        print("\nNext steps:")
        print("1. Open parceiros.html in your browser")
        print("2. Click the chat widget in the bottom-right corner")
        print("3. Start chatting with your Q Business assistant!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("- Ensure AWS credentials are configured: aws configure")
        print("- Check Q_BUSINESS_APPLICATION_ID in .env file")
        print("- Make sure the backend server is running: ./start-chatbot.sh")
        print("- Verify your Q Business application has data sources configured")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
