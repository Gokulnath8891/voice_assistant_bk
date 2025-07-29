#!/usr/bin/env python3
"""
Wake Word Detection Example
Demonstrates how to use the wake word detection module
"""

import time
import requests
from wake_word_detection import VoiceAssistantWithWakeWord, WakeWordDetector


def simple_wake_word_example():
    """
    Simple example using the WakeWordDetector class
    """
    print("🎤 Simple Wake Word Detection Example")
    print("=" * 50)
    
    def on_wake_word(command_text):
        print(f"🎯 Wake word detected! Command: '{command_text}'")
        if command_text:
            print(f"💬 Processing command: {command_text}")
        else:
            print("👂 Ready for your question...")
    
    # Create detector
    detector = WakeWordDetector(
        subscription_key="your_azure_key",  # Will use from .env
        region="your_region",              # Will use from .env
        wake_word="hey buddy",
        callback=on_wake_word
    )
    
    try:
        print("Starting wake word detection...")
        detector.start_listening()
        
        print("💬 Say 'hey buddy' to activate!")
        print("🛑 Press Ctrl+C to stop")
        
        # Keep running
        while detector.is_listening:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        detector.stop_listening()


def full_voice_assistant_example():
    """
    Full voice assistant example with API integration
    """
    print("🤖 Full Voice Assistant Example")
    print("=" * 50)
    
    try:
        # Create voice assistant
        assistant = VoiceAssistantWithWakeWord()
        wake_detector = assistant.start()
        
        print("🎤 Voice Assistant is ready!")
        print("💬 Say 'hey buddy' followed by your question")
        print("   Example: 'hey buddy, how does the airbag work?'")
        print("🛑 Press Ctrl+C to stop")
        
        # Keep running
        while wake_detector.is_listening:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'assistant' in locals():
            assistant.stop()


def api_integration_example():
    """
    Example showing how to integrate with the wake word API endpoints
    """
    print("🌐 Wake Word API Integration Example")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Start wake word detection via API
        print("📡 Starting wake word detection via API...")
        response = requests.post(f"{base_url}/wakeword/start")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print(f"👂 Listening for: '{result['wake_word']}'")
            
            # Monitor status
            for i in range(30):  # Monitor for 30 seconds
                status_response = requests.get(f"{base_url}/wakeword/status")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    
                    if status['recent_detections']:
                        print(f"🎯 Detection found!")
                        for detection in status['recent_detections']:
                            print(f"   Text: '{detection['full_text']}'")
                            print(f"   Command: '{detection['command_text']}'")
                            print(f"   Time: {time.ctime(detection['timestamp'])}")
                        break
                
                time.sleep(1)
                if i % 5 == 0:
                    print(f"⏰ Listening... ({30-i} seconds remaining)")
            
            # Stop detection
            stop_response = requests.post(f"{base_url}/wakeword/stop")
            if stop_response.status_code == 200:
                print("🛑 Wake word detection stopped")
        else:
            print(f"❌ Failed to start: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_wake_word_pipeline():
    """
    Test the complete wake word to response pipeline
    """
    print("🔄 Complete Wake Word Pipeline Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test commands
    test_commands = [
        "how does the airbag work",
        "what is fuel injection",
        "explain engine cooling system"
    ]
    
    try:
        for command in test_commands:
            print(f"\n🧪 Testing command: '{command}'")
            
            # Process command through wake word pipeline
            response = requests.post(
                f"{base_url}/wakeword/process",
                json={"command_text": command}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Summary: {result['summary'][:100]}...")
                print(f"📄 Found {len(result['relevant_chunks'])} relevant chunks")
            else:
                print(f"❌ Failed: {response.text}")
                
            time.sleep(1)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")


def interactive_wake_word_demo():
    """
    Interactive demo for testing wake word detection
    """
    print("🎮 Interactive Wake Word Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    while True:
        print("\nChoose an option:")
        print("1. Start wake word detection")
        print("2. Check status")
        print("3. Stop wake word detection")
        print("4. Test command processing")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        try:
            if choice == '1':
                response = requests.post(f"{base_url}/wakeword/start")
                result = response.json()
                print(f"📡 {result['message']}")
                
            elif choice == '2':
                response = requests.get(f"{base_url}/wakeword/status")
                result = response.json()
                print(f"👂 Listening: {result['listening']}")
                print(f"🔤 Wake word: '{result['wake_word']}'")
                print(f"📊 Detections: {result['detection_count']}")
                
                if result['recent_detections']:
                    print("Recent detections:")
                    for detection in result['recent_detections'][-3:]:
                        print(f"  - '{detection['full_text']}' at {time.ctime(detection['timestamp'])}")
                
            elif choice == '3':
                response = requests.post(f"{base_url}/wakeword/stop")
                result = response.json()
                print(f"🛑 {result['message']}")
                
            elif choice == '4':
                command = input("Enter test command: ").strip()
                if command:
                    response = requests.post(
                        f"{base_url}/wakeword/process",
                        json={"command_text": command}
                    )
                    result = response.json()
                    print(f"🤖 Response: {result['summary']}")
                
            elif choice == '5':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Make sure Django server is running.")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("Wake Word Detection Examples")
    print("=" * 50)
    print("1. Simple wake word detection")
    print("2. Full voice assistant")
    print("3. API integration example")
    print("4. Pipeline test")
    print("5. Interactive demo")
    
    choice = input("\nChoose example (1-5): ").strip()
    
    if choice == '1':
        simple_wake_word_example()
    elif choice == '2':
        full_voice_assistant_example()
    elif choice == '3':
        api_integration_example()
    elif choice == '4':
        test_wake_word_pipeline()
    elif choice == '5':
        interactive_wake_word_demo()
    else:
        print("Invalid choice")