# process_docs.py
import os
import fitz  # PyMuPDF
import chromadb
import google.generativeai as genai
# --- CONFIGURATION ---
# Make sure your API key is configured, especially for embedding
# This can be done here or ensured via your .env file
genai.configure(api_key="AIzaSyCPLiZ3_wns9WnlucnrykKPnf45WKjfFpE")


DOCUMENTS_DIR = "documents"
CHROMA_DB_PATH = "aml_rules_db"
COLLECTION_NAME = "aml_regulations"
EMBEDDING_MODEL = "text-embedding-004"

def get_pdf_text(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=1000, overlap=100):
    """Splits text into overlapping chunks."""
    # A simple chunking strategy. More advanced methods exist.
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def main():
    print("Starting document processing...")
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    doc_id_counter = 0
    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(DOCUMENTS_DIR, filename)
            print(f"Processing: {filename}")
            
            document_text = get_pdf_text(pdf_path)
            text_chunks = chunk_text(document_text)
            
            # --- THE FIX ---
            # Check if any text was actually extracted before proceeding.
            if not text_chunks or not any(text.strip() for text in text_chunks):
                print(f"Warning: No text found in {filename}. Skipping.")
                continue  # Move to the next file
            # ---------------

            print(f"Generating {len(text_chunks)} embeddings...")
            embeddings = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text_chunks,
                task_type="RETRIEVAL_DOCUMENT"
            )["embedding"]
            
            ids = [f"doc_{filename}_{i}" for i in range(len(text_chunks))]
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=text_chunks
            )
            doc_id_counter += len(text_chunks)

    print("-" * 50)
    print(f"Processing complete. Added {doc_id_counter} document chunks to the database.")
    print(f"Database stored at: {CHROMA_DB_PATH}")
    print("-" * 50)
    
if __name__ == "__main__":
    main()