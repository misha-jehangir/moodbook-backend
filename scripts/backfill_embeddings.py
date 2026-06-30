import sys
import os
import time
import argparse

# Add the parent directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.gemini_service import get_embeddings_batch

import firebase_admin
from firebase_admin import credentials, firestore

def main():
    parser = argparse.ArgumentParser(description="Backfill vector embeddings for historical mood entries.")
    parser.add_argument("--limit", type=int, default=None, help="Max number of entries to process in this run.")
    args = parser.parse_args()

    print("Starting historical embedding backfill...")
    
    # Load settings
    if not settings.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set in your .env file.")
        return
        
    # Initialize Firebase Admin
    cred_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "service-account.json"
    )
    if not os.path.exists(cred_path):
        print(f"Error: service-account.json not found at: {cred_path}")
        print("Please place your Firebase Admin SDK service account key in the backend root directory.")
        return
        
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
    
    target_uid = "IAIQRkIqfzdV8MGmDG6BCP3yTnG2"
    print(f"Fetching mood entries for user: {target_uid}...")
    
    # Fetch all entries to filter in memory (avoids having to create composite index just for backfill query)
    docs = db.collection('mood_entries').where('userId', '==', target_uid).stream()
    
    entries_to_update = []
    
    for doc in docs:
        data = doc.to_dict()
        # Check if notesEmbedding is missing/None and notes has text content
        if not data.get('notesEmbedding') and data.get('notes'):
            entries_to_update.append((doc.id, data.get('notes')))
            
    total_to_update = len(entries_to_update)
    print(f"Found {total_to_update} entries needing embeddings.")
    
    # Apply user-specified limit if provided
    if args.limit is not None:
        entries_to_update = entries_to_update[:args.limit]
        total_to_update = len(entries_to_update)
        print(f"Limiting run to first {total_to_update} entries.")
        
    if total_to_update == 0:
        print("No entries need embeddings. Exiting.")
        return
        
    # Batch process in chunks of 100 (Gemini batch limit)
    chunk_size = 100
    for i in range(0, total_to_update, chunk_size):
        chunk = entries_to_update[i:i + chunk_size]
        doc_ids = [item[0] for item in chunk]
        texts = [item[1] for item in chunk]
        
        print(f"\nProcessing chunk {i // chunk_size + 1} of {(total_to_update + chunk_size - 1) // chunk_size} (Size: {len(chunk)})...")
        
        try:
            # Generate embeddings in batch via Gemini
            embeddings = get_embeddings_batch(texts)
            
            if len(embeddings) != len(doc_ids):
                print(f"Error: Received {len(embeddings)} embeddings for {len(doc_ids)} texts. Skipping chunk.")
                continue

            # Write back to Firestore in a batch update
            db_batch = db.batch()
            for doc_id, vector in zip(doc_ids, embeddings):
                doc_ref = db.collection('mood_entries').document(doc_id)
                db_batch.update(doc_ref, {"notesEmbedding": vector})
                
            print("Writing vectors to Firestore...")
            db_batch.commit()
            print("Batch committed successfully.")
            
        except Exception as e:
            print(f"Error processing chunk: {e}")
            print("Stopping to prevent partial updates. You can run the script again to resume.")
            return
            
        # Sleep for 65 seconds to stay under the 100 RPM (Requests Per Minute) free-tier limit of Gemini API
        if i + chunk_size < total_to_update:
            print("Sleeping for 65 seconds to prevent API rate limit issues...")
            time.sleep(65)
            
    print("\nBackfill complete! All historical entries are now embedded.")

if __name__ == "__main__":
    main()
