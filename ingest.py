import os
import uuid
import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

# Assuming these modules exist and are correctly implemented as per the plan
from ingest.structured_extractor import StructuredExtractor
from ingest.langextract_job import run_extraction
from ingest.file_parser import extract_text_from_file
import app.database as db

# Load environment variables from .env file
load_dotenv()

# Configure debug logging for ingestion and libraries
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("pinecone").setLevel(logging.DEBUG)

# --- CONFIGURATION ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter") 
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "jd-copilot")
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # A solid open-source embedding model

# --- INITIALIZATION ---
# Initialize Pinecone client
pc = None
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    logging.warning("PINECONE_API_KEY not found in .env file. Pinecone integration will be skipped.")
    pc = None

# Initialize Embedding Model
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Initialize Database
database = db.PlacementDatabase()

# Structured extractor
structured_extractor = StructuredExtractor()

def get_or_create_pinecone_index():
    """Gets or creates the Pinecone index using the new Pinecone client API."""
    if not pc:
        return None
    try:
        existing = [idx.name for idx in pc.list_indexes().names()]
    except Exception:
        try:
            existing = list(pc.list_indexes())
        except Exception:
            existing = []
    if PINECONE_INDEX_NAME not in existing:
        logging.info(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
        try:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=embedding_model.get_sentence_embedding_dimension(),
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-west-2')
            )
        except Exception as e:
            logging.warning(f"Failed to create Pinecone index: {e}. Proceeding without vector index.")
            return None
    # Return an Index-like wrapper - use the client to access by name
    try:
        return pc.Index(PINECONE_INDEX_NAME)
    except Exception:
        return None

def chunk_text(text, chunk_size=800, chunk_overlap=100):
    """Semantically chunks the text using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def process_file(file_path, index):
    """Extracts, chunks, embeds, and upserts data from a single file."""
    logging.info(f"Processing file: {file_path}")
    try:
        text = extract_text_from_file(file_path)
        if not text:
            print(f"Could not extract text from {file_path}")
            return

        # 1. Structured Extraction
        structured_data_obj = None
        structured_data = None
        try:
            structured_data_obj = structured_extractor.extract_structured_data(text)
            if structured_data_obj:
                # Convert dataclass-like object into a plain dict for metadata
                structured_data = json.loads(json.dumps(structured_data_obj, default=lambda o: o.__dict__))
        except Exception:
            structured_data = None

        company_name = structured_data.get("company_name") if structured_data else None
        if not company_name:
            # Fallback extractor if primary fails
            try:
                fallback_data = run_extraction(os.path.basename(file_path), text)
                company_name = fallback_data.get("company")
            except Exception:
                company_name = None

        # 2. Chunking
        chunks = chunk_text(text)
        vectors_to_upsert = []
        
        # 3. Process each chunk for Pinecone
        for i, chunk in enumerate(chunks):
            chunk_id = f"{os.path.basename(file_path)}_{i}"
            
            # Generate embedding
            vector = embedding_model.encode(chunk).tolist()
            
            # Prepare metadata as per the plan
            metadata = {
                "company_name": company_name or "Unknown",
                "source_path": file_path,
                "chunk_id": chunk_id,
                "text": chunk, # Storing the original text is crucial for retrieval
                "ingest_timestamp": datetime.utcnow().isoformat() + 'Z',
                "language": "en", # Assuming English for now
                "structured_fields": structured_data if structured_data else None,
                "confidence_scores": {} # Placeholder for confidence scores
            }
            
            vectors_to_upsert.append((chunk_id, vector, metadata))

        # 4. Upsert to Pinecone
        if index and vectors_to_upsert:
            index.upsert(vectors=vectors_to_upsert)
            logging.info(f"Upserted {len(vectors_to_upsert)} vectors to Pinecone for {file_path}")

        # 5. Insert into SQLite if structured data is present and passes confidence
        # (Confidence check is a placeholder for now as per the plan)
        if structured_data and structured_data.get("company_name"):
            # The plan requires linking the role to the source chunk.
            # We'll use the first chunk's ID as the source for the structured data.
            source_chunk_id = f"{os.path.basename(file_path)}_0"
            if database.insert_company_extraction(structured_data, source_chunk_id):
                logging.info(f"Inserted structured data for '{structured_data.get('company_name')}' into SQLite.")
            else:
                logging.warning(f"Failed to insert structured data for {file_path} into SQLite.")

    except Exception as e:
        logging.exception(f"Failed to process {file_path}: {e}")

def main(folder_path, dry_run=False, limit=0):
    """Main function to ingest a folder of JDs."""
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        return

    if dry_run:
        print("--- DRY RUN MODE ---")
        print("The following actions would be performed:")

    # Get Pinecone index if not a dry run
    index = None
    if not dry_run:
        # PlacementDatabase initializes tables in its constructor
        index = get_or_create_pinecone_index()

    # Process each file in the folder
    processed = 0
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.pdf', '.docx', '.txt', '.html')):
            file_path = os.path.join(folder_path, filename)
            if dry_run:
                print(f"  - Detect file: {file_path}")
                print("    - Plan: Extract text, chunk, create embeddings, and upsert to Pinecone.")
                print("    - Plan: Extract structured data and insert into SQLite.")
            else:
                process_file(file_path, index)
                processed += 1
                if limit and processed >= limit:
                    break
    
    if dry_run:
        print("\n--- END DRY RUN ---")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Ingest job descriptions into the RAG system.")
    parser.add_argument("--folder", type=str, default="tests/sample_jds", help="Folder containing JD files.")
    parser.add_argument("--project", type=str, default="placement", help="Project name (for future use).")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing them.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on number of files to process (0 = no limit).")
    args = parser.parse_args()

    if not os.path.exists(args.folder):
        os.makedirs(args.folder)
        print(f"Created '{args.folder}' directory. Please add your JD files there and run again.")
    else:
        main(args.folder, args.dry_run if args.dry_run else False, limit=args.limit)
