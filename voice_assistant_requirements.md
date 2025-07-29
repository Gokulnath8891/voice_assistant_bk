# Voice Assistant Application Requirements

## Project Overview

A voice-enabled intelligent assistant application that processes spoken queries, performs semantic search on a pre-existing vector database, and returns synthesised audio responses. The system leverages Azure Cognitive Services for speech processing and Azure OpenAI for text generation.

## Architecture Components

### Core Technologies
- **Framework**: Django (Python)
- **Speech Recognition**: Azure Cognitive Services Speech SDK
- **Embeddings**: SentenceTransformers (`thenlper/gte-large`)
- **Language Model**: Azure OpenAI GPT-4.1-mini
- **Text-to-Speech**: pyttsx3
- **Vector Store**: Pre-existing collection (path-based loading)
- **Testing Interface**: Streamlit

## Functional Requirements

### FR-1: Voice Recognition API
**Endpoint**: `POST /api/v1/speech/recognize`

**Purpose**: Convert audio input to English text query

**Input**: 
- Audio file (WAV/MP3 format)
- Audio stream data

**Output**:
```json
{
    "status": "success",
    "recognized_text": "What is machine learning?",
    "confidence_score": 0.95,
    "processing_time_ms": 1200
}
```

**Requirements**:
- Support multiple audio formats
- Handle background noise filtering
- Return confidence scores
- Maximum audio length: 60 seconds
- Response time: < 3 seconds

### FR-2: Semantic Search & Summarisation API
**Endpoint**: `POST /api/v1/search/query`

**Purpose**: Process text query, perform similarity search, and generate summarised response

**Input**:
```json
{
    "query": "What is machine learning?",
    "max_chunks": 5,
    "similarity_threshold": 0.7
}
```

**Output**:
```json
{
    "status": "success",
    "query": "What is machine learning?",
    "summary": "Machine learning is a subset of artificial intelligence...",
    "relevant_chunks": [
        {
            "content": "...",
            "similarity_score": 0.89,
            "source": "document_123"
        }
    ],
    "processing_time_ms": 2500
}
```

**Requirements**:
- Load pre-existing vector store by path
- Generate embeddings using `thenlper/gte-large`
- Perform cosine similarity search
- Return top-k relevant chunks
- Summarise using Azure OpenAI GPT-4.1-mini
- Response time: < 5 seconds

### FR-3: Text-to-Speech API
**Endpoint**: `POST /api/v1/speech/synthesize`

**Purpose**: Convert summarised text to audio stream

**Input**:
```json
{
    "text": "Machine learning is a subset of artificial intelligence...",
    "voice_settings": {
        "rate": 150,
        "volume": 0.8,
        "voice": "default"
    }
}
```

**Output**:
- Streaming audio response (WAV format)
- Content-Type: `audio/wav`

**Requirements**:
- Support streaming audio output
- Configurable voice parameters
- Handle text length up to 1000 words
- Audio quality: 16kHz, 16-bit
- Response initiation: < 1 second

## Non-Functional Requirements

### Performance
- **Latency**: End-to-end response < 10 seconds
- **Throughput**: Support 10 concurrent users
- **Availability**: 99.5% uptime

### Security
- API key authentication for Azure services
- Rate limiting: 100 requests/hour per client
- Input validation and sanitisation
- CORS configuration for frontend access

### Scalability
- Stateless API design
- Database connection pooling
- Async processing for I/O operations
- Horizontal scaling capability

## Technical Specifications

### Dependencies
```
Django==4.2.7
django-cors-headers==4.3.1
azure-cognitiveservices-speech==1.34.0
sentence-transformers==2.2.2
openai==1.3.0
pyttsx3==2.90
chromadb==0.4.15
streamlit==1.28.0
requests==2.31.0
python-dotenv==1.0.0
```

### Environment Variables
```
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region
AZURE_OPENAI_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
VECTOR_STORE_PATH=/path/to/vector/store
VECTOR_COLLECTION_NAME=your_collection_name
```

### API Response Standards
- HTTP status codes: 200 (success), 400 (bad request), 500 (server error)
- Consistent JSON response format
- Error handling with descriptive messages
- Request/response logging

## Testing Requirements

### Unit Tests
- Test each API endpoint individually
- Mock external service dependencies
- Validate input/output formats
- Error scenario testing

### Integration Tests
- End-to-end workflow testing
- Azure service connectivity
- Vector store operations
- Audio processing pipeline

### Load Testing
- Concurrent user simulation
- Performance benchmarking
- Memory usage monitoring
- Response time validation

## Streamlit Testing Interface

### Features
- Audio recording capability
- File upload for audio testing
- Real-time API response display
- Audio playback of synthesised speech
- Performance metrics dashboard
- Error logging and debugging

### User Interface Components
- Microphone input button
- File upload widget
- Text display areas
- Audio player controls
- API endpoint selection
- Configuration settings panel

## Deployment Considerations

### Development Environment
- Local Django development server
- SQLite database for development
- Environment variable configuration
- Debug logging enabled

### Production Environment
- WSGI server (Gunicorn/uWSGI)
- PostgreSQL/MySQL database
- Redis for caching
- Nginx reverse proxy
- SSL/TLS encryption
- Production logging configuration

## Success Criteria

1. **Functionality**: All three APIs operational with specified response formats
2. **Performance**: Meet latency and throughput requirements
3. **Reliability**: Handle errors gracefully with appropriate responses
4. **Usability**: Streamlit interface provides intuitive testing capabilities
5. **Documentation**: Complete API documentation with examples
6. **Testing**: Comprehensive test coverage > 90%

## Future Enhancements

- Multi-language support
- Custom voice training
- Real-time streaming capabilities
- Advanced similarity search algorithms
- Conversation context management
- Analytics and usage monitoring