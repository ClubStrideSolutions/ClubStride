# document_storage.py
import os
import mimetypes
import uuid
from datetime import datetime
import streamlit as st

def get_upload_directory():
    """Get the directory for document uploads"""
    # In production, consider using a cloud storage service instead
    base_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def save_uploaded_document(uploaded_file, owner_id, document_type):
    """
    Save an uploaded file to the document storage system.
    Returns tuple of (file_path, file_type, file_size)
    """
    # Generate a unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Extract file extension and ensure it's clean
    original_filename = uploaded_file.name
    _, extension = os.path.splitext(original_filename)
    extension = extension.lower()
    
    # Determine MIME type
    content_type = uploaded_file.type
    if not content_type:
        content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
    
    # Create a secure filename
    secure_filename = f"{document_type}_{timestamp}_{owner_id}_{unique_id}{extension}"
    
    # Determine storage path
    upload_dir = get_upload_directory()
    year_month = datetime.utcnow().strftime("%Y-%m")
    target_dir = os.path.join(upload_dir, year_month)
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, secure_filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # For database storage, use a relative path
    relative_path = os.path.join(year_month, secure_filename)
    file_size = os.path.getsize(file_path)
    
    return relative_path, content_type, file_size

def get_document_file_path(relative_path):
    """Convert a relative path to a full path"""
    return os.path.join(get_upload_directory(), relative_path)