"""
Rebuild the schema index with updated metadata.
Run this after updating schema_metadata.json
"""

import os
import shutil
from app.agents.schema_agent import build_schema_index, extract_schema_from_metadata, CHROMA_PATH

def rebuild_index():
    """Rebuild the Chroma vector index with updated schema metadata."""
    
    print("🔄 Rebuilding schema index...")
    
    # Remove old index
    if os.path.exists(CHROMA_PATH):
        print(f"🗑️  Removing old index at {CHROMA_PATH}")
        shutil.rmtree(CHROMA_PATH)
    
    # Extract schema from metadata
    print("📚 Extracting schema from metadata...")
    schema_docs = extract_schema_from_metadata()
    
    print(f"✅ Found {len(schema_docs)} tables:")
    for doc in schema_docs:
        table_name = doc.metadata.get("table_name", "unknown")
        print(f"   - {table_name}")
    
    # Build new index
    print("🔨 Building new index...")
    vectorstore = build_schema_index(schema_docs)
    
    print(f"✅ Schema index rebuilt successfully at {CHROMA_PATH}")
    print(f"📊 Index contains {vectorstore._collection.count()} documents")
    
    return vectorstore


if __name__ == "__main__":
    rebuild_index()
    print("\n🎉 Done! Restart your server to use the new index.")
