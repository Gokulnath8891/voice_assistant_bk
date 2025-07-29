# Voice Assistant API - Quick Reference

## Base URL: `http://localhost:8000/api/v1`

## 📋 Endpoints Summary

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/wakeword/start` | POST | Start wake word detection | None | JSON status |
| `/wakeword/stop` | POST | Stop wake word detection | None | JSON status |
| `/wakeword/status` | GET | Get detection status | None | JSON with detections |
| `/wakeword/stream` | GET | Live detection stream | None | Server-Sent Events |
| `/wakeword/process` | POST | Process wake word command | JSON with command | JSON with summary |
| `/speech/recognize` | POST | Audio → Text | Audio file | JSON with text |
| `/search/query` | POST | Text → Knowledge Search | JSON with query | JSON with summary |
| `/tts/synthesize` | POST | Text → Audio | JSON with text | Audio file (WAV) |

---

## 🎯 Wake Word Detection

### Start Wake Word Detection
```bash
POST /wakeword/start

curl -X POST http://localhost:8000/api/v1/wakeword/start
```

**Response:**
```json
{
  "status": "success",
  "message": "Wake word detection started",
  "wake_word": "hey buddy",
  "listening": true
}
```

### Get Status & Recent Detections
```bash
GET /wakeword/status

curl http://localhost:8000/api/v1/wakeword/status
```

**Response:**
```json
{
  "status": "success",
  "listening": true,
  "wake_word": "hey buddy",
  "detection_count": 2,
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

### Stop Wake Word Detection
```bash
POST /wakeword/stop

curl -X POST http://localhost:8000/api/v1/wakeword/stop
```

### Process Wake Word Command
```bash
POST /wakeword/process
Content-Type: application/json

curl -X POST http://localhost:8000/api/v1/wakeword/process \
  -H "Content-Type: application/json" \
  -d '{"command_text": "how does the airbag work"}'
```

### Live Detection Stream (JavaScript)
```javascript
const eventSource = new EventSource('/api/v1/wakeword/stream');
eventSource.onmessage = function(event) {
  const detection = JSON.parse(event.data);
  if (detection.wake_word_detected) {
    console.log('Wake word detected:', detection.command_text);
  }
};
```

---

## 🎤 Speech Recognition
```bash
POST /speech/recognize
Content-Type: multipart/form-data

# Upload audio file
curl -X POST http://localhost:8000/api/v1/speech/recognize \
  -F "audio=@recording.wav"
```

**Response:**
```json
{
  "status": "success",
  "recognized_text": "How does the airbag work?",
  "confidence_score": 0.95,
  "processing_time_ms": 1250
}
```

---

## 🔍 Semantic Search
```bash
POST /search/query
Content-Type: application/json

curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the airbag work?"}'
```

**Response:**
```json
{
  "status": "success",
  "query": "How does the airbag work?",
  "summary": "• Airbags inflate rapidly during collision...",
  "relevant_chunks": [...],
  "processing_time_ms": 850
}
```

---

## 🔊 Text-to-Speech
```bash
POST /tts/synthesize
Content-Type: application/json

curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav
```

**Response:** Binary audio data (WAV format)

---

## 🔄 Complete Pipeline Options

### Option 1: Wake Word Pipeline (Recommended)
```javascript
// 1. Start wake word detection
const startResponse = await fetch('/api/v1/wakeword/start', { method: 'POST' });

// 2. Listen for detections
const eventSource = new EventSource('/api/v1/wakeword/stream');
eventSource.onmessage = async function(event) {
  const detection = JSON.parse(event.data);
  
  if (detection.wake_word_detected && detection.command_text) {
    // 3. Process command automatically
    const response = await fetch('/api/v1/wakeword/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command_text: detection.command_text })
    });
    const result = await response.json();
    
    // 4. Convert to speech and play
    const ttsResponse = await fetch('/api/v1/tts/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: result.summary })
    });
    const audioBlob = await ttsResponse.blob();
    const audio = new Audio(URL.createObjectURL(audioBlob));
    audio.play();
  }
};

// Now just say "hey buddy" + your question!
```

### Option 2: Traditional File Upload Pipeline
```javascript
// 1. Upload audio for recognition
const formData = new FormData();
formData.append('audio', audioFile);
const speechResponse = await fetch('/api/v1/speech/recognize', {
  method: 'POST',
  body: formData
});
const speechResult = await speechResponse.json();

// 2. Search knowledge base
const searchResponse = await fetch('/api/v1/search/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: speechResult.recognized_text })
});
const searchResult = await searchResponse.json();

// 3. Convert summary to speech
const ttsResponse = await fetch('/api/v1/tts/synthesize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: searchResult.summary })
});
const audioBlob = await ttsResponse.blob();

// 4. Play audio
const audio = new Audio(URL.createObjectURL(audioBlob));
audio.play();
```

---

## ⚙️ Optional Parameters

### Semantic Search
```json
{
  "query": "your question",
  "max_chunks": 5,              // Default: 5
  "similarity_threshold": 0.7   // Default: 0.7
}
```

### Text-to-Speech
```json
{
  "text": "your text",
  "voice_settings": {
    "rate": 150,        // Speed (50-300)
    "volume": 0.8,      // Volume (0.0-1.0)
    "voice": "default"  // Voice type
  }
}
```

---

## 🚨 Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 400 | "No audio file provided" | Include audio file in request |
| 400 | "Query is required" | Include query text in JSON body |
| 500 | "Azure Speech Service not configured" | Set AZURE_SPEECH_KEY environment variable |
| 500 | "Vector database configuration missing" | Set VECTOR_STORE_PATH environment variable |

---

## 🧪 Test Commands

```bash
# Health check
curl -I http://localhost:8000/admin/

# Test with sample data
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```