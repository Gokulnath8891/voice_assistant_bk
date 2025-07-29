# Wake Word Testing Guide

## ⚠️ Why Streamlit Wake Word Doesn't Work Properly

The wake word system has limitations when used through Streamlit:

### **Browser Security Restrictions:**
- 🚫 **No Direct Microphone Access**: Browsers restrict continuous microphone access
- 🚫 **JavaScript Limitations**: Embedded JavaScript can't access system-level audio
- 🚫 **CORS Issues**: Cross-origin security policies block microphone streams
- 🚫 **Server-Side Processing**: Wake word detection runs on Django server, not in browser

### **Technical Issues:**
- Wake word detection requires **continuous microphone listening**
- Streamlit runs in browser with **limited audio capabilities**
- Azure Speech SDK needs **system-level microphone access**
- Real-time processing requires **server-side execution**

---

## ✅ Proper Testing Methods

### **Method 1: Python Script Testing (Recommended)**

Use the dedicated testing script for full functionality:

```bash
# Run the comprehensive testing script
python test_wake_word.py
```

**Features:**
- ✅ Direct microphone access
- ✅ Full wake word detection
- ✅ API endpoint testing
- ✅ Complete pipeline testing
- ✅ Error diagnostics

### **Method 2: Command Line Wake Word**

Run wake word detection directly:

```bash
# Start wake word detection
python wake_word_detection.py

# Or use the example script
python wake_word_example.py
```

### **Method 3: API Testing**

Test individual endpoints:

```bash
# Start detection
curl -X POST http://localhost:8000/api/v1/wakeword/start

# Check status
curl http://localhost:8000/api/v1/wakeword/status

# Stop detection
curl -X POST http://localhost:8000/api/v1/wakeword/stop
```

---

## 🧪 Step-by-Step Testing Process

### **Step 1: Environment Check**

First, verify your environment setup:

```bash
# Check Azure credentials
echo $AZURE_SPEECH_KEY
echo $AZURE_SPEECH_REGION

# If not set, add to .env file:
# AZURE_SPEECH_KEY=your_key_here
# AZURE_SPEECH_REGION=eastus2
```

### **Step 2: Django Server**

Make sure Django server is running:

```bash
# Start Django server
python manage.py runserver

# Verify server is running
curl http://localhost:8000/admin/
```

### **Step 3: Microphone Test**

Test microphone access:

```bash
# Run microphone test
python test_wake_word.py
# Choose option 2: Test microphone access
```

### **Step 4: Wake Word Detection**

Test actual wake word detection:

```bash
# Run wake word test
python test_wake_word.py
# Choose option 3: Test direct wake word detection

# Say: "hey buddy, how does the airbag work?"
```

### **Step 5: Full Pipeline**

Test complete voice assistant:

```bash
# Run full pipeline test
python test_wake_word.py
# Choose option 4: Test full pipeline

# Say: "hey buddy" + any question about your documents
```

---

## 🔧 Troubleshooting Common Issues

### **Issue 1: Microphone Not Working**

**Symptoms:**
- No speech detected
- Recognition fails
- Microphone access denied

**Solutions:**
```bash
# Check microphone permissions
# Windows: Settings > Privacy > Microphone
# Linux: Check ALSA/PulseAudio
# macOS: System Preferences > Security & Privacy > Microphone

# Test microphone with:
python test_wake_word.py  # Option 2
```

### **Issue 2: Azure Credentials**

**Symptoms:**
- "Azure Speech credentials not configured"
- Authentication errors
- Connection failed

**Solutions:**
```bash
# Verify credentials
python -c "
import os
print('Key:', os.getenv('AZURE_SPEECH_KEY', 'NOT SET'))
print('Region:', os.getenv('AZURE_SPEECH_REGION', 'NOT SET'))
"

# Set in .env file:
AZURE_SPEECH_KEY=your_actual_key
AZURE_SPEECH_REGION=your_region
```

### **Issue 3: Django Server Issues**

**Symptoms:**
- Connection refused
- API endpoints not found
- 404 errors

**Solutions:**
```bash
# Check server status
curl -I http://localhost:8000/admin/

# Restart server
python manage.py runserver

# Check installed apps in settings.py
# Make sure 'wake_word' is in INSTALLED_APPS
```

### **Issue 4: Wake Word Not Detected**

**Symptoms:**
- Speech recognized but wake word missed
- Commands not processed
- No detection events

**Solutions:**
- Speak clearly: "**hey buddy**, how does the airbag work?"
- Use proper spacing and pronunciation
- Check microphone sensitivity
- Increase volume/get closer to microphone

---

## 📊 Expected Test Results

### **Successful Wake Word Detection:**

```
🎯 WAKE WORD DETECTED at Mon Jan 15 14:30:45 2024
   Command: 'how does the airbag work'

📝 AI Response: • Airbags are safety devices that inflate rapidly during a collision
• They use sodium azide as the inflating agent
• Sensors detect rapid deceleration and trigger deployment...

🔊 Playing audio response...
```

### **API Status Response:**

```json
{
  "status": "success",
  "listening": true,
  "wake_word": "hey buddy",
  "detection_count": 3,
  "recent_detections": [
    {
      "timestamp": 1703123456.789,
      "full_text": "Hey buddy, how does the airbag work?",
      "command_text": "how does the airbag work",
      "confidence": 0.95
    }
  ]
}
```

---

## 🎯 Testing Checklist

Use this checklist to verify wake word functionality:

### **Environment Setup:**
- [ ] Azure Speech Service credentials configured
- [ ] Django server running on localhost:8000
- [ ] Microphone connected and working
- [ ] Python environment activated

### **Basic Functionality:**
- [ ] API endpoints respond (start/stop/status)
- [ ] Microphone access test passes
- [ ] Single speech recognition works
- [ ] Wake word detection module initializes

### **Wake Word Detection:**
- [ ] "hey buddy" phrase detected
- [ ] Command text extracted correctly
- [ ] Multiple detections work
- [ ] False positives are minimal

### **Complete Pipeline:**
- [ ] Wake word triggers semantic search
- [ ] AI generates relevant summary
- [ ] Text-to-speech plays response
- [ ] End-to-end latency acceptable

### **Error Handling:**
- [ ] Graceful handling of microphone issues
- [ ] Network error recovery
- [ ] Azure service outage handling
- [ ] Invalid command processing

---

## 🚀 Production Deployment Testing

For production environments:

```bash
# Test with Docker
docker-compose up --build
docker-compose exec voice-api python test_wake_word.py

# Test with systemd service
sudo systemctl start voice-assistant
python test_wake_word.py

# Load testing
# Run multiple concurrent wake word detections
```

---

## 💡 Alternative Solutions

If wake word detection still doesn't work:

### **Option 1: Push-to-Talk**
- Use button activation instead of wake word
- Implement in Streamlit with audio recording
- More reliable for web applications

### **Option 2: Scheduled Detection**
- Run wake word detection as background service
- Monitor through API endpoints
- Use webhook notifications

### **Option 3: Desktop Application**
- Create standalone desktop app
- Full system integration
- No browser limitations

### **Option 4: Mobile App**
- Native mobile application
- Better microphone access
- Always-on capabilities

---

## 📞 Getting Help

If you're still having issues:

1. **Run the full test suite:**
   ```bash
   python test_wake_word.py
   # Choose option 5: Run all tests
   ```

2. **Check the logs:**
   ```bash
   # Django logs
   tail -f voice_assistant.log
   
   # System logs
   journalctl -f -u voice-assistant
   ```

3. **Verify system requirements:**
   - Python 3.11+
   - Azure Speech SDK
   - Working microphone
   - Network connectivity

The wake word system should work perfectly when tested properly outside of Streamlit! 🎤✨