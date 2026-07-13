from typing import List, Tuple
from langchain_core.documents import Document
from src.config import settings

def check_confidence(search_results: List[Tuple[Document, float]]) -> Tuple[bool, List[Document], float]:
    """
    Checks if the closest document chunk meets the confidence threshold.
    Converts Chroma cosine distance to a similarity score:
    similarity = 1.0 - cosine_distance
    
    Args:
        search_results: List of (Document, cosine_distance) tuples from Chroma.
        
    Returns:
        Tuple[bool, List[Document], float]:
            - bool: True if the best similarity is >= CONFIDENCE_THRESHOLD, False otherwise.
            - List[Document]: List of documents passing the threshold if overall checks pass.
            - float: Best similarity score calculated.
    """
    if not search_results:
        return False, [], 0.0
        
    # Chroma sorts by distance ascending, so first index is the closest match
    best_doc, best_distance = search_results[0]
    
    # Convert cosine distance to similarity score
    # Cosine distance = 1.0 - cosine_similarity. So similarity = 1.0 - distance.
    best_similarity = 1.0 - best_distance
    best_similarity = max(0.0, min(1.0, best_similarity))
    
    threshold = settings.CONFIDENCE_THRESHOLD
    
    if best_similarity < threshold:
        return False, [], best_similarity
        
    # Return documents that satisfy the threshold
    valid_docs = []
    for doc, dist in search_results:
        sim = max(0.0, min(1.0, 1.0 - dist))
        if sim >= threshold:
            valid_docs.append(doc)
            
    if not valid_docs:
        return False, [], best_similarity
        
    return True, valid_docs, best_similarity

def get_empty_response() -> str:
    """
    Returns the standard fallback answer when retrieval confidence is too low.
    """
    return "İlgili dokümanlarda bu konuda yeterli bilgi bulunamadı."
