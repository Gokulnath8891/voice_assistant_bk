#!/usr/bin/env python3
"""
Wake Word Testing Script
Direct testing of wake word functionality without Streamlit limitations
"""

import os
import time
import requests
import threading
from wake_word_detection import VoiceAssistantWithWakeWord, WakeWordDetector


def test_wake_word_api_endpoints():
    """Test all wake word API endpoints"""
    print("🧪 Testing Wake Word API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Test 1: Start wake word detection
        print("1️⃣ Testing Start Wake Word Detection...")
        response = requests.post(f"{base_url}/wakeword/start")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result['message']}")
            print(f"   👂 Wake word: '{result['wake_word']}'")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return False
        
        # Test 2: Check status
        print("\n2️⃣ Testing Status Check...")
        time.sleep(1)
        response = requests.get(f"{base_url}/wakeword/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ Listening: {status['listening']}")
            print(f"   📊 Detection count: {status['detection_count']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        
        # Test 3: Process command
        print("\n3️⃣ Testing Command Processing...")
        test_command = "how does the airbag work"
        response = requests.post(
            f"{base_url}/wakeword/process",
            json={"command_text": test_command}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Command processed successfully")
            print(f"   📝 Summary: {result['summary'][:100]}...")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
        
        # Test 4: Stop detection
        print("\n4️⃣ Testing Stop Wake Word Detection...")
        response = requests.post(f"{base_url}/wakeword/stop")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result['message']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running:")
        print("   python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_wake_word_direct():
    """Test wake word detection directly (not through API)"""
    print("\n🎤 Testing Direct Wake Word Detection")
    print("=" * 50)
    
    detection_results = []
    
    def on_wake_word_detected(command_text):
        timestamp = time.time()
        detection_results.append({
            'timestamp': timestamp,
            'command': command_text,
            'time_str': time.ctime(timestamp)
        })
        print(f"🎯 WAKE WORD DETECTED at {time.ctime(timestamp)}")
        print(f"   Command: '{command_text}'")
    
    try:
        # Check environment variables
        azure_key = os.getenv('AZURE_SPEECH_KEY')
        azure_region = os.getenv('AZURE_SPEECH_REGION')
        
        if not azure_key or not azure_region:
            print("❌ Azure Speech credentials not found in environment variables")
            print("   Make sure to set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION")
            return False
        
        print(f"✅ Azure credentials found")
        print(f"   Region: {azure_region}")
        print(f"   Key: {azure_key[:10]}...")
        
        # Create wake word detector
        print("\n🔧 Initializing wake word detector...")
        detector = WakeWordDetector(
            subscription_key=azure_key,
            region=azure_region,
            wake_word="hey buddy",
            callback=on_wake_word_detected
        )
        
        print("✅ Wake word detector initialized")
        print("🎧 Starting detection...")
        print("💬 Say 'hey buddy' followed by a command")
        print("⏰ Will listen for 30 seconds...")
        print("🛑 Press Ctrl+C to stop early")
        
        # Start detection
        detector.start_listening()
        
        # Listen for 30 seconds
        start_time = time.time()
        try:
            while time.time() - start_time < 30 and detector.is_listening:
                time.sleep(1)
                elapsed = int(time.time() - start_time)
                remaining = 30 - elapsed
                
                if elapsed % 5 == 0 and remaining > 0:
                    print(f"⏳ {remaining} seconds remaining...")
        
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        
        # Stop detection
        detector.stop_listening()
        
        # Show results
        print(f"\n📊 Detection Summary:")
        print(f"   Total detections: {len(detection_results)}")
        
        if detection_results:
            print("   Recent detections:")
            for i, result in enumerate(detection_results[-5:], 1):
                print(f"   {i}. '{result['command']}' at {result['time_str']}")
        else:
            print("   ❌ No wake words detected")
            print("   💡 Try speaking louder or closer to microphone")
            print("   💡 Make sure microphone is working")
        
        return len(detection_results) > 0
        
    except Exception as e:
        print(f"❌ Error in direct testing: {e}")
        return False


def test_microphone_access():
    """Test microphone access and audio recording"""
    print("\n🎙️ Testing Microphone Access")
    print("=" * 50)
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Test microphone access
        print("🔧 Testing microphone configuration...")
        
        azure_key = os.getenv('AZURE_SPEECH_KEY')
        azure_region = os.getenv('AZURE_SPEECH_REGION')
        
        if not azure_key or not azure_region:
            print("❌ Azure credentials not found")
            return False
        
        # Create speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region
        )
        speech_config.speech_recognition_language = "en-US"
        
        # Test default microphone
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        print("✅ Speech recognizer created successfully")
        print("🎤 Testing single recognition (say something)...")
        print("⏰ Listening for 5 seconds...")
        
        # Test single recognition
        result = recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"✅ Microphone working! Recognized: '{result.text}'")
            return True
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("⚠️ Microphone working but no speech detected")
            print("💡 Try speaking louder or closer to microphone")
            return True
        else:
            print(f"❌ Recognition failed: {result.reason}")
            if result.reason == speechsdk.ResultReason.Canceled:
                details = result.cancellation_details
                print(f"   Error: {details.reason}")
                if details.error_details:
                    print(f"   Details: {details.error_details}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")
        return False


def test_full_pipeline():
    """Test the complete voice assistant pipeline"""
    print("\n🔄 Testing Full Voice Assistant Pipeline")
    print("=" * 50)
    
    try:
        # Create voice assistant
        print("🤖 Creating voice assistant...")
        assistant = VoiceAssistantWithWakeWord()
        
        print("✅ Voice assistant created")
        print("🎧 Starting wake word detection...")
        
        wake_detector = assistant.start()
        
        print("✅ Wake word detection started")
        print("💬 Say: 'hey buddy, how does the airbag work?'")
        print("⏰ Listening for 45 seconds...")
        print("🛑 Press Ctrl+C to stop")
        
        # Monitor for 45 seconds
        start_time = time.time()
        try:
            while time.time() - start_time < 45 and wake_detector.is_listening:
                time.sleep(1)
                elapsed = int(time.time() - start_time)
                remaining = 45 - elapsed
                
                if elapsed % 10 == 0 and remaining > 0:
                    print(f"⏳ {remaining} seconds remaining...")
        
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        
        # Stop assistant
        assistant.stop()
        print("✅ Voice assistant stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full pipeline test: {e}")
        return False


def main():
    """Main testing function"""
    print("🎤 Wake Word System Testing")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('AZURE_SPEECH_KEY'):
        print("❌ AZURE_SPEECH_KEY not found in environment")
        print("   Please set your Azure Speech Service key")
        return
    
    if not os.getenv('AZURE_SPEECH_REGION'):
        print("❌ AZURE_SPEECH_REGION not found in environment")
        print("   Please set your Azure Speech Service region")
        return
    
    print("Choose test to run:")
    print("1. Test API endpoints (requires Django server)")
    print("2. Test microphone access")
    print("3. Test direct wake word detection")
    print("4. Test full pipeline")
    print("5. Run all tests")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        test_wake_word_api_endpoints()
    elif choice == '2':
        test_microphone_access()
    elif choice == '3':
        test_wake_word_direct()
    elif choice == '4':
        test_full_pipeline()
    elif choice == '5':
        print("🚀 Running all tests...")
        print("\n" + "="*60)
        
        # Test 1: API endpoints
        api_success = test_wake_word_api_endpoints()
        
        # Test 2: Microphone
        mic_success = test_microphone_access()
        
        # Test 3: Direct detection (only if mic works)
        if mic_success:
            direct_success = test_wake_word_direct()
        else:
            direct_success = False
            print("\n⏭️ Skipping direct detection test (microphone issues)")
        
        # Summary
        print("\n" + "="*60)
        print("📊 Test Summary:")
        print(f"   API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
        print(f"   Microphone: {'✅ PASS' if mic_success else '❌ FAIL'}")
        print(f"   Wake Word Detection: {'✅ PASS' if direct_success else '❌ FAIL'}")
        
        if all([api_success, mic_success, direct_success]):
            print("\n🎉 All tests passed! Wake word system is working.")
        else:
            print("\n⚠️ Some tests failed. Check the issues above.")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()