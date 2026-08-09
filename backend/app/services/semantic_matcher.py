import logging
import math
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# --- Try imports for Sentence Transformers and FAISS ---
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    import faiss  # type: ignore
    import numpy as np  # type: ignore
    HAS_SEMANTIC_LIBS = True
except ImportError:
    HAS_SEMANTIC_LIBS = False
    SentenceTransformer: Any = None
    faiss: Any = None
    np: Any = None


class MockFAISSIndex:
    """Pure-Python FAISS Index fallback implementing cosine similarity search."""
    def __init__(self, d: int):
        self.d = d
        self.vectors: List[List[float]] = []
        self.ids: List[int] = []

    def add(self, vectors: List[List[float]]):
        for vec in vectors:
            self.vectors.append(vec)

    def search(self, query_vector: List[float], k: int) -> Tuple[List[float], List[int]]:
        if not self.vectors:
            return [], []
            
        results = []
        for idx, vec in enumerate(self.vectors):
            # Compute cosine similarity
            dot = sum(q * v for q, v in zip(query_vector, vec))
            norm_q = math.sqrt(sum(q**2 for q in query_vector))
            norm_v = math.sqrt(sum(v**2 for v in vec))
            sim = dot / (norm_q * norm_v) if norm_q and norm_v else 0.0
            results.append((sim, idx))
            
        results.sort(reverse=True, key=lambda x: x[0])
        top_k = results[:k]
        
        return [r[0] for r in top_k], [r[1] for r in top_k]


# --- Global Model Instance or Fallback Vectorizer ---
_model = None

def get_embedding_model():
    global _model
    if not HAS_SEMANTIC_LIBS:
        return None
    if _model is None:
        try:
            logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2')...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {str(e)}")
            _model = None
    return _model


def get_pure_python_embedding(text: str) -> List[float]:
    """
    Generates a deterministic 128-dimensional unit vector representation of a text
    using term frequencies and hashing for pure-Python fallback.
    """
    import hashlib
    words = [w.lower() for w in text.split() if len(w) > 2]
    
    # 128-dimensional embedding vector
    vec = [0.0] * 128
    
    # Simple hash mapping to assign term weight to vector dimensions
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        dimension = h % 128
        vec[dimension] += 1.0

    # Add general context features
    h_full = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    for i in range(128):
        # Add deterministic pseudo-random noise to make vectors distinctive
        noise = float((h_full >> (i % 32)) & 1) * 0.05
        vec[i] += noise

    # Normalize to unit length
    magnitude = math.sqrt(sum(x**2 for x in vec))
    if magnitude > 0:
        vec = [x / magnitude for x in vec]
    else:
        # Default fallback unit vector
        vec[0] = 1.0
        
    return vec


# --- Core Semantic Matcher Functions ---

def get_text_embedding(text: str) -> List[float]:
    """Generates vector embedding for the input text."""
    model = get_embedding_model()
    if model is not None:
        try:
            emb = model.encode(text)
            return emb.tolist()
        except Exception as e:
            logger.warning(f"SentenceTransformer encoding failed: {str(e)}. Falling back to pure Python.")
            
    return get_pure_python_embedding(text)


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    dot = sum(q * v for q, v in zip(vec1, vec2))
    norm1 = math.sqrt(sum(q**2 for q in vec1))
    norm2 = math.sqrt(sum(v**2 for v in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return dot / (norm1 * norm2)


def match_resume_to_job_semantic(resume_text: str, job_text: str) -> Dict[str, Any]:
    """
    Main entry point: Semantically matches resume with job descriptions.
    Uses FAISS index to do the search similarity query.
    """
    # 1. Generate embeddings
    resume_vec = get_text_embedding(resume_text)
    job_vec = get_text_embedding(job_text)

    # 2. Build index & search similarity (simulate FAISS or use real FAISS)
    if HAS_SEMANTIC_LIBS:
        try:
            # Setup real FAISS index
            dim = len(resume_vec)
            np_res = np.array([resume_vec]).astype('float32')
            np_job = np.array([job_vec]).astype('float32')
            
            index = faiss.IndexFlatIP(dim) # Cosine similarity if normalized
            faiss.normalize_L2(np_res)
            faiss.normalize_L2(np_job)
            
            index.add(np_res)
            distances, indices = index.search(np_job, 1)
            
            similarity = float(distances[0][0])
            # Scale -1..1 similarity to 0..100 percentage
            similarity_pct = round(max(0.0, min(1.0, (similarity + 1.0) / 2.0)) * 100, 2)
            
            logger.info(f"FAISS Match successfully computed: {similarity_pct}%")
            return {
                "semantic_score": similarity_pct,
                "library_used": "FAISS FlatIP Index"
            }
        except Exception as e:
            logger.warning(f"Real FAISS Flat Index search failed: {str(e)}. Falling back to Mock index.")
            pass

    # Fallback to MockFAISSIndex
    mock_index = MockFAISSIndex(d=len(resume_vec))
    mock_index.add([resume_vec])
    scores, indices = mock_index.search(job_vec, 1)
    
    similarity_score = scores[0] if scores else 0.0
    # Map cosine similarity (-1 to 1) to percentage score (0 to 100)
    similarity_pct = round(max(0.0, min(1.0, (similarity_score + 1.0) / 2.0)) * 100, 2)
    
    logger.info(f"Mock FAISS Match computed: {similarity_pct}%")
    return {
        "semantic_score": similarity_pct,
        "library_used": "MockFAISS pure-Python"
    }
