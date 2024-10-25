import fitz  # For PDF processing
import docx  # For DOCX processing
from typing import Tuple, List, Union
from fastapi import HTTPException
import os
from llm_models.embed import Embeddings
from db import document_collection
from utils import logger
from datetime import datetime
import time
import tempfile
from pathlib import Path

class FileProcessor:
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    CHUNK_SIZE = 512  # Adjust based on your needs
    CHUNK_OVERLAP = 50  # Adjust based on your needs
    
    def __init__(self):
        self.embeddings = Embeddings()
        # Create a temporary directory that persists for the instance
        self.temp_dir = Path(tempfile.gettempdir()) / 'ai_assistant_uploads'
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str) -> bool:
        """
        Validate if the file type is allowed.
        Returns True if valid, raises HTTPException if not.
        """
        if not any(filename.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Only {', '.join(self.ALLOWED_EXTENSIONS)} files are allowed."
            )
        return True

    async def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        Save file temporarily and return the file location.
        """
        # Create a unique filename to avoid collisions
        unique_filename = f"{int(time.time())}_{filename}"
        file_location = self.temp_dir / unique_filename
        
        # Ensure the directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        try:
            file_location.write_bytes(file_content)
            logger.info(f"File saved temporarily at: {file_location}")
            return str(file_location)
        except Exception as e:
            logger.error(f"Error saving temporary file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {str(e)}"
            )

    async def process_and_store_file(self, file_content: bytes, filename: str) -> Tuple[str, List[float]]:
        """
        Process a file: validate, save temporarily, create embeddings for chunks, 
        store in vector database, and clean up.
        Returns a summary and embeddings.
        """
        try:
            self.validate_file(filename)
            logger.info(f"Processing file: {filename}")

            file_location = await self.save_temp_file(file_content, filename)
            
            try:
                # Extract text and create chunks
                full_text, embeddings = await self.process_file(file_location)
                chunks = self.create_chunks(full_text) if full_text else ["Image file"]
                
                # Process chunks in batches of 96 (Cohere's limit)
                BATCH_SIZE = 96
                timestamp = int(time.time())
                
                for i in range(0, len(chunks), BATCH_SIZE):
                    batch_chunks = chunks[i:i + BATCH_SIZE]
                    logger.info(f"Processing batch {i//BATCH_SIZE + 1} of {len(chunks)//BATCH_SIZE + 1}")
                    
                    # Create embeddings for the batch
                    batch_embeddings = self.embeddings.embed_documents(batch_chunks) if full_text else [embeddings]
                    
                    # Store batch in vector database
                    document_collection.add(
                        documents=batch_chunks,
                        metadatas=[{
                            "filename": filename,
                            "chunk_index": j + i,  # Global chunk index
                            "total_chunks": len(chunks),
                            "type": "image" if filename.endswith(('.jpg', '.jpeg', '.png')) else "document",
                            "timestamp": datetime.now().isoformat()
                        } for j in range(len(batch_chunks))],
                        ids=[f"file_{filename}_{timestamp}_chunk_{j+i}" for j in range(len(batch_chunks))],
                        embeddings=batch_embeddings
                    )
                
                logger.info(f"File processed and stored in {len(chunks)} chunks")
                # Return a brief summary instead of full text
                summary = f"Processed {filename} into {len(chunks)} chunks"
                return summary, embeddings[0] if isinstance(embeddings, list) else embeddings

            finally:
                Path(file_location).unlink(missing_ok=True)
                logger.info(f"Temporary file removed: {file_location}")

        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}", exc_info=True)
            raise

    async def process_file(self, file_path: str) -> Tuple[str, List[float]]:
        """Process file and return both extracted text (if applicable) and embeddings"""
        if file_path.endswith('.pdf'):
            text, _ = self.extract_text_from_pdf(file_path)
            embeddings = self.embeddings.embed_documents([text])
            return text, embeddings[0]
        
        elif file_path.endswith(('.jpg', '.jpeg', '.png')):
            embeddings = self.embeddings.embed_images([file_path])
            return "", embeddings[0]
        
        elif file_path.endswith(('.doc', '.docx')):
            text = self.extract_text_from_doc(file_path)
            embeddings = self.embeddings.embed_documents([text])
            return text, embeddings[0]
        
        else:
            raise ValueError("Unsupported file type")

    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, List[bytes]]:
        doc = fitz.open(file_path)
        text = ""
        images = []

        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            text += page.get_text()

            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append(image_bytes)

        return text, images

    def extract_text_from_doc(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation
        """
        chunks = []
        if not text:
            return chunks

        words = text.split()
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space

            if current_size >= self.CHUNK_SIZE:
                chunks.append(' '.join(current_chunk))
                # Keep overlap words for context
                current_chunk = current_chunk[-self.CHUNK_OVERLAP:]
                current_size = sum(len(word) + 1 for word in current_chunk)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
