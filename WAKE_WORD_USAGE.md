# Wake Word Detection with "Hey Buddy"

## Overview

The wake word detection system uses Azure Speech SDK to continuously listen for the phrase "hey buddy" and automatically trigger the voice assistant pipeline.

## Features

- ✅ **Continuous Listening**: Always-on wake word detection
- ✅ **Azure Speech SDK**: High-accuracy speech recognition
- ✅ **Command Processing**: Extracts commands after wake word
- ✅ **API Integration**: RESTful endpoints for control
- ✅ **Real-time Streaming**: Server-Sent Events for live updates
- ✅ **Full Pipeline**: Wake word → Speech → Search → TTS

---

## Quick Start

### 1. Basic Usage (Python Script)

```python
from wake_word_detection import VoiceAssistantWithWakeWord

# Create and start voice assistant
assistant = VoiceAssistantWithWakeWord()
wake_detector = assistant.start()

print("🎤 Say 'hey buddy' followed by your question!")

# Keep running
try:
    while wake_detector.is_listening:
        time.sleep(1)
except KeyboardInterrupt:
    assistant.stop()
```

### 2. Command Line Usage

```bash
# Run the wake word detection script
python wake_word_detection.py

# Or run examples
python wake_word_example.py
```

### 3. API Usage

```bash
# Start wake word detection
curl -X POST http://localhost:8000/api/v1/wakeword/start

# Check status
curl http://localhost:8000/api/v1/wakeword/status

# Stop detection
curl -X POST http://localhost:8000/api/v1/wakeword/stop
```

---

## API Endpoints

### Start Wake Word Detection
**POST** `/api/v1/wakeword/start`

Starts continuous wake word detection for "hey buddy".

```json
// Response
{
  "status": "success",
  "message": "Wake word detection started",
  "wake_word": "hey buddy",
  "listening": true
}
```

### Stop Wake Word Detection
**POST** `/api/v1/wakeword/stop`

Stops wake word detection.

```json
// Response
{
  "status": "success",
  "message": "Wake word detection stopped",
  "listening": false
}
```

### Get Status
**GET** `/api/v1/wakeword/status`

Get current status and recent detections.

```json
// Response
{
  "status": "success",
  "listening": true,
  "wake_word": "hey buddy",
  "detection_count": 3,
  "recent_detections": [
    {
      "timestamp": 1703123456.789,
      "wake_word_detected": true,
      "full_text": "Hey buddy, how does the airbag work?",
      "command_text": "how does the airbag work",
      "confidence": 0.95
    }
  ]
}
```

### Stream Detections
**GET** `/api/v1/wakeword/stream`

Real-time stream of wake word detections using Server-Sent Events.

```javascript
// JavaScript example
const eventSource = new EventSource('/api/v1/wakeword/stream');

eventSource.onmessage = function(event) {
  const detection = JSON.parse(event.data);
  console.log('Wake word detected:', detection);
};
```

### Process Command
**POST** `/api/v1/wakeword/process`

Process a wake word command through the complete pipeline.

```json
// Request
{
  "command_text": "how does the airbag work"
}

// Response
{
  "status": "success",
  "command_text": "how does the airbag work",
  "summary": "• Airbags are safety devices...",
  "relevant_chunks": [...],
  "wake_word_triggered": true
}
```

---

## Usage Patterns

### 1. Always-On Voice Assistant

```python
from wake_word_detection import VoiceAssistantWithWakeWord
import signal
import sys

def signal_handler(sig, frame):
    assistant.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

assistant = VoiceAssistantWithWakeWord()
assistant.start()

print("🎤 Voice assistant is ready!")
print("💬 Say 'hey buddy' + your question")

# Keep running until interrupted
while True:
    time.sleep(1)
```

### 2. Web Integration

```javascript
// Start wake word detection
async function startWakeWord() {
  const response = await fetch('/api/v1/wakeword/start', {
    method: 'POST'
  });
  const result = await response.json();
  console.log(result.message);
}

// Monitor detections
const eventSource = new EventSource('/api/v1/wakeword/stream');
eventSource.onmessage = function(event) {
  const detection = JSON.parse(event.data);
  
  if (detection.wake_word_detected) {
    console.log('Command:', detection.command_text);
    // Process the command or update UI
  }
};

// Start detection
startWakeWord();
```

### 3. Custom Callback Processing

```python
from wake_word_detection import WakeWordDetector

def my_wake_word_handler(command_text):
    print(f"🎯 Detected command: {command_text}")
    
    # Custom processing logic
    if "weather" in command_text:
        get_weather_info()
    elif "music" in command_text:
        play_music()
    else:
        # Use default voice assistant
        process_with_ai(command_text)

detector = WakeWordDetector(
    subscription_key=os.getenv('AZURE_SPEECH_KEY'),
    region=os.getenv('AZURE_SPEECH_REGION'),
    wake_word="hey buddy",
    callback=my_wake_word_handler
)

detector.start_listening()
```

---

## Advanced Configuration

### Environment Variables

```bash
# Required
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus2

# Optional
WAKE_WORD_PHRASE="hey buddy"  # Default wake word
WAKE_WORD_CONFIDENCE=0.7      # Minimum confidence threshold
```

### Custom Wake Word

```python
# Change wake word from "hey buddy" to something else
detector = WakeWordDetector(
    subscription_key=os.getenv('AZURE_SPEECH_KEY'),
    region=os.getenv('AZURE_SPEECH_REGION'),
    wake_word="computer",  # Custom wake word
    callback=my_callback
)
```

### Threading and Performance

```python
import threading

class ThreadedWakeWordApp:
    def __init__(self):
        self.detector = None
        self.processing_thread = None
    
    def start_detection(self):
        self.detector = WakeWordDetector(
            subscription_key=os.getenv('AZURE_SPEECH_KEY'),
            region=os.getenv('AZURE_SPEECH_REGION'),
            wake_word="hey buddy",
            callback=self._process_command
        )
        self.detector.start_listening()
    
    def _process_command(self, command_text):
        # Process in separate thread to avoid blocking detection
        self.processing_thread = threading.Thread(
            target=self._handle_command,
            args=(command_text,),
            daemon=True
        )
        self.processing_thread.start()
    
    def _handle_command(self, command_text):
        # Heavy processing here
        pass
```

---

## Error Handling

### Common Issues

1. **Azure credentials not configured**
```python
try:
    detector = WakeWordDetector(...)
except ValueError as e:
    print("❌ Check AZURE_SPEECH_KEY and AZURE_SPEECH_REGION")
```

2. **Microphone access denied**
```python
try:
    detector.start_listening()
except Exception as e:
    print("❌ Check microphone permissions")
```

3. **Network connectivity issues**
```python
# Add retry logic
import time

def start_with_retry(detector, max_retries=3):
    for attempt in range(max_retries):
        try:
            detector.start_listening()
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    return False
```

---

## Testing

### Unit Tests

```bash
# Test wake word detection
python -m pytest wake_word/tests/

# Test API endpoints
python -m pytest wake_word/tests/test_api.py
```

### Manual Testing

```python
# Run interactive demo
python wake_word_example.py

# Choose option 5 for interactive testing
```

### API Testing with curl

```bash
# Start detection
curl -X POST http://localhost:8000/api/v1/wakeword/start

# Test command processing
curl -X POST http://localhost:8000/api/v1/wakeword/process \
  -H "Content-Type: application/json" \
  -d '{"command_text": "test command"}'

# Check status
curl http://localhost:8000/api/v1/wakeword/status

# Stop detection
curl -X POST http://localhost:8000/api/v1/wakeword/stop
```

---

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
import requests

st.title("🎤 Wake Word Voice Assistant")

# Control buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("🎧 Start Wake Word"):
        response = requests.post('http://localhost:8000/api/v1/wakeword/start')
        if response.status_code == 200:
            st.success("Wake word detection started!")
        else:
            st.error("Failed to start wake word detection")

with col2:
    if st.button("🛑 Stop Wake Word"):
        response = requests.post('http://localhost:8000/api/v1/wakeword/stop')
        if response.status_code == 200:
            st.success("Wake word detection stopped!")

# Status display
if st.button("📊 Check Status"):
    response = requests.get('http://localhost:8000/api/v1/wakeword/status')
    if response.status_code == 200:
        status = response.json()
        st.json(status)
```

### React Integration

```javascript
import React, { useState, useEffect } from 'react';

function WakeWordController() {
  const [isListening, setIsListening] = useState(false);
  const [detections, setDetections] = useState([]);

  const startWakeWord = async () => {
    try {
      const response = await fetch('/api/v1/wakeword/start', {
        method: 'POST'
      });
      const result = await response.json();
      setIsListening(true);
      console.log(result.message);
    } catch (error) {
      console.error('Failed to start wake word:', error);
    }
  };

  const stopWakeWord = async () => {
    try {
      const response = await fetch('/api/v1/wakeword/stop', {
        method: 'POST'
      });
      setIsListening(false);
    } catch (error) {
      console.error('Failed to stop wake word:', error);
    }
  };

  useEffect(() => {
    if (isListening) {
      const eventSource = new EventSource('/api/v1/wakeword/stream');
      
      eventSource.onmessage = (event) => {
        const detection = JSON.parse(event.data);
        if (detection.wake_word_detected) {
          setDetections(prev => [...prev, detection]);
        }
      };

      return () => eventSource.close();
    }
  }, [isListening]);

  return (
    <div>
      <h2>🎤 Wake Word Detection</h2>
      
      <div>
        <button onClick={startWakeWord} disabled={isListening}>
          Start Listening
        </button>
        <button onClick={stopWakeWord} disabled={!isListening}>
          Stop Listening
        </button>
      </div>

      <div>
        <p>Status: {isListening ? '🎧 Listening' : '🔇 Stopped'}</p>
        <p>Wake Word: "hey buddy"</p>
      </div>

      <div>
        <h3>Recent Detections:</h3>
        {detections.map((detection, index) => (
          <div key={index}>
            <p><strong>Command:</strong> {detection.command_text}</p>
            <p><strong>Time:</strong> {new Date(detection.timestamp * 1000).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default WakeWordController;
```

---

## Best Practices

1. **Resource Management**
   - Always stop detection when not needed
   - Use context managers for automatic cleanup
   - Handle microphone access gracefully

2. **Performance**
   - Process commands in separate threads
   - Implement timeout for long-running operations
   - Use appropriate confidence thresholds

3. **Error Handling**
   - Implement retry logic for network issues
   - Handle Azure service outages gracefully
   - Provide user feedback for errors

4. **Security**
   - Store Azure credentials securely
   - Validate command input
   - Implement rate limiting if needed

5. **User Experience**
   - Provide clear status indicators
   - Give audio/visual feedback for wake word detection
   - Handle false positives gracefully

---

## Troubleshooting

### Issue: Wake word not detected

**Solution:**
- Check microphone permissions
- Verify Azure credentials
- Test with clear pronunciation
- Adjust microphone sensitivity

### Issue: High false positive rate

**Solution:**
- Increase confidence threshold
- Use more specific wake word phrases
- Implement noise filtering
- Train custom wake word model

### Issue: High latency

**Solution:**
- Use dedicated microphone thread
- Optimize Azure region selection
- Implement local preprocessing
- Cache frequently used responses

---

## Production Deployment

### Docker Configuration

```dockerfile
# Add to existing Dockerfile
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Ensure microphone access in container
VOLUME ["/dev/snd"]
```

### Environment Setup

```bash
# Production environment variables
AZURE_SPEECH_KEY=prod_key_here
AZURE_SPEECH_REGION=eastus2
WAKE_WORD_PHRASE="hey assistant"
LOG_LEVEL=INFO
```

### Monitoring

```python
import logging
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Monitor wake word detection health
        pass
```

This completes your wake word detection system with "hey buddy" trigger phrase! 🎤