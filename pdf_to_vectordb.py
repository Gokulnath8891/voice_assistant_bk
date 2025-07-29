#!/usr/bin/env python3
"""
PDF to Vector Database Script
Extracts text from PDF files, generates embeddings, and stores in ChromaDB
Compatible with the voice assistant's existing configuration
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List, Tuple
import uuid

import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOFILE"] = "1"

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFVectorizer:
    def __init__(self, vector_store_path: str, collection_name: str):
        """
        Initialize the PDF vectorizer
        
        Args:
            vector_store_path: Path to ChromaDB storage
            collection_name: Name of the ChromaDB collection
        """
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name
        
        # Initialize sentence transformer model (same as voice assistant)
        logger.info("Loading sentence transformer model: thenlper/gte-large")
        self.model = SentenceTransformer('thenlper/gte-large')
        
        # Initialize ChromaDB client
        logger.info(f"Connecting to ChromaDB at: {vector_store_path}")
        self.chroma_client = chromadb.PersistentClient(path=vector_store_path)
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.chroma_client.create_collection(name=collection_name)
            logger.info(f"Created new collection: {collection_name}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n\n--- Page {page_num + 1} ---\n"
                            text += page_text
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1} of {pdf_path}: {e}")
                        continue
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error reading PDF file {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence end if possible
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(start + chunk_size - 200, start + 1), -1):
                    if text[i-1] in '.!?':
                        end = i
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_pdf_file(self, pdf_path: str) -> int:
        """
        Process a single PDF file and add to vector database
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of chunks added to the database
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return 0
        
        # Split into chunks
        chunks = self.chunk_text(text)
        logger.info(f"Split {pdf_path} into {len(chunks)} chunks")
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.model.encode(chunks)
        
        # Prepare data for ChromaDB
        pdf_filename = Path(pdf_path).name
        chunk_ids = [f"{pdf_filename}_chunk_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
        
        # Create metadata for each chunk
        metadatas = [
            {
                "source": pdf_filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "file_path": pdf_path
            }
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB collection
        try:
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids
            )
            logger.info(f"Successfully added {len(chunks)} chunks from {pdf_filename}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error adding chunks to database: {e}")
            return 0
    
    def process_pdf_folder(self, folder_path: str) -> Tuple[int, int]:
        """
        Process all PDF files in a folder
        
        Args:
            folder_path: Path to folder containing PDF files
            
        Returns:
            Tuple of (total_files_processed, total_chunks_added)
        """
        pdf_folder = Path(folder_path)
        if not pdf_folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find all PDF files (case-insensitive)
        pdf_files = []
        seen_files = set()
        
        for pattern in ["*.pdf", "*.PDF"]:
            for pdf_file in pdf_folder.glob(pattern):
                # Use lowercase filename to avoid duplicates
                file_key = pdf_file.name.lower()
                if file_key not in seen_files:
                    pdf_files.append(pdf_file)
                    seen_files.add(file_key)
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {folder_path}")
            return 0, 0
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        total_chunks = 0
        processed_files = 0
        
        for pdf_file in pdf_files:
            try:
                chunks_added = self.process_pdf_file(str(pdf_file))
                if chunks_added > 0:
                    total_chunks += chunks_added
                    processed_files += 1
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue
        
        logger.info(f"Processing complete: {processed_files}/{len(pdf_files)} files processed, {total_chunks} total chunks added")
        return processed_files, total_chunks
    
    def get_collection_info(self) -> dict:
        """Get information about the current collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "vector_store_path": self.vector_store_path
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to vector embeddings in ChromaDB")
    parser.add_argument("pdf_folder", help="Path to folder containing PDF files")
    parser.add_argument("--vector-store-path", 
                       default=os.getenv('VECTOR_STORE_PATH', './chroma_db'),
                       help="Path to ChromaDB storage (default: ./chroma_db)")
    parser.add_argument("--collection-name",
                       default=os.getenv('VECTOR_COLLECTION_NAME', 'voice_assistant_docs'),
                       help="ChromaDB collection name (default: voice_assistant_docs)")
    parser.add_argument("--chunk-size", type=int, default=1000,
                       help="Maximum characters per text chunk (default: 1000)")
    parser.add_argument("--chunk-overlap", type=int, default=200,
                       help="Overlap between chunks in characters (default: 200)")
    
    args = parser.parse_args()
    
    try:
        # Initialize vectorizer
        vectorizer = PDFVectorizer(args.vector_store_path, args.collection_name)
        
        # Show current collection info
        info = vectorizer.get_collection_info()
        if info:
            logger.info(f"Collection info: {info}")
        
        # Process PDF files
        files_processed, chunks_added = vectorizer.process_pdf_folder(args.pdf_folder)
        
        # Show final results
        final_info = vectorizer.get_collection_info()
        logger.info(f"Final collection info: {final_info}")
        
        print(f"\n✅ Processing Complete!")
        print(f"📁 Files processed: {files_processed}")
        print(f"📄 Chunks added: {chunks_added}")
        print(f"🗂️  Collection: {args.collection_name}")
        print(f"📍 Vector store: {args.vector_store_path}")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())