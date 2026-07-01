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
    Retrieves the most recent mood entries for a user, querying natively from Firestore.
    """
    docs = (
        db.collection('mood_entries')
        .where('userId', '==', user_id)
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    return [serialize_doc(doc) for doc in docs]

def get_entries_by_date_range(user_id: str, start_date_str: str, end_date_str: str) -> list[dict]:
    """
    Retrieves mood entries between start_date and end_date (ISO strings, e.g., 'YYYY-MM-DD').
    Queries natively from Firestore for sub-second performance.
    """
    # Parse start and end as timezone-aware datetime objects in UTC to match Firestore native queries
    start_dt = datetime.datetime.fromisoformat(start_date_str.split('T')[0]).replace(tzinfo=datetime.timezone.utc)
    end_dt = (datetime.datetime.fromisoformat(end_date_str.split('T')[0]) + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).replace(tzinfo=datetime.timezone.utc)

    docs = (
        db.collection('mood_entries')
        .where('userId', '==', user_id)
        .where('timestamp', '>=', start_dt)
        .where('timestamp', '<=', end_dt)
        .get()
    )
    
    serialized = [serialize_doc(doc) for doc in docs]
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
