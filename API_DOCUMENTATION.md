# Voice Assistant API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently, no authentication is required. All endpoints are publicly accessible.

## Content Types
- Request: `application/json` or `multipart/form-data` (for file uploads)
- Response: `application/json` or `audio/wav`

---

## Endpoints

### 1. Wake Word Detection

Control wake word detection for hands-free voice activation using "hey buddy".

**Base Endpoint:** `/wakeword/`

#### Start Wake Word Detection
**Endpoint:** `POST /wakeword/start`

Start continuous wake word detection for "hey buddy".

##### Response
```json
{
  "status": "success",
  "message": "Wake word detection started",
  "wake_word": "hey buddy",
  "listening": true
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/wakeword/start
```

##### Example Request (JavaScript)
```javascript
const response = await fetch('http://localhost:8000/api/v1/wakeword/start', {
  method: 'POST'
});

const result = await response.json();
console.log(result.message); // "Wake word detection started"
```

#### Stop Wake Word Detection
**Endpoint:** `POST /wakeword/stop`

Stop wake word detection.

##### Response
```json
{
  "status": "success",
  "message": "Wake word detection stopped",
  "listening": false
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/wakeword/stop
```

#### Get Wake Word Status
**Endpoint:** `GET /wakeword/status`

Get current status and recent wake word detections.

##### Response
```json
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

##### Example Request (JavaScript)
```javascript
const response = await fetch('http://localhost:8000/api/v1/wakeword/status');
const status = await response.json();

console.log(`Listening: ${status.listening}`);
console.log(`Recent detections: ${status.detection_count}`);
```

#### Stream Wake Word Detections
**Endpoint:** `GET /wakeword/stream`

Real-time stream of wake word detections using Server-Sent Events (SSE).

**Content-Type:** `text/event-stream`

##### Example Request (JavaScript)
```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/wakeword/stream');

eventSource.onmessage = function(event) {
  const detection = JSON.parse(event.data);
  
  if (detection.wake_word_detected) {
    console.log('Wake word detected!');
    console.log('Command:', detection.command_text);
    console.log('Full text:', detection.full_text);
  } else if (detection.type === 'heartbeat') {
    console.log('Connection alive');
  }
};

eventSource.onerror = function(event) {
  console.error('Stream error:', event);
};

// Close stream when done
// eventSource.close();
```

#### Process Wake Word Command
**Endpoint:** `POST /wakeword/process`

Process a wake word command through the complete voice assistant pipeline with conversation memory.

##### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| command_text | String | Yes | The command text to process |
| session_id | String | No | Session ID for conversation continuity |

##### Request Body
```json
{
  "command_text": "how does the airbag work",
  "session_id": "optional-session-id"
}
```

##### Response
```json
{
  "status": "success",
  "command_text": "how does the airbag work",
  "summary": "• Airbags are safety devices that inflate rapidly during a collision\n• They use sodium azide as the inflating agent\n• Sensors detect rapid deceleration and trigger deployment",
  "session_id": "abc123e4-f567-8901-2345-6789abcdef01",
  "topic_name": "Airbag",
  "relevant_chunks": [
    {
      "content": "Airbags are inflatable safety devices...",
      "metadata": {
        "source": "automotive_safety.pdf",
        "chunk_index": 5
      },
      "similarity_score": 0.89
    }
  ],
  "processing_time_ms": 1100,
  "wake_word_triggered": true
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/wakeword/process \
  -H "Content-Type: application/json" \
  -d '{"command_text": "how does the airbag work"}'
```

##### Error Responses
```json
// Wake word detection not configured
{
  "status": "error",
  "message": "Azure Speech credentials not configured"
}

// Detection already active
{
  "status": "error",
  "message": "Wake word detection is already active"
}

// Missing command text
{
  "status": "error",
  "message": "Command text is required"
}
```

---

### 2. Speech Recognition

Convert audio files to text using Azure Speech Services.

**Endpoint:** `POST /speech/recognize`

**Content-Type:** `multipart/form-data`

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| audio | File | Yes | Audio file (WAV, MP3, FLAC) |

#### Response
```json
{
  "status": "success",
  "recognized_text": "How does the airbag work?",
  "confidence_score": 0.95,
  "processing_time_ms": 1250
}
```

#### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/speech/recognize \
  -F "audio=@recording.wav"
```

#### Example Request (JavaScript)
```javascript
const formData = new FormData();
formData.append('audio', audioFile);

const response = await fetch('http://localhost:8000/api/v1/speech/recognize', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.recognized_text);
```

#### Error Responses
```json
// No audio file provided
{
  "status": "error",
  "message": "No audio file provided"
}

// Azure Speech Service not configured
{
  "status": "error",
  "message": "Azure Speech Service not configured"
}

// Recognition failed
{
  "status": "error",
  "message": "No speech could be recognized"
}
```

---

### 2. Semantic Search & Conversation Management

Search through document knowledge base with conversation memory and automatic topic detection.

**Endpoint:** `POST /search/query`

**Content-Type:** `application/json`

#### Request Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | String | Yes | - | Search query text |
| session_id | String | No | null | Conversation session ID for continuity |
| max_chunks | Integer | No | 5 | Maximum number of document chunks to retrieve |
| similarity_threshold | Float | No | 0.7 | Minimum similarity score (0.0-1.0) |

#### Request Body
```json
{
  "query": "How does the airbag work?",
  "session_id": "abc123e4-f567-8901-2345-6789abcdef01",
  "max_chunks": 5,
  "similarity_threshold": 0.7
}
```

#### Response
```json
{
  "status": "success",
  "query": "How does the airbag work?",
  "summary": "• Airbags are safety devices that inflate rapidly during a collision\n• They use sodium azide as the inflating agent\n• Sensors detect rapid deceleration and trigger deployment\n• The airbag inflates within 30 milliseconds of impact",
  "session_id": "abc123e4-f567-8901-2345-6789abcdef01",
  "topic_name": "Airbag",
  "relevant_chunks": [
    {
      "content": "Airbags are inflatable safety devices designed to protect vehicle occupants during a collision...",
      "metadata": {
        "source": "automotive_safety.pdf",
        "chunk_index": 5
      },
      "similarity_score": 0.89
    }
  ],
  "processing_time_ms": 850,
  "conversation_active": true
}
```

#### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the airbag work?",
    "max_chunks": 3,
    "similarity_threshold": 0.8
  }'
```

#### Example Request (JavaScript)
```javascript
const response = await fetch('http://localhost:8000/api/v1/search/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'How does the airbag work?',
    max_chunks: 5,
    similarity_threshold: 0.7
  })
});

const result = await response.json();
console.log(result.summary);
```

#### Error Responses
```json
// Missing query
{
  "status": "error",
  "message": "Query is required"
}

// Vector database not configured
{
  "status": "error",
  "message": "Vector database configuration missing"
}

// Azure OpenAI not configured
{
  "status": "error",
  "message": "Azure OpenAI configuration missing"
}
```

---

### 3. Conversation Management

Manage conversation sessions with automatic topic detection and session persistence.

#### Create New Session

**Endpoint:** `POST /search/conversation/new`

Create a new conversation session with optional custom topic name.

##### Request Body
```json
{
  "topic_name": "Engine Diagnostics"
}
```

##### Request Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| topic_name | String | No | "New Topic" | Custom name for the conversation topic |

##### Response
```json
{
  "status": "success",
  "message": "New conversation session created",
  "session_id": "new-uuid-here",
  "topic_name": "Engine Diagnostics",
  "created_at": 1674567890.123
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "Brake System Analysis"
  }'
```

#### Reset Session

**Endpoint:** `POST /search/conversation/reset`

Reset an existing session or create a new one, clearing all conversation history.

##### Request Body
```json
{
  "session_id": "old-session-uuid",
  "topic_name": "New Topic Name"
}
```

##### Request Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| session_id | String | No | null | Session ID to reset (if exists) |
| topic_name | String | No | "New Topic" | Topic name for the new session |

##### Response
```json
{
  "status": "success",
  "message": "Session reset successfully",
  "old_session_id": "old-uuid-here",
  "new_session_id": "new-uuid-here",
  "topic_name": "New Topic Name",
  "created_at": 1674567890.123
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/search/conversation/reset \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123-old-session",
    "topic_name": "Electrical System"
  }'
```

#### Clear Conversation

**Endpoint:** `POST /search/conversation/clear`

Clear conversation history for a specific session without creating a new session.

##### Request Body
```json
{
  "session_id": "session-uuid-to-clear"
}
```

##### Response
```json
{
  "status": "success",
  "message": "Conversation memory cleared",
  "session_id": "session-uuid-to-clear"
}
```

##### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/search/conversation/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123-session-id"}'
```

#### Get Conversation History

**Endpoint:** `GET /search/conversation/history?session_id=<session_id>`

Retrieve conversation history for a specific session.

##### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | String | Yes | Session ID to retrieve history for |

##### Response
```json
{
  "status": "success",
  "session_id": "abc123-session-id",
  "chat_history": [
    {
      "type": "humanmessage",
      "content": "How does the engine work?"
    },
    {
      "type": "aimessage", 
      "content": "The engine converts fuel into mechanical energy..."
    }
  ],
  "created_at": 1674567890.123,
  "last_accessed": 1674567950.456
}
```

##### Example Request (cURL)
```bash
curl "http://localhost:8000/api/v1/search/conversation/history?session_id=abc123-session-id"
```

#### List Active Sessions

**Endpoint:** `GET /search/conversation/sessions`

Get a list of all currently active conversation sessions.

##### Response
```json
{
  "status": "success",
  "active_sessions": 3,
  "sessions": [
    {
      "session_id": "abc123-session-1",
      "topic_name": "Engine Diagnostics",
      "created_at": 1674567890.123,
      "last_accessed": 1674567950.456,
      "message_count": 8
    },
    {
      "session_id": "def456-session-2", 
      "topic_name": "Brake System",
      "created_at": 1674567800.789,
      "last_accessed": 1674567900.123,
      "message_count": 4
    }
  ]
}
```

##### Example Request (cURL)
```bash
curl http://localhost:8000/api/v1/search/conversation/sessions
```

---

### 4. Automatic Topic Detection

The API automatically detects and assigns topic names based on conversation content.

#### Automotive Topic Categories

| Topic | Keywords |
|-------|----------|
| **Engine** | engine, motor, combustion, cylinder, piston, valves, timing |
| **Transmission** | transmission, gearbox, clutch, gear, shift, automatic, manual |
| **Brakes** | brake, braking, pad, rotor, disc, caliper, abs |
| **Suspension** | suspension, shock, strut, spring, damper, coil |
| **Electrical** | electrical, battery, alternator, starter, wiring, fuse, relay |
| **Fuel System** | fuel, injection, pump, filter, carburetor, tank |
| **Cooling System** | cooling, radiator, coolant, thermostat, fan, temperature |
| **Exhaust** | exhaust, muffler, catalytic, converter, emissions, tailpipe |
| **Steering** | steering, wheel, rack, pinion, power steering, alignment |
| **Tires** | tire, tyre, wheel, rim, pressure, tread, rotation |
| **Airbag** | airbag, safety, srs, crash, sensor |
| **HVAC** | air conditioning, heating, hvac, climate, ac, heater, ventilation |

#### Topic Change Detection

The system automatically creates new sessions when it detects keywords like:
- **Topic transition**: "new topic", "different topic", "change topic"
- **Conversation reset**: "start over", "new conversation", "reset"
- **Flow control**: "fresh start", "move on", "next topic"

#### Example: Automatic Topic Detection

```bash
# First query creates "Engine" topic automatically
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the engine work?"}'

# Response includes:
# "topic_name": "Engine"
# "session_id": "abc123-new-session"

# This query auto-creates new session with "Brakes" topic
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Let me move on to a different topic - how do brakes work?",
    "session_id": "abc123-new-session"
  }'

# Response includes:
# "topic_name": "Brakes"
# "session_id": "def456-different-session" (new session created)
```

#### Custom Topic Names

You can also provide custom topic names when creating sessions:

```bash
curl -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Tesla Model S Diagnostics"}'
```

---

### 5. Text-to-Speech

Convert text to speech audio using pyttsx3.

**Endpoint:** `POST /tts/synthesize`

**Content-Type:** `application/json`

#### Request Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text | String | Yes | - | Text to convert to speech |
| voice_settings | Object | No | {} | Voice configuration options |

#### Voice Settings Object
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| rate | Integer | 150 | Speech rate (50-300 words per minute) |
| volume | Float | 0.8 | Volume level (0.0-1.0) |
| voice | String | "default" | Voice type: "default", "male", "female" |

#### Request Body
```json
{
  "text": "The airbag system uses sensors to detect collisions and deploy within milliseconds.",
  "voice_settings": {
    "rate": 150,
    "volume": 0.8,
    "voice": "default"
  }
}
```

#### Response
Returns audio/wav file as binary data.

**Content-Type:** `audio/wav`
**Content-Disposition:** `inline; filename="speech.wav"`

#### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test message",
    "voice_settings": {
      "rate": 150,
      "volume": 0.8,
      "voice": "default"
    }
  }' \
  --output speech.wav
```

#### Example Request (JavaScript)
```javascript
const response = await fetch('http://localhost:8000/api/v1/tts/synthesize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: 'Hello, this is a test message',
    voice_settings: {
      rate: 150,
      volume: 0.8,
      voice: 'default'
    }
  })
});

// Get audio as blob
const audioBlob = await response.blob();

// Create audio element and play
const audio = new Audio(URL.createObjectURL(audioBlob));
audio.play();
```

#### Error Responses
```json
// Missing text
{
  "status": "error",
  "message": "Text is required"
}

// TTS engine error
{
  "status": "error",
  "message": "Text-to-speech conversion failed"
}
```

---

## Complete Conversation Flow Examples

### Example 1: Multi-Turn Conversation with Automatic Topic Detection

```bash
# First query - creates new session with "Engine" topic
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the engine work?"}'

# Response:
# {
#   "session_id": "abc123-session-1",
#   "topic_name": "Engine",
#   "summary": "The engine converts fuel into mechanical energy..."
# }

# Follow-up question - uses same session
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main components you mentioned?",
    "session_id": "abc123-session-1"
  }'

# Response maintains context:
# {
#   "session_id": "abc123-session-1", 
#   "topic_name": "Engine",
#   "summary": "The main engine components I mentioned are cylinders, pistons, valves..."
# }

# Topic change - auto-creates new session
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Let me move on to a different topic - how do brakes work?",
    "session_id": "abc123-session-1"
  }'

# Response with new session:
# {
#   "session_id": "def456-session-2",
#   "topic_name": "Brakes", 
#   "summary": "Brakes use hydraulic pressure to create friction..."
# }
```

### Example 2: Manual Session Management

```bash
# Create custom session with specific topic
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Tesla Model S Troubleshooting"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "Created session: $SESSION_ID"

# Use the session for related queries
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are common issues with Model S charging?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Continue conversation
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"How do I troubleshoot the first issue you mentioned?\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Check conversation history
curl "http://localhost:8000/api/v1/search/conversation/history?session_id=$SESSION_ID"

# Reset to new topic when done
curl -X POST http://localhost:8000/api/v1/search/conversation/reset \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"topic_name\": \"Model S Performance Tuning\"
  }"
```

### Example 3: Wake Word with Conversation Continuity

```bash
# Start wake word detection
curl -X POST http://localhost:8000/api/v1/wakeword/start

# Simulate wake word detection and processing
curl -X POST http://localhost:8000/api/v1/wakeword/process \
  -H "Content-Type: application/json" \
  -d '{"command_text": "how does the transmission work"}'

# Response includes new session:
# {
#   "session_id": "xyz789-wake-session",
#   "topic_name": "Transmission",
#   "summary": "The transmission transfers power from the engine..."
# }

# Follow-up via wake word (include session_id)
curl -X POST http://localhost:8000/api/v1/wakeword/process \
  -H "Content-Type: application/json" \
  -d '{
    "command_text": "what about automatic versus manual",
    "session_id": "xyz789-wake-session"
  }'

# Response maintains conversation context:
# {
#   "session_id": "xyz789-wake-session",
#   "topic_name": "Transmission", 
#   "summary": "Regarding the transmission types I mentioned, automatic..."
# }
```

### Example 4: Complete Audio Pipeline with Sessions

```bash
# Step 1: Create session for audio conversation
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Audio Troubleshooting Session"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')

# Step 2: Process audio file with session context
SPEECH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/speech/recognize \
  -F "audio=@user_question.wav")

RECOGNIZED_TEXT=$(echo $SPEECH_RESPONSE | jq -r '.recognized_text')

# Step 3: Search with conversation memory
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"$RECOGNIZED_TEXT\",
    \"session_id\": \"$SESSION_ID\"
  }")

ANSWER=$(echo $SEARCH_RESPONSE | jq -r '.summary')
TOPIC=$(echo $SEARCH_RESPONSE | jq -r '.topic_name')

# Step 4: Convert to speech
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$ANSWER\"}" \
  --output "answer_audio.wav"

echo "Conversation in topic: $TOPIC"
echo "Audio response saved as: answer_audio.wav"

# Step 5: Continue with follow-up audio
# (Repeat steps 2-4 with same SESSION_ID for conversation continuity)
```

### Example 5: Session Management and Monitoring

```bash
# Create multiple sessions for different topics
curl -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Engine Diagnostics"}'

curl -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Brake System Analysis"}'

curl -X POST http://localhost:8000/api/v1/search/conversation/new \
  -H "Content-Type: application/json" \
  -d '{"topic_name": "Electrical Troubleshooting"}'

# List all active sessions
curl http://localhost:8000/api/v1/search/conversation/sessions

# Response shows all active sessions:
# {
#   "active_sessions": 3,
#   "sessions": [
#     {
#       "session_id": "abc123-engine",
#       "topic_name": "Engine Diagnostics",
#       "message_count": 0,
#       "created_at": 1674567890.123
#     },
#     {
#       "session_id": "def456-brake", 
#       "topic_name": "Brake System Analysis",
#       "message_count": 0,
#       "created_at": 1674567891.456
#     },
#     {
#       "session_id": "ghi789-electrical",
#       "topic_name": "Electrical Troubleshooting", 
#       "message_count": 0,
#       "created_at": 1674567892.789
#     }
#   ]
# }
```

---

## Complete Voice Assistant Pipeline Examples

### Option 1: Wake Word Activated Pipeline

The most convenient way to use the voice assistant with hands-free activation:

```javascript
class WakeWordVoiceAssistant {
  constructor(baseUrl = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
    this.eventSource = null;
  }

  // Start wake word detection
  async startWakeWordDetection() {
    const response = await fetch(`${this.baseUrl}/wakeword/start`, {
      method: 'POST'
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`✅ ${result.message}`);
      console.log(`🗣️ Say "${result.wake_word}" to activate!`);
      
      // Start listening for detections
      this.startDetectionStream();
      return true;
    } else {
      console.error('Failed to start wake word detection');
      return false;
    }
  }

  // Listen for real-time wake word detections
  startDetectionStream() {
    this.eventSource = new EventSource(`${this.baseUrl}/wakeword/stream`);
    
    this.eventSource.onmessage = (event) => {
      const detection = JSON.parse(event.data);
      
      if (detection.wake_word_detected) {
        console.log('🎯 Wake word detected!');
        console.log('Command:', detection.command_text);
        
        // Automatically process the command
        if (detection.command_text) {
          this.processWakeWordCommand(detection.command_text);
        }
      }
    };

    this.eventSource.onerror = (event) => {
      console.error('Wake word stream error:', event);
    };
  }

  // Process wake word command through complete pipeline
  async processWakeWordCommand(commandText) {
    try {
      // Process through semantic search
      const response = await fetch(`${this.baseUrl}/wakeword/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command_text: commandText })
      });

      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('📝 AI Response:', result.summary);
        
        // Convert to speech
        await this.speakResponse(result.summary);
        
        return result;
      } else {
        console.error('Failed to process command:', result.message);
      }
    } catch (error) {
      console.error('Error processing wake word command:', error);
    }
  }

  // Convert text to speech and play
  async speakResponse(text) {
    try {
      const response = await fetch(`${this.baseUrl}/tts/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audio = new Audio(URL.createObjectURL(audioBlob));
        audio.play();
        console.log('🔊 Playing audio response...');
      }
    } catch (error) {
      console.error('Error in text-to-speech:', error);
    }
  }

  // Stop wake word detection
  async stopWakeWordDetection() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    const response = await fetch(`${this.baseUrl}/wakeword/stop`, {
      method: 'POST'
    });

    if (response.ok) {
      const result = await response.json();
      console.log(`🛑 ${result.message}`);
      return true;
    } else {
      console.error('Failed to stop wake word detection');
      return false;
    }
  }

  // Get current status
  async getStatus() {
    const response = await fetch(`${this.baseUrl}/wakeword/status`);
    return await response.json();
  }
}

// Usage Example
const assistant = new WakeWordVoiceAssistant();

// Start wake word detection
assistant.startWakeWordDetection();

// Now just say "hey buddy" followed by your question!
// Example: "Hey buddy, how does the airbag work?"

// Stop when done
// assistant.stopWakeWordDetection();
```

### Option 2: Traditional File Upload Pipeline

For scenarios where you have audio files to process:

```javascript
class VoiceAssistant {
  constructor(baseUrl = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }

  // Step 1: Convert audio to text
  async speechToText(audioFile) {
    const formData = new FormData();
    formData.append('audio', audioFile);

    const response = await fetch(`${this.baseUrl}/speech/recognize`, {
      method: 'POST',
      body: formData
    });

    return await response.json();
  }

  // Step 2: Search knowledge base
  async searchKnowledge(query) {
    const response = await fetch(`${this.baseUrl}/search/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query })
    });

    return await response.json();
  }

  // Step 3: Convert text to speech
  async textToSpeech(text) {
    const response = await fetch(`${this.baseUrl}/tts/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });

    return await response.blob();
  }

  // Complete pipeline
  async processVoiceQuery(audioFile) {
    try {
      // 1. Speech recognition
      const speechResult = await this.speechToText(audioFile);
      if (speechResult.status !== 'success') {
        throw new Error('Speech recognition failed');
      }

      // 2. Knowledge search
      const searchResult = await this.searchKnowledge(speechResult.recognized_text);
      if (searchResult.status !== 'success') {
        throw new Error('Knowledge search failed');
      }

      // 3. Text-to-speech
      const audioBlob = await this.textToSpeech(searchResult.summary);

      return {
        recognizedText: speechResult.recognized_text,
        summary: searchResult.summary,
        audioResponse: audioBlob,
        relevantChunks: searchResult.relevant_chunks
      };
    } catch (error) {
      console.error('Voice processing error:', error);
      throw error;
    }
  }
}

// Usage example
const assistant = new VoiceAssistant();

// Process audio file
document.getElementById('audioInput').addEventListener('change', async (e) => {
  const audioFile = e.target.files[0];
  if (audioFile) {
    try {
      const result = await assistant.processVoiceQuery(audioFile);
      
      // Display results
      document.getElementById('recognizedText').textContent = result.recognizedText;
      document.getElementById('summary').textContent = result.summary;
      
      // Play audio response
      const audio = new Audio(URL.createObjectURL(result.audioResponse));
      audio.play();
    } catch (error) {
      console.error('Error processing voice query:', error);
    }
  }
});
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Server error

### Common Error Patterns
```javascript
// Handle API errors
async function handleApiCall(apiFunction) {
  try {
    const response = await apiFunction();
    
    if (response.status === 'error') {
      throw new Error(response.message);
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error.message);
    // Show user-friendly error message
    showErrorMessage('Something went wrong. Please try again.');
  }
}
```

---

## Rate Limits

Currently, there are no rate limits implemented. However, consider:
- Azure Speech Services has usage quotas
- Azure OpenAI has token limits
- Large audio files may take longer to process

---

## File Format Support

### Audio Input (Speech Recognition)
- **WAV** (Recommended) - Uncompressed, best quality
- **MP3** - Compressed, good quality
- **FLAC** - Lossless compression

### Audio Output (Text-to-Speech)
- **WAV** - Uncompressed audio output

---

## Performance Considerations

### Processing Times (Approximate)
- Speech Recognition: 1-3 seconds
- Semantic Search: 0.5-2 seconds  
- Text-to-Speech: 0.5-1 second

### Optimization Tips
- Use WAV format for best speech recognition accuracy
- Keep queries concise for faster search results
- Cache frequently requested TTS audio
- Implement retry logic for network failures

---

## Environment Variables

The following environment variables need to be configured:

```env
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus2
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
CHATGPT_MODEL=gpt-4o-mini
VECTOR_STORE_PATH=./my_vector_db
VECTOR_COLLECTION_NAME=my_documents
```

---

## Testing the API

### Health Check
```bash
curl -I http://localhost:8000/admin/
```

### Quick Test Sequence
```bash
# 1. Test speech recognition
curl -X POST http://localhost:8000/api/v1/speech/recognize \
  -F "audio=@test_audio.wav"

# 2. Test semantic search
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# 3. Test text-to-speech
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output test_output.wav
```

---

## Support

For issues or questions:
1. Check the logs: `docker-compose logs voice-api`
2. Verify environment variables are set correctly
3. Ensure Azure services are properly configured
4. Test each endpoint individually to isolate issues