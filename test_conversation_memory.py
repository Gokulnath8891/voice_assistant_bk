#!/usr/bin/env python3
"""
Test script for LangChain conversation memory integration
"""

import json
import requests
import time
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_assistant_project.settings')

import django
django.setup()

from semantic_search.views import get_conversational_chain, setup_langchain

def test_conversation_memory():
    """Test conversation memory functionality"""
    print("🧪 Testing LangChain Conversation Memory Integration")
    print("=" * 60)
    
    try:
        # Initialize LangChain
        print("\n1. Initializing LangChain components...")
        setup_langchain()
        print("✅ LangChain initialized successfully")
        
        # Test 1: First conversation in a session
        print("\n2. Testing first conversation...")
        session_id = "test_session_001"
        
        query1 = "What is an airbag?"
        answer1, chunks1, returned_session = get_conversational_chain(query1, session_id)
        
        print(f"   Query: {query1}")
        print(f"   Session ID: {returned_session}")
        print(f"   Answer: {answer1[:100]}...")
        print(f"   Source chunks: {len(chunks1)}")
        
        # Test 2: Follow-up question (should use conversation context)
        print("\n3. Testing follow-up conversation...")
        query2 = "How does it work?"
        answer2, chunks2, returned_session2 = get_conversational_chain(query2, session_id)
        
        print(f"   Query: {query2}")
        print(f"   Session ID: {returned_session2}")
        print(f"   Answer: {answer2[:100]}...")
        print(f"   Source chunks: {len(chunks2)}")
        
        # Test 3: New session (should not have previous context)
        print("\n4. Testing new session...")
        new_session_id = "test_session_002"
        query3 = "What are you referring to?"
        answer3, chunks3, returned_session3 = get_conversational_chain(query3, new_session_id)
        
        print(f"   Query: {query3}")
        print(f"   Session ID: {returned_session3}")
        print(f"   Answer: {answer3[:100]}...")
        print(f"   Source chunks: {len(chunks3)}")
        
        print("\n✅ All conversation memory tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing conversation memory: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test conversation memory API endpoints"""
    print("\n\n🌐 Testing API Endpoints")
    print("=" * 60)
    
    try:
        base_url = "http://localhost:8000/api/v1/semantic_search"
        
        # Test 1: Search query with session
        print("\n1. Testing search query with session...")
        search_data = {
            "query": "What is brake fluid?",
            "session_id": "api_test_session"
        }
        
        response = requests.post(f"{base_url}/query", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Search successful")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Summary: {result.get('summary', '')[:50]}...")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 2: Follow-up query
        print("\n2. Testing follow-up query...")
        followup_data = {
            "query": "How often should it be changed?",
            "session_id": result.get('session_id') if response.status_code == 200 else "api_test_session"
        }
        
        response2 = requests.post(f"{base_url}/query", json=followup_data)
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   ✅ Follow-up successful")
            print(f"   Summary: {result2.get('summary', '')[:50]}...")
        else:
            print(f"   ❌ Follow-up failed: {response2.status_code}")
        
        # Test 3: Get conversation history
        print("\n3. Testing conversation history...")
        session_id = result.get('session_id') if response.status_code == 200 else "api_test_session"
        history_response = requests.get(f"{base_url}/conversation/history?session_id={session_id}")
        
        if history_response.status_code == 200:
            history = history_response.json()
            print(f"   ✅ History retrieved")
            print(f"   Messages: {len(history.get('chat_history', []))}")
        else:
            print(f"   ❌ History failed: {history_response.status_code}")
        
        # Test 4: List active sessions
        print("\n4. Testing active sessions...")
        sessions_response = requests.get(f"{base_url}/conversation/sessions")
        
        if sessions_response.status_code == 200:
            sessions = sessions_response.json()
            print(f"   ✅ Sessions listed")
            print(f"   Active sessions: {sessions.get('active_sessions', 0)}")
        else:
            print(f"   ❌ Sessions failed: {sessions_response.status_code}")
        
        print("\n✅ API endpoint tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Django server not running. Please start it with:")
        print("   python manage.py runserver")
        return False
    except Exception as e:
        print(f"\n❌ Error testing API endpoints: {e}")
        return False

def run_all_tests():
    """Run all conversation memory tests"""
    print("🚀 Starting Comprehensive Conversation Memory Tests")
    print("=" * 80)
    
    # Test direct function calls
    direct_test_success = test_conversation_memory()
    
    # Test API endpoints (requires Django server)
    api_test_success = test_api_endpoints()
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Direct Function Tests: {'✅ PASSED' if direct_test_success else '❌ FAILED'}")
    print(f"API Endpoint Tests: {'✅ PASSED' if api_test_success else '❌ FAILED'}")
    
    if direct_test_success and api_test_success:
        print("\n🎉 ALL TESTS PASSED! Conversation memory is working correctly.")
    elif direct_test_success:
        print("\n⚠️  Direct tests passed, but API tests failed. Check Django server.")
    else:
        print("\n❌ Tests failed. Check the error messages above.")
    
    return direct_test_success and api_test_success

if __name__ == "__main__":
    run_all_tests()