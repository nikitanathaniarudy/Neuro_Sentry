"""
Main RAG system for stroke triage.
This connects your knowledge base with Gemini API.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
import os


class StrokeTriageRAG:
    def __init__(self, gemini_api_key=None):
        """
        Initialize RAG system.
        
        Args:
            gemini_api_key: Your Gemini API key (or set GEMINI_API_KEY env var)
        """
        # Get API key from parameter or environment
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "Gemini API key required. Either pass it to __init__ or "
                "set GEMINI_API_KEY environment variable."
            )
        
        print("Initializing RAG system...")
        
        # Load embedding model (runs locally, no API needed)
        print("  Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Configure Gemini
        print("  Configuring Gemini API...")
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel('gemini-pro')
        
        # Storage
        self.documents = []
        self.index = None
        
        print("✓ RAG system ready")
        
    def build_index(self, documents):
        """
        Build vector index from knowledge base documents.
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
        """
        self.documents = documents
        texts = [doc['text'] for doc in documents]
        
        print(f"\nBuilding vector index for {len(texts)} documents...")
        
        # Generate embeddings (this might take 10-30 seconds)
        print("  Generating embeddings...")
        embeddings = self.embedding_model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=32
        )
        
        # Create FAISS index for fast similarity search
        print("  Creating FAISS index...")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"✓ Index built with {len(documents)} documents\n")
        
    def retrieve(self, query, top_k=3):
        """
        Retrieve most relevant documents for a query.
        
        Args:
            query: String or dict of features
            top_k: Number of documents to retrieve
            
        Returns:
            List of documents with relevance scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Convert features to query string if needed
        if isinstance(query, dict):
            query = self._features_to_query(query)
        
        # Embed query
        query_embedding = self.embedding_model.encode([query])
        
        # Search
        distances, indices = self.index.search(
            query_embedding.astype('float32'), 
            top_k
        )
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            doc = self.documents[idx].copy()
            # Convert distance to similarity score
            doc['relevance_score'] = float(1 / (1 + distances[0][i]))
            results.append(doc)
            
        return results
    
    def _features_to_query(self, features):
        """Convert numerical features to natural language query"""
        queries = []
        
        # Check facial asymmetry
        if features.get('face_asymmetry_score', 0) > 0.3:
            queries.append("facial asymmetry stroke")
        
        # Check mouth droop difference
        left = features.get('left_mouth_drop_mm', 0)
        right = features.get('right_mouth_drop_mm', 0)
        diff = abs(left - right)
        
        if diff > 3:
            side = "left" if left > right else "right"
            queries.append(f"{side} sided mouth droop weakness palsy")
        
        # Check speech
        if features.get('speech_clarity_proxy', 1.0) < 0.6:
            queries.append("dysarthria speech impairment")
        
        # Check vitals
        if features.get('hr_mean', 0) > 100:
            queries.append("elevated heart rate")
        if features.get('br_mean', 0) > 20:
            queries.append("elevated respiratory rate")
        
        # Return combined query or default
        return " ".join(queries) if queries else "stroke assessment triage"
    
    def generate_triage(self, presage_features, top_k=3):
        """
        Generate triage assessment using Gemini with retrieved context.
        
        Args:
            presage_features: Dict of live sensor data from Presage
            top_k: Number of documents to retrieve
            
        Returns:
            Dict with triage assessment and retrieved context
        """
        print(f"\nGenerating triage for features: {presage_features}")
        
        # Retrieve relevant context
        print("  Retrieving relevant clinical context...")
        retrieved_docs = self.retrieve(presage_features, top_k=top_k)
        
        print(f"  Retrieved {len(retrieved_docs)} documents")
        for i, doc in enumerate(retrieved_docs, 1):
            print(f"    {i}. {doc['metadata']['category']} "
                  f"(score: {doc['relevance_score']:.3f})")
        
        # Format context for prompt
        context_text = self._format_context(retrieved_docs)
        
        # Build prompt
        prompt = self._build_prompt(presage_features, context_text)
        
        # Call Gemini
        print("  Calling Gemini API...")
        response = self.llm.generate_content(prompt)
        
        # Parse response
        result = self._parse_response(response.text)
        result['retrieved_docs'] = retrieved_docs  # Include for transparency
        
        print("✓ Triage generated successfully\n")
        return result
    
    def _format_context(self, docs):
        """Format retrieved documents for prompt"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc['metadata'].get('source', 'Unknown')
            category = doc['metadata'].get('category', 'Unknown')
            score = doc.get('relevance_score', 0)
            
            formatted.append(
                f"[Document {i}]\n"
                f"Source: {source} | Category: {category} | Relevance: {score:.2f}\n"
                f"Content: {doc['text']}\n"
            )
        return "\n".join(formatted)
    
    def _build_prompt(self, features, context):
        """Build prompt for Gemini"""
        return f"""You are a medical triage AI assistant analyzing real-time patient data from wearable sensors.

LIVE SENSOR DATA FROM PRESAGE:
{json.dumps(features, indent=2)}

RETRIEVED CLINICAL CONTEXT:
{context}

Based on the live sensor data and the retrieved clinical context, provide a triage assessment.

CRITICAL: Respond with ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "overall_risk": <float between 0 and 1>,
  "triage_level": <integer 1-4, where 4=critical, 3=urgent, 2=semi-urgent, 1=non-urgent>,
  "confidence": <float between 0 and 1>,
  "rationale_short": "<brief explanation citing specific features and retrieved context>",
  "ui_directives": {{
    "alert_color": "<red|orange|yellow|green>",
    "highlight_regions": ["<region1>", "<region2>"]
  }}
}}

Guidelines:
- Use retrieved clinical context to ground your reasoning
- Cite specific measurements and thresholds from the context
- Be conservative with risk scores - better to over-triage than under-triage
- Consider combinations of symptoms (e.g., facial palsy + dysarthria)
"""
    
    def _parse_response(self, response_text):
        """Parse Gemini's JSON response"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if '```' in text:
                # Extract content between code blocks
                parts = text.split('```')
                for part in parts:
                    if part.strip().startswith('json'):
                        text = part.replace('json', '', 1).strip()
                        break
                    elif '{' in part:
                        text = part.strip()
                        break
            
            # Parse JSON
            result = json.loads(text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"\n✗ Error parsing Gemini response: {e}")
            print(f"Raw response:\n{response_text}\n")
            raise


def load_knowledge_base(filepath='knowledge_base.json'):
    """Helper to load knowledge base"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("="*60)
    print("Stroke Triage RAG System - Manual Test")
    print("="*60)
    
    # Load knowledge base
    print("\nLoading knowledge base...")
    kb = load_knowledge_base()
    
    # Initialize RAG (will look for GEMINI_API_KEY env var)
    rag = StrokeTriageRAG()
    
    # Build index
    rag.build_index(kb)
    
    # Test with example features
    test_features = {
        "hr_mean": 112,
        "br_mean": 23,
        "face_asymmetry_score": 0.42,
        "left_mouth_drop_mm": 6.1,
        "right_mouth_drop_mm": 0.9,
        "speech_clarity_proxy": 0.47
    }
    
    # Generate triage
    result = rag.generate_triage(test_features)
    
    # Display results
    print("="*60)
    print("TRIAGE RESULT")
    print("="*60)
    print(json.dumps({
        "overall_risk": result['overall_risk'],
        "triage_level": result['triage_level'],
        "confidence": result['confidence'],
        "rationale": result['rationale_short'],
        "ui_directives": result['ui_directives']
    }, indent=2))