from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from app.utils import read_pdf, split_text, get_pdf_files
from app.config import DATA_DIR, MODEL_NAME, FAISS_INDEX_PATH
import google.generativeai as genai
import os

# Initialize models
embedding_model = SentenceTransformer(MODEL_NAME)
genai.configure(api_key='AIzaSyDbYFrawCr3lA-Nn2ubnf6sRi77HdJS4CM')
gemini_model = genai.GenerativeModel("gemini-pro")

# Global variables for the index and texts
global_index = None
global_texts = None

def embed_chunks(chunks):
    return embedding_model.encode(chunks)

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def process_documents(folder_path=DATA_DIR):
    global global_index, global_texts
    
    all_texts = []
    for file_path in get_pdf_files(folder_path):
        text = read_pdf(file_path)
        chunks = split_text(text)
        all_texts.extend(chunks)

    embeddings = embed_chunks(all_texts)
    global_index = build_faiss_index(np.array(embeddings))
    global_texts = all_texts

    # Save the index for persistence
    if not os.path.exists(os.path.dirname(FAISS_INDEX_PATH)):
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH))
    faiss.write_index(global_index, FAISS_INDEX_PATH)

def load_faiss_index():
    global global_index
    if os.path.exists(FAISS_INDEX_PATH):
        global_index = faiss.read_index(FAISS_INDEX_PATH)

def query_index(query, top_k=3):
    if global_index is None or global_texts is None:
        load_faiss_index()
        if global_index is None:
            return []
    
    q_embedding = embedding_model.encode([query])
    distances, indices = global_index.search(np.array(q_embedding), top_k)
    return [global_texts[idx] for idx in indices[0]]

def get_answer(question: str) -> str:
    # First try to get answer from documents
    relevant_chunks = query_index(question)
    
    if relevant_chunks:
        context = "\n\n".join(relevant_chunks)
        prompt = f"""Based on the following context:
        {context}
        
        Answer this question: {question}"""
        
        try:
            response = gemini_model.generate_content(prompt)
            return f"Answering:gem{{{response.text}}}"
        except:
            # Fallback to just returning the relevant chunks
            return f"Relevant information: {relevant_chunks[0]}"
    else:
        # If no relevant documents found, use Gemini directly
        try:
            response = gemini_model.generate_content(question)
            return f"Answering:gem{{{response.text}}}"
        except Exception as e:
            return f"Error: {str(e)}"