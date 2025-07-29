import json
import time
import os
import uuid
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

# LangChain imports
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

# Disable ChromaDB telemetry and fix httpx compatibility
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOFILE"] = "1"
os.environ["CHROMA_SERVER_SSL_ENABLED"] = "False"

# Fix httpx compatibility issue
import sys
if 'httpx' in sys.modules:
    del sys.modules['httpx']

logger = logging.getLogger(__name__)

# Global variables
qa_chain = None
embedding_model = None
vectordb = None
llm_instance = None  # Store LLM instance separately
retriever_instance = None  # Store retriever instance separately
combine_docs_kwargs = None  # Store combine docs kwargs
conversation_sessions = {}  # Store conversation sessions by session_id


def setup_langchain():
    """Initialize LangChain components"""
    global qa_chain, embedding_model, vectordb, llm_instance, retriever_instance, combine_docs_kwargs
    
    if qa_chain is not None:
        return qa_chain
    
    try:
        # Initialize embedding model
        logger.info("Initializing SentenceTransformer embeddings...")
        embedding_model = SentenceTransformerEmbeddings(model_name='thenlper/gte-large')
        
        # Initialize vector database
        logger.info("Connecting to vector database...")
        vectordb = Chroma(
            collection_name=settings.VECTOR_COLLECTION_NAME,
            persist_directory=settings.VECTOR_STORE_PATH,
            embedding_function=embedding_model
        )
        
        # Create retriever
        retriever_instance = vectordb.as_retriever(
            search_type='similarity',
            search_kwargs={'k': 5}
        )
        
        # Initialize Azure OpenAI
        logger.info("Initializing Azure OpenAI...")
        llm_instance = AzureChatOpenAI(
            deployment_name=settings.CHATGPT_MODEL_NAME,
            temperature=0,
            openai_api_key=settings.AZURE_OPENAI_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            openai_api_version="2025-01-01-preview"
        )
        
        # Custom prompt template
        custom_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are a helpful voice assistant for an automotive technician.
Use the following context to answer the user's question.
If you don't know the answer, say so. Be brief and clear.
If there are multiple steps, just give one step and ask the user if they want to proceed for the next step.

Chat History:
{chat_history}

Context:
{context}

Question:
{question}

Answer:"""
        )
        
        # Store combine docs kwargs globally
        combine_docs_kwargs = {"prompt": custom_prompt}
        
        # Create default memory (will be overridden per session)
        default_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Create conversational retrieval chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_instance,
            retriever=retriever_instance,
            memory=default_memory,
            combine_docs_chain_kwargs=combine_docs_kwargs,
            verbose=True,
            return_source_documents=True
        )
        
        logger.info("LangChain setup completed successfully")
        return qa_chain
        
    except Exception as e:
        logger.error(f"Error setting up LangChain: {e}", exc_info=True)
        raise


def get_or_create_session(session_id=None, topic_name=None):
    """Get or create a conversation session"""
    global conversation_sessions
    
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    if session_id not in conversation_sessions:
        # Create new conversation session with its own memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Clone the main chain but with new memory
        setup_langchain()  # Ensure chain is initialized
        
        session_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_instance,
            retriever=retriever_instance,
            memory=memory,
            combine_docs_chain_kwargs=combine_docs_kwargs,
            verbose=True,
            return_source_documents=True
        )
        
        conversation_sessions[session_id] = {
            'chain': session_chain,
            'memory': memory,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'topic_name': topic_name or "New Topic",
            'message_count': 0
        }
        
        logger.info(f"Created new conversation session: {session_id} with topic: {topic_name}")
    else:
        # Update last accessed time
        conversation_sessions[session_id]['last_accessed'] = time.time()
    
    return session_id, conversation_sessions[session_id]


def cleanup_old_sessions(max_age_hours=24):
    """Clean up old conversation sessions"""
    global conversation_sessions
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    sessions_to_remove = []
    
    for session_id, session_data in conversation_sessions.items():
        if current_time - session_data['last_accessed'] > max_age_seconds:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        del conversation_sessions[session_id]
        logger.info(f"Cleaned up old session: {session_id}")


def detect_new_topic_keywords(user_query):
    """Detect if user wants to start a new conversation topic"""
    new_topic_keywords = [
        'new topic', 'new question', 'different topic', 'change topic',
        'start over', 'new conversation', 'reset', 'clear history',
        'fresh start', 'different question', 'move on', 'next topic'
    ]
    
    query_lower = user_query.lower()
    return any(keyword in query_lower for keyword in new_topic_keywords)


def generate_topic_name(user_query):
    """Generate a topic name based on the first user query"""
    # Remove common question words and conjunctions
    stop_words = {
        'how', 'what', 'when', 'where', 'why', 'who', 'which', 'can', 'could', 'would', 'should',
        'do', 'does', 'did', 'is', 'are', 'was', 'were', 'will', 'has', 'have', 'had',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'among', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    # Automotive-specific topic mapping
    automotive_topics = {
        'engine': ['engine', 'motor', 'combustion', 'cylinder', 'piston', 'valves', 'timing'],
        'transmission': ['transmission', 'gearbox', 'clutch', 'gear', 'shift', 'automatic', 'manual'],
        'brakes': ['brake', 'braking', 'pad', 'rotor', 'disc', 'caliper', 'abs'],
        'suspension': ['suspension', 'shock', 'strut', 'spring', 'damper', 'coil'],
        'electrical': ['electrical', 'battery', 'alternator', 'starter', 'wiring', 'fuse', 'relay'],
        'fuel system': ['fuel', 'injection', 'pump', 'filter', 'carburetor', 'tank'],
        'cooling system': ['cooling', 'radiator', 'coolant', 'thermostat', 'fan', 'temperature'],
        'exhaust': ['exhaust', 'muffler', 'catalytic', 'converter', 'emissions', 'tailpipe'],
        'steering': ['steering', 'wheel', 'rack', 'pinion', 'power steering', 'alignment'],
        'tires': ['tire', 'tyre', 'wheel', 'rim', 'pressure', 'tread', 'rotation'],
        'airbag': ['airbag', 'safety', 'srs', 'crash', 'sensor'],
        'hvac': ['air conditioning', 'heating', 'hvac', 'climate', 'ac', 'heater', 'ventilation']
    }
    
    query_lower = user_query.lower()
    query_words = [word.strip('.,!?;:()[]{}"\'-') for word in query_lower.split()]
    
    # Check for automotive topic matches
    for topic, keywords in automotive_topics.items():
        if any(keyword in query_lower for keyword in keywords):
            return topic.title()
    
    # Extract meaningful words (not stop words)
    meaningful_words = [word for word in query_words if word not in stop_words and len(word) > 2]
    
    # Take first 2-3 meaningful words
    if meaningful_words:
        topic_words = meaningful_words[:3]
        topic_name = ' '.join(word.capitalize() for word in topic_words)
        return topic_name if len(topic_name) <= 30 else topic_words[0].capitalize()
    
    # Fallback to generic name
    return "General Query"


def get_conversational_chain(user_query, session_id=None):
    """
    Process user query using LangChain with conversation memory
    
    Args:
        user_query: The user's question
        session_id: Optional session ID for conversation continuity
        
    Returns:
        tuple: (answer, relevant_chunks, session_id)
    """
    try:
        # Check if user wants to start a new topic
        if detect_new_topic_keywords(user_query):
            # Clear old session if it exists
            if session_id and session_id in conversation_sessions:
                del conversation_sessions[session_id]
                logger.info(f"Auto-cleared session due to new topic keywords: {session_id}")
            session_id = None  # Force creation of new session
        
        # Generate topic name for new sessions
        is_new_session = session_id is None or session_id not in conversation_sessions
        topic_name = None
        if is_new_session:
            topic_name = generate_topic_name(user_query)
        
        # Get or create conversation session
        session_id, session_data = get_or_create_session(session_id, topic_name)
        chain = session_data['chain']
        
        # Update message count
        session_data['message_count'] += 1
        
        # Clean up old sessions periodically
        if len(conversation_sessions) > 50:  # Arbitrary threshold
            cleanup_old_sessions()
        
        # Process the query
        logger.info(f"Processing query in session {session_id}: {user_query}")
        
        result = chain({"question": user_query})
        
        # Extract answer and source documents
        answer = result.get('answer', 'No answer generated')
        source_documents = result.get('source_documents', [])
        
        # Format source documents for API response
        relevant_chunks = []
        for doc in source_documents:
            chunk_data = {
                'page_content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': getattr(doc, 'similarity_score', 0.8)  # Default score
            }
            relevant_chunks.append(chunk_data)
        
        logger.info(f"Generated answer with {len(relevant_chunks)} source documents")
        
        return answer, relevant_chunks, session_id, session_data['topic_name']
        
    except Exception as e:
        logger.error(f"Error in conversational chain: {e}", exc_info=True)
        return f"Sorry, I encountered an error: {str(e)}", [], session_id, "Error"


@csrf_exempt
@require_http_methods(["POST"])
def search_query(request):
    """Handle search query with conversation memory"""
    start_time = time.time()
    
    try:
        # Check required settings
        if not all([settings.VECTOR_STORE_PATH, settings.VECTOR_COLLECTION_NAME]):
            return JsonResponse({
                'status': 'error',
                'message': 'Vector database configuration missing'
            }, status=500)
            
        if not all([settings.AZURE_OPENAI_KEY, settings.AZURE_OPENAI_ENDPOINT, settings.CHATGPT_MODEL_NAME]):
            return JsonResponse({
                'status': 'error',
                'message': 'Azure OpenAI configuration missing'
            }, status=500)
        
        data = json.loads(request.body)
        query = data.get('query')
        session_id = data.get('session_id')  # Optional session ID
        max_chunks = data.get('max_chunks', 5)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        
        if not query:
            return JsonResponse({
                'status': 'error',
                'message': 'Query is required'
            }, status=400)
        
        # Process query with conversation memory
        summary, relevant_chunks, session_id, topic_name = get_conversational_chain(
            user_query=query,
            session_id=session_id
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return JsonResponse({
            'status': 'success',
            'query': query,
            'summary': summary,
            'session_id': session_id,
            'topic_name': topic_name,
            'relevant_chunks': [
                {
                    'content': chunk['page_content'], 
                    'metadata': chunk['metadata'], 
                    'similarity_score': chunk['similarity_score']
                } for chunk in relevant_chunks
            ],
            'processing_time_ms': processing_time_ms,
            'conversation_active': True
        })
        
    except Exception as e:
        logger.error(f"Semantic search error: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_conversation(request):
    """Clear conversation memory for a session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Session ID is required'
            }, status=400)
        
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
            logger.info(f"Cleared conversation session: {session_id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Conversation memory cleared',
                'session_id': session_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Session not found'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversation_history(request):
    """Get conversation history for a session"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Session ID is required'
            }, status=400)
        
        if session_id not in conversation_sessions:
            return JsonResponse({
                'status': 'error',
                'message': 'Session not found'
            }, status=404)

        session_data = conversation_sessions[session_id]
        memory = session_data['memory']
        
        # Get chat history from memory
        chat_history = []
        if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
            for message in memory.chat_memory.messages:
                chat_history.append({
                    'type': message.__class__.__name__.lower(),
                    'content': message.content
                })
        
        return JsonResponse({
            'status': 'success',
            'session_id': session_id,
            'chat_history': chat_history,
            'created_at': session_data['created_at'],
            'last_accessed': session_data['last_accessed']
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_new_session(request):
    """Create a new conversation session"""
    try:
        data = json.loads(request.body) if request.body else {}
        topic_name = data.get('topic_name', 'New Topic')
        
        # Force create a new session
        new_session_id = str(uuid.uuid4())
        session_id, session_data = get_or_create_session(new_session_id, topic_name)
        
        logger.info(f"Created new session via API: {session_id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'New conversation session created',
            'session_id': session_id,
            'topic_name': session_data['topic_name'],
            'created_at': session_data['created_at']
        })
        
    except Exception as e:
        logger.error(f"Error creating new session: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reset_session(request):
    """Reset/clear a specific session or create new one"""
    try:
        data = json.loads(request.body)
        old_session_id = data.get('session_id')
        topic_name = data.get('topic_name', 'New Topic')
        
        if old_session_id and old_session_id in conversation_sessions:
            # Clear the old session
            del conversation_sessions[old_session_id]
            logger.info(f"Cleared old session: {old_session_id}")
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        session_id, session_data = get_or_create_session(new_session_id, topic_name)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Session reset successfully',
            'old_session_id': old_session_id,
            'new_session_id': session_id,
            'topic_name': session_data['topic_name'],
            'created_at': session_data['created_at']
        })
        
    except Exception as e:
        logger.error(f"Error resetting session: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_active_sessions(request):
    """List all active conversation sessions"""
    try:
        sessions_info = []
        
        for session_id, session_data in conversation_sessions.items():
            sessions_info.append({
                'session_id': session_id,
                'topic_name': session_data.get('topic_name', 'Unknown Topic'),
                'created_at': session_data['created_at'],
                'last_accessed': session_data['last_accessed'],
                'message_count': session_data.get('message_count', 0)
            })
        
        return JsonResponse({
            'status': 'success',
            'active_sessions': len(sessions_info),
            'sessions': sessions_info
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)

        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)