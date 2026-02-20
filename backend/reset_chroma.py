#!/usr/bin/env python3
"""
Reset ChromaDB collection to fix embedding dimension mismatches.

Usage:
    python reset_chroma.py
"""

from pathlib import Path
from app.db.chroma import reset_chroma_collection

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChromaDB Collection Reset Tool")
    print("="*60)
    print("\nThis will DELETE all old embeddings and create a fresh collection.")
    print("You'll need to re-upload your PDFs after this.\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == "yes":
        reset_chroma_collection()
        print("\n✅ ChromaDB collection has been reset successfully!")
        print("You can now re-upload your PDFs.")
    else:
        print("\n❌ Reset cancelled.")
    
    print("="*60 + "\n")
