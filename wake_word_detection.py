#!/usr/bin/env python3
"""
Wake Word Detection Module using Azure Speech SDK
Detects "hey buddy" wake word and triggers speech recognition
"""

import os
import time
import threading
import logging
from typing import Callable, Optional
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detection using Azure Speech SDK keyword recognition
    """
    
    def __init__(self, 
                 subscription_key: str, 
                 region: str,
                 wake_word: str = "hey buddy",
                 callback: Optional[Callable] = None):
        """
        Initialize wake word detector
        
        Args:
            subscription_key: Azure Speech Service subscription key
            region: Azure Speech Service region
            wake_word: Wake word phrase to detect
            callback: Function to call when wake word is detected
        """
        self.subscription_key = subscription_key
        self.region = region
        self.wake_word = wake_word.lower()
        self.callback = callback
        
        # Detection state
        self.is_listening = False
        self._stop_event = threading.Event()
        self._detection_thread = None
        
        # Azure Speech SDK objects
        self.speech_config = None
        self.audio_config = None
        self.keyword_recognizer = None
        
        self._initialize_speech_config()
    
    def _initialize_speech_config(self):
        """Initialize Azure Speech SDK configuration"""
        try:
            # Configure speech service
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            
            # Set recognition language
            self.speech_config.speech_recognition_language = "en-US"
            
            # Configure audio input from microphone
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            
            logger.info("Azure Speech SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech SDK: {e}")
            raise
    
    def _create_keyword_model(self):
        """
        Create keyword model for wake word detection
        Note: For production, you should create a proper keyword model file (.table)
        For now, we'll use continuous recognition with keyword filtering
        """
        try:
            # Create speech recognizer for continuous recognition
            self.keyword_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )
            
            logger.info(f"Keyword recognizer created for wake word: '{self.wake_word}'")
            
        except Exception as e:
            logger.error(f"Failed to create keyword model: {e}")
            raise
    
    def _on_recognition_result(self, evt):
        """
        Handle recognition results and check for wake word
        
        Args:
            evt: Recognition event from Azure Speech SDK
        """
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = evt.result.text.lower().strip()
            logger.debug(f"Recognized: '{recognized_text}'")
            
            # Check if wake word is detected
            if self.wake_word in recognized_text:
                logger.info(f"🎤 Wake word '{self.wake_word}' detected!")
                
                # Extract command after wake word if any
                wake_word_index = recognized_text.find(self.wake_word)
                command_text = recognized_text[wake_word_index + len(self.wake_word):].strip()
                
                # Trigger callback
                if self.callback:
                    try:
                        if command_text:
                            self.callback(command_text)
                        else:
                            self.callback("")
                    except Exception as e:
                        logger.error(f"Error in wake word callback: {e}")
                
                # Optional: Stop listening after detection (for single-shot mode)
                # self.stop_listening()
        
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logger.debug("No speech could be recognized")
    
    def _on_recognition_canceled(self, evt):
        """Handle recognition cancellation"""
        cancellation_details = evt.result.cancellation_details
        logger.warning(f"Speech recognition canceled: {cancellation_details.reason}")
        
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            logger.error(f"Error details: {cancellation_details.error_details}")
    
    def _detection_loop(self):
        """Main detection loop running in separate thread"""
        try:
            # Create keyword recognizer
            self._create_keyword_model()
            
            # Connect event handlers
            self.keyword_recognizer.recognized.connect(self._on_recognition_result)
            self.keyword_recognizer.canceled.connect(self._on_recognition_canceled)
            
            # Start continuous recognition
            logger.info("🎧 Starting wake word detection...")
            self.keyword_recognizer.start_continuous_recognition()
            
            # Keep detection running until stop event
            while not self._stop_event.is_set():
                time.sleep(0.1)
            
            # Stop recognition
            self.keyword_recognizer.stop_continuous_recognition()
            logger.info("Wake word detection stopped")
            
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
        finally:
            self.is_listening = False
    
    def start_listening(self):
        """Start wake word detection in background thread"""
        if self.is_listening:
            logger.warning("Wake word detection is already running")
            return
        
        if not self.subscription_key or not self.region:
            raise ValueError("Azure Speech Service credentials not configured")
        
        self.is_listening = True
        self._stop_event.clear()
        
        # Start detection in separate thread
        self._detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True,
            name="WakeWordDetector"
        )
        self._detection_thread.start()
        
        logger.info(f"🎤 Wake word detection started. Say '{self.wake_word}' to activate!")
    
    def stop_listening(self):
        """Stop wake word detection"""
        if not self.is_listening:
            logger.warning("Wake word detection is not running")
            return
        
        logger.info("Stopping wake word detection...")
        self._stop_event.set()
        
        # Wait for detection thread to finish
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=5.0)
        
        self.is_listening = False
        logger.info("Wake word detection stopped")
    
    def set_callback(self, callback: Callable):
        """Set callback function for wake word detection"""
        self.callback = callback
    
    def __enter__(self):
        """Context manager entry"""
        self.start_listening()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_listening()


class VoiceAssistantWithWakeWord:
    """
    Complete voice assistant with wake word detection
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.wake_word_detector = None
        
        # Get Azure credentials
        self.azure_key = os.getenv('AZURE_SPEECH_KEY')
        self.azure_region = os.getenv('AZURE_SPEECH_REGION')
        
        if not self.azure_key or not self.azure_region:
            raise ValueError("Azure Speech Service credentials not found in environment variables")
    
    def _on_wake_word_detected(self, command_text: str = ""):
        """
        Callback function when wake word is detected
        
        Args:
            command_text: Any text spoken after the wake word
        """
        logger.info(f"🎯 Wake word detected! Command: '{command_text}'")
        
        try:
            if command_text:
                # If there's a command after wake word, process it directly
                self._process_voice_command(command_text)
            else:
                # If no command, start listening for full speech
                logger.info("👂 Listening for your question...")
                self._start_full_speech_recognition()
                
        except Exception as e:
            logger.error(f"Error processing wake word: {e}")
    
    def _process_voice_command(self, text: str):
        """
        Process voice command using the semantic search API
        
        Args:
            text: The recognized text to process
        """
        try:
            import requests
            
            # Send to semantic search API
            response = requests.post(
                f"{self.base_url}/search/query",
                json={"query": text},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('summary', 'No answer found')
                
                logger.info(f"📝 Answer: {summary}")
                
                # Convert answer to speech
                self._text_to_speech(summary)
            else:
                logger.error(f"Search API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
    
    def _start_full_speech_recognition(self):
        """Start full speech recognition after wake word"""
        try:
            # Create speech recognizer for full recognition
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_key,
                region=self.azure_region
            )
            speech_config.speech_recognition_language = "en-US"
            
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            logger.info("🎤 Listening... (speak your question)")
            
            # Recognize speech with timeout
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"🗣️ You said: '{result.text}'")
                self._process_voice_command(result.text)
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech recognized")
            else:
                logger.error(f"Speech recognition failed: {result.reason}")
                
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
    
    def _text_to_speech(self, text: str):
        """
        Convert text to speech using the TTS API
        
        Args:
            text: Text to convert to speech
        """
        try:
            import requests
            
            response = requests.post(
                f"{self.base_url}/tts/synthesize",
                json={"text": text},
                timeout=10
            )
            
            if response.status_code == 200:
                # Save and play audio (you can implement audio playback here)
                logger.info("🔊 Playing audio response...")
                
                # For now, we'll just log that TTS was successful
                # In a real implementation, you'd play the audio
                logger.info(f"TTS response generated ({len(response.content)} bytes)")
            else:
                logger.error(f"TTS API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def start(self):
        """Start the voice assistant with wake word detection"""
        try:
            # Create wake word detector
            self.wake_word_detector = WakeWordDetector(
                subscription_key=self.azure_key,
                region=self.azure_region,
                wake_word="hey buddy",
                callback=self._on_wake_word_detected
            )
            
            # Start listening for wake word
            self.wake_word_detector.start_listening()
            
            return self.wake_word_detector
            
        except Exception as e:
            logger.error(f"Failed to start voice assistant: {e}")
            raise
    
    def stop(self):
        """Stop the voice assistant"""
        if self.wake_word_detector:
            self.wake_word_detector.stop_listening()


def main():
    """Main function for testing wake word detection"""
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print('\n👋 Shutting down wake word detection...')
        assistant.stop()
        sys.exit(0)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create and start voice assistant
        assistant = VoiceAssistantWithWakeWord()
        wake_detector = assistant.start()
        
        print("🎤 Voice Assistant is ready!")
        print("💬 Say 'hey buddy' followed by your question")
        print("🛑 Press Ctrl+C to stop")
        
        # Keep running until interrupted
        while wake_detector.is_listening:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print('\n👋 Goodbye!')
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if 'assistant' in locals():
            assistant.stop()


if __name__ == "__main__":
    main()