import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

# Retrieve the active Firestore client
db = firestore.client()

def serialize_doc(doc) -> dict:
    """
    Helper to serialize a Firestore document dict.
    Converts datetime objects and Timestamp objects to ISO strings,
    and removes the vector embedding so we don't bloat the LLM context window.
    """
    data = doc.to_dict()
    data['id'] = doc.id
    
    # Convert Timestamp/datetime to ISO string
    if 'timestamp' in data:
        ts = data['timestamp']
        if isinstance(ts, datetime.datetime):
            data['timestamp'] = ts.isoformat()
        elif hasattr(ts, 'to_datetime'): # Firestore Timestamp object
            data['timestamp'] = ts.to_datetime().isoformat()
            
    # Remove notesEmbedding from results sent to LLM to save tokens
    if 'notesEmbedding' in data:
        del data['notesEmbedding']
        
    return data

def get_recent_entries(user_id: str, limit: int = 50) -> list[dict]:
    """
    Retrieves the most recent mood entries for a user, sorted in-memory
    to avoid composite index errors during development.
    """
    docs = db.collection('mood_entries').where('userId', '==', user_id).stream()
    serialized = [serialize_doc(doc) for doc in docs]
    
    # Sort by timestamp descending
    serialized.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return serialized[:limit]

def get_entries_by_date_range(user_id: str, start_date_str: str, end_date_str: str) -> list[dict]:
    """
    Retrieves mood entries between start_date and end_date (ISO strings, e.g., 'YYYY-MM-DD').
    Filters in-memory to prevent composite indexing constraints.
    """
    # Parse start and end as datetime objects at boundary points
    start_dt = datetime.datetime.fromisoformat(start_date_str.split('T')[0])
    end_dt = datetime.datetime.fromisoformat(end_date_str.split('T')[0]) + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

    docs = db.collection('mood_entries').where('userId', '==', user_id).stream()
    serialized = []
    
    for doc in docs:
        data = serialize_doc(doc)
        dt = datetime.datetime.fromisoformat(data['timestamp'])
        if start_dt <= dt <= end_dt:
            serialized.append(data)
            
    # Sort chronologically
    serialized.sort(key=lambda x: x.get('timestamp', ''))
    return serialized

def get_entries_by_emotion(user_id: str, emotion: str, limit: int = 20) -> list[dict]:
    """
    Retrieves mood entries that contain the specified emotion tag.
    """
    docs = db.collection('mood_entries')\
             .where('userId', '==', user_id)\
             .where('emotions', 'array_contains', emotion)\
             .stream()
             
    serialized = [serialize_doc(doc) for doc in docs]
    serialized.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return serialized[:limit]

def search_similar_notes(user_id: str, query: str, limit: int = 5) -> list[dict]:
    """
    Performs a native Firestore vector search query using COSINE similarity.
    This fetches the nearest matching journal entries semantically.
    """
    # Import get_embedding locally to prevent circular import at module load
    from app.services.gemini_service import get_embedding
    query_vector = get_embedding(query)
    
    # Perform Firestore native vector query
    results = (
        db.collection('mood_entries')
        .where('userId', '==', user_id)
        .find_nearest(
            vector_field='notesEmbedding',
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit,
            distance_result_field='search_distance' # Returns similarity distance
        )
        .get()
    )
    
    return [serialize_doc(doc) for doc in results]
