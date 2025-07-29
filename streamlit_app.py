import streamlit as st
import streamlit.components.v1 as components
import requests
import io
import json
import time
from audio_recorder_streamlit import audio_recorder

st.set_page_config(
    page_title="Voice Assistant Testing Interface",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Voice Assistant Testing Interface")

BASE_URL = "http://localhost:8000/api/v1"

# Initialize session state for conversation continuity
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None

st.sidebar.header("Configuration")
server_url = st.sidebar.text_input("Server URL", value=BASE_URL)

# Conversation controls in sidebar
st.sidebar.header("Conversation Controls")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 New Chat", key="new_local"):
        st.session_state.session_id = None
        st.session_state.conversation_history = []
        st.session_state.current_topic = None
        st.sidebar.success("Started new conversation!")

with col2:
    if st.button("🆕 API Reset", key="new_api"):
        try:
            response = requests.post(f"{server_url}/search/conversation/new")
            if response.status_code == 200:
                result = response.json()
                st.session_state.session_id = result['session_id']
                st.session_state.current_topic = result.get('topic_name', 'New Topic')
                st.session_state.conversation_history = []
                st.sidebar.success("New session created via API!")
            else:
                st.sidebar.error("Failed to create new session")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

if st.session_state.session_id:
    st.sidebar.info(f"Session ID: {st.session_state.session_id[:8]}...")
    if st.session_state.current_topic:
        st.sidebar.success(f"📋 Topic: **{st.session_state.current_topic}**")
else:
    st.sidebar.info("No active session")

# Show conversation history in sidebar
if st.session_state.conversation_history:
    st.sidebar.header("💬 Conversation History")
    if st.session_state.current_topic:
        st.sidebar.markdown(f"**Current Topic:** {st.session_state.current_topic}")
    
    for i, conv in enumerate(st.session_state.conversation_history[-3:]):  # Show last 3
        with st.sidebar.expander(f"Q{len(st.session_state.conversation_history) - 2 + i}: {conv['query'][:30]}..."):
            st.write(f"**Q:** {conv['query']}")
            st.write(f"**A:** {conv['response'][:100]}...")

st.sidebar.header("API Endpoints")
endpoint = st.sidebar.selectbox(
    "Select Endpoint",
    ["Complete Pipeline", "Wake Word Control", "Speech Recognition", "Semantic Search", "Text-to-Speech"]
)

if endpoint == "Complete Pipeline":
    st.header("Complete Voice Assistant Pipeline")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Audio Input")
        
        input_method = st.radio("Input Method", ["Record Audio", "Upload File"])
        
        audio_data = None
        if input_method == "Record Audio":
            audio_data = audio_recorder(text="Click to record", icon_size="2x")
        else:
            uploaded_file = st.file_uploader("Upload Audio File", type=['wav', 'mp3', 'flac'])
            if uploaded_file:
                audio_data = uploaded_file.read()
        
        if st.button("Process Audio") and audio_data:
            with st.spinner("Processing..."):
                start_time = time.time()
                
                files = {'audio': ('audio.wav', audio_data, 'audio/wav')}
                response = requests.post(f"{server_url}/speech/recognize", files=files)
                
                if response.status_code == 200:
                    speech_result = response.json()
                    recognized_text = speech_result['recognized_text']
                    
                    st.success(f"Recognized: {recognized_text}")
                    
                    # Include session_id in search request
                    search_data = {
                        "query": recognized_text,
                        "session_id": st.session_state.session_id
                    }
                    search_response = requests.post(f"{server_url}/search/query", json=search_data)
                    
                    if search_response.status_code == 200:
                        search_result = search_response.json()
                        summary = search_result['summary']
                        
                        # Update session_id and topic from response
                        if 'session_id' in search_result:
                            st.session_state.session_id = search_result['session_id']
                        if 'topic_name' in search_result:
                            st.session_state.current_topic = search_result['topic_name']
                        
                        # Add to conversation history
                        st.session_state.conversation_history.append({
                            'query': recognized_text,
                            'response': summary
                        })
                        
                        st.info(f"Summary: {summary}")
                        
                        tts_data = {"text": summary}
                        tts_response = requests.post(f"{server_url}/tts/synthesize", json=tts_data)
                        
                        if tts_response.status_code == 200:
                            st.audio(tts_response.content, format='audio/wav')
                            
                            total_time = time.time() - start_time
                            st.metric("Total Processing Time", f"{total_time:.2f}s")
                        else:
                            st.error("Text-to-Speech failed")
                    else:
                        st.error("Semantic search failed")
                else:
                    st.error("Speech recognition failed")
    
    with col2:
        st.subheader("Results")
        st.text("Results will appear here after processing")

elif endpoint == "Wake Word Control":
    st.header("🎤 Wake Word Detection Control")
    
    # Important notice
    st.warning("⚠️ **Important**: Wake word detection requires system microphone access and runs on the Django server, not in the browser. For best results, use the Python testing script: `python test_wake_word.py`")
    
    # Wake word status
    if st.button("🔄 Check Status"):
        try:
            response = requests.get(f"{server_url}/wakeword/status")
            if response.status_code == 200:
                status = response.json()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if status['listening']:
                        st.success("🎧 Listening")
                    else:
                        st.error("🔇 Not Listening")
                
                with col2:
                    st.metric("Wake Word", f'"{status["wake_word"]}"')
                
                with col3:
                    st.metric("Detections", status['detection_count'])
                
                # Recent detections
                if status['recent_detections']:
                    st.subheader("Recent Wake Word Detections")
                    for i, detection in enumerate(status['recent_detections'][-5:]):
                        with st.expander(f"Detection {i+1} - {time.ctime(detection['timestamp'])}"):
                            st.write(f"**Full Text:** {detection['full_text']}")
                            st.write(f"**Command:** {detection['command_text']}")
                            st.write(f"**Confidence:** {detection['confidence']}")
                else:
                    st.info("No recent wake word detections")
            else:
                st.error(f"Failed to get status: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎧 Start Wake Word Detection"):
            with st.spinner("Starting wake word detection..."):
                try:
                    response = requests.post(f"{server_url}/wakeword/start")
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        st.info(f"🗣️ Say '{result['wake_word']}' to activate!")
                    else:
                        st.error(f"Failed to start: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("🛑 Stop Wake Word Detection"):
            with st.spinner("Stopping wake word detection..."):
                try:
                    response = requests.post(f"{server_url}/wakeword/stop")
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error(f"Failed to stop: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Test wake word command processing
    st.subheader("🧪 Test Wake Word Command Processing")
    
    test_command = st.text_input(
        "Enter test command:", 
        placeholder="e.g., how does the airbag work?"
    )
    
    if st.button("🚀 Process Command") and test_command:
        with st.spinner("Processing command..."):
            try:
                response = requests.post(
                    f"{server_url}/wakeword/process",
                    json={
                        "command_text": test_command,
                        "session_id": st.session_state.session_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update session_id and topic from response
                    if 'session_id' in result:
                        st.session_state.session_id = result['session_id']
                    if 'topic_name' in result:
                        st.session_state.current_topic = result['topic_name']
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        'query': test_command,
                        'response': result['summary']
                    })
                    
                    st.success("✅ Command processed successfully!")
                    
                    # Display results
                    st.subheader("📝 AI Summary")
                    st.write(result['summary'])
                    
                    # Convert summary to speech
                    if st.button("🔊 Play Audio Response"):
                        tts_response = requests.post(
                            f"{server_url}/tts/synthesize",
                            json={"text": result['summary']}
                        )
                        if tts_response.status_code == 200:
                            st.audio(tts_response.content, format='audio/wav')
                    
                    # Show relevant chunks
                    if result['relevant_chunks']:
                        st.subheader("📄 Relevant Document Chunks")
                        for i, chunk in enumerate(result['relevant_chunks']):
                            with st.expander(f"Chunk {i+1} - Score: {chunk['similarity_score']:.3f}"):
                                st.write(chunk['content'])
                                if chunk['metadata']:
                                    st.json(chunk['metadata'])
                else:
                    st.error(f"Failed to process command: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Testing alternatives
    st.subheader("🧪 Alternative Testing Methods")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**🐍 Python Script Testing (Recommended)**")
        st.code("python test_wake_word.py", language="bash")
        st.write("• Direct microphone access")
        st.write("• Full wake word detection")
        st.write("• Comprehensive testing")
    
    with col2:
        st.info("**🌐 Browser Limitations**")
        st.write("• Limited microphone access")
        st.write("• No continuous listening")
        st.write("• Use for API testing only")
    
    # Real-time detection stream (limited functionality)
    st.subheader("🔴 Detection Status Monitor")
    
    if st.checkbox("Enable Status Monitoring"):
        st.info("ℹ️ This monitors detection status, but actual wake word detection must run on the server")
        
        # Simplified status monitoring
        status_placeholder = st.empty()
        
        if st.button("Start Monitoring"):
            for i in range(30):  # Monitor for 30 seconds
                try:
                    response = requests.get(f"{server_url}/wakeword/status")
                    if response.status_code == 200:
                        status = response.json()
                        
                        with status_placeholder.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if status['listening']:
                                    st.success("🎧 Listening")
                                else:
                                    st.error("🔇 Not Listening")
                            with col2:
                                st.metric("Detections", status['detection_count'])
                            with col3:
                                st.metric("Time", f"{i+1}s")
                            
                            if status['recent_detections']:
                                st.write("**Recent Detection:**")
                                latest = status['recent_detections'][-1]
                                st.write(f"Command: {latest['command_text']}")
                                st.write(f"Time: {time.ctime(latest['timestamp'])}")
                                break
                    
                    time.sleep(1)
                except Exception as e:
                    st.error(f"Monitoring error: {e}")
                    break
    
    # Original JavaScript implementation (kept for reference but with warnings)
    if st.expander("🔧 Advanced: JavaScript Integration (Limited)"):
        st.warning("⚠️ This JavaScript implementation has limited functionality due to browser security restrictions")
        
        # JavaScript for Server-Sent Events
        components.html("""
        <div id="wake-word-stream">
            <h4>Live Detection Feed:</h4>
            <div id="detections" style="height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
                <p>Waiting for wake word detections...</p>
            </div>
            <button onclick="startStream()">Start Stream</button>
            <button onclick="stopStream()">Stop Stream</button>
        </div>

        <script>
        let eventSource = null;

        function startStream() {
            if (eventSource) {
                eventSource.close();
            }
            
            eventSource = new EventSource('/api/v1/wakeword/stream');
            
            eventSource.onmessage = function(event) {
                const detection = JSON.parse(event.data);
                const detectionsDiv = document.getElementById('detections');
                
                if (detection.wake_word_detected) {
                    const detectionElement = document.createElement('div');
                    detectionElement.innerHTML = `
                        <div style="border-bottom: 1px solid #eee; padding: 5px; margin: 5px 0;">
                            <strong>🎯 Wake Word Detected!</strong><br>
                            <strong>Command:</strong> ${detection.command_text}<br>
                            <strong>Time:</strong> ${new Date(detection.timestamp * 1000).toLocaleString()}
                        </div>
                    `;
                    detectionsDiv.insertBefore(detectionElement, detectionsDiv.firstChild);
                } else if (detection.type === 'heartbeat') {
                    console.log('Heartbeat received');
                }
            };
            
            eventSource.onerror = function(event) {
                console.error('Stream error:', event);
                document.getElementById('detections').innerHTML += '<p style="color: red;">❌ Stream error occurred</p>';
            };
        }

        function stopStream() {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
                document.getElementById('detections').innerHTML += '<p style="color: orange;">🛑 Stream stopped</p>';
            }
        }
        </script>
        """, height=300)

elif endpoint == "Speech Recognition":
    st.header("Speech Recognition Testing")
    
    uploaded_file = st.file_uploader("Upload Audio File", type=['wav', 'mp3', 'flac'])
    
    if uploaded_file and st.button("Recognize Speech"):
        files = {'audio': uploaded_file}
        response = requests.post(f"{server_url}/speech/recognize", files=files)
        
        if response.status_code == 200:
            result = response.json()
            st.success("Recognition successful!")
            st.json(result)
        else:
            st.error(f"Error: {response.text}")

elif endpoint == "Semantic Search":
    st.header("Semantic Search Testing")
    
    query = st.text_input("Enter your query:")
    max_chunks = st.slider("Max chunks", 1, 10, 5)
    similarity_threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)
    
    if query and st.button("Search"):
        data = {
            "query": query,
            "max_chunks": max_chunks,
            "similarity_threshold": similarity_threshold,
            "session_id": st.session_state.session_id
        }
        response = requests.post(f"{server_url}/search/query", json=data)
        
        if response.status_code == 200:
            result = response.json()
            st.success("Search successful!")
            
            # Update session_id and topic from response
            if 'session_id' in result:
                st.session_state.session_id = result['session_id']
            if 'topic_name' in result:
                st.session_state.current_topic = result['topic_name']
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                'query': query,
                'response': result['summary']
            })
            
            st.subheader("Summary")
            st.write(result['summary'])
            
            st.subheader("Relevant Chunks")
            for chunk in result['relevant_chunks']:
                with st.expander(f"Score: {chunk['similarity_score']} - Source: {chunk['source']}"):
                    st.write(chunk['content'])
        else:
            st.error(f"Error: {response.text}")

elif endpoint == "Text-to-Speech":
    st.header("Text-to-Speech Testing")
    
    text = st.text_area("Enter text to synthesize:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        rate = st.slider("Speech Rate", 50, 300, 150)
    with col2:
        volume = st.slider("Volume", 0.0, 1.0, 0.8)
    with col3:
        voice = st.selectbox("Voice", ["default", "male", "female"])
    
    if text and st.button("Synthesize"):
        data = {
            "text": text,
            "voice_settings": {
                "rate": rate,
                "volume": volume,
                "voice": voice
            }
        }
        response = requests.post(f"{server_url}/tts/synthesize", json=data)
        
        if response.status_code == 200:
            st.success("Synthesis successful!")
            st.audio(response.content, format='audio/wav')
        else:
            st.error(f"Error: {response.text}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Performance Metrics")
if st.sidebar.button("Check Server Status"):
    try:
        response = requests.get(f"{server_url.replace('/api/v1', '')}/admin/")
        if response.status_code in [200, 302]:
            st.sidebar.success("Server is running")
        else:
            st.sidebar.error("Server not responding")
    except:
        st.sidebar.error("Cannot connect to server")