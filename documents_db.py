# documents_db.py
from bson import ObjectId
from datetime import datetime, timedelta
import hashlib
import uuid
import pandas as pd
from typing import List, Dict, Optional
from students_db import connect_to_db
import streamlit as st
import plotly.express as px
from instructors_db import list_programs

def generate_document_id(title: str, owner_id: str, timestamp: datetime) -> str:
    """Generate a unique document ID"""
    composite_str = f"{title.strip().lower()}:{owner_id}:{timestamp.isoformat()}"
    full_hash = hashlib.md5(composite_str.encode('utf-8')).hexdigest()
    return full_hash[:12]  # Use first 12 chars for readability

# def create_document(title: str, description: str, document_type: str, 
#                    owner_id: str, owner_type: str, document_url: str,
#                    program_id: Optional[int] = None,
#                    expiration_date: Optional[datetime] = None,
#                    is_template: bool = False,
#                    required_signatures: Optional[List[Dict]] = None,
#                    metadata: Optional[Dict] = None) -> str:
#     """
#     Create a new document record with a URL instead of an uploaded file.
#     Returns the document_id of the created document.
#     """
#     db = connect_to_db()
#     coll = db["Documents"]
    
#     now = datetime.utcnow()
#     document_id = generate_document_id(title, owner_id, now)
    
#     doc = {
#         "document_id": document_id,
#         "title": title,
#         "description": description,
#         "document_type": document_type,
#         "program_id": program_id,
#         "owner_id": owner_id,
#         "owner_type": owner_type,
#         "created_at": now,
#         "updated_at": now,
#         "expiration_date": expiration_date,
#         "template": is_template,
#         "document_url": document_url,  # Store the URL instead of file location
#         "status": "active",
#         "required_signatures": required_signatures or [],
#         "metadata": metadata or {}
#     }
    
#     result = coll.insert_one(doc)
#     if result.inserted_id:
#         return document_id
#     else:
#         return None
# Add this function to documents_db.py

def check_document_exists(title: str = None, document_url: str = None, owner_id: str = None) -> bool:
    """
    Check if a document with the same title or URL already exists for this owner.
    Returns True if a duplicate exists, False otherwise.
    
    Args:
        title: Title to check (optional)
        document_url: Document URL to check (optional)
        owner_id: Owner ID to limit the check to (optional, if None checks all documents)
    """
    db = connect_to_db()
    coll = db["Documents"]
    
    # Build query to check for duplicates
    query = {"$or": []}
    
    if title:
        # Case-insensitive title search
        query["$or"].append({"title": {"$regex": f"^{title}$", "$options": "i"}})
    
    if document_url:
        # Exact URL match
        query["$or"].append({"document_url": document_url})
    
    # If no search criteria provided, return False (no duplicates)
    if not query["$or"]:
        return False
    
    # If owner_id provided, limit search to that owner
    if owner_id:
        query["owner_id"] = owner_id
    
    # Check if any document matches the query
    count = coll.count_documents(query)
    return count > 0
def check_document_instance_exists(document_id: str, recipient_email: str) -> bool:
    """
    Check if a document instance already exists for this document and recipient.
    Returns True if an instance exists, False otherwise.
    
    Args:
        document_id: ID of the document
        recipient_email: Email of the recipient
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    # Check if any instance exists with this document ID and recipient email
    count = coll.count_documents({
        "document_id": document_id,
        "recipient_email": recipient_email
    })
    return count > 0
# Update the create_document function to include duplicate checking
def create_document(title: str, description: str, document_type: str, 
                   owner_id: str, owner_type: str, document_url: str,
                   program_id: Optional[int] = None,
                   expiration_date: Optional[datetime] = None,
                   is_template: bool = False,
                   required_signatures: Optional[List[Dict]] = None,
                   metadata: Optional[Dict] = None,
                   check_duplicates: bool = True) -> str:
    """
    Create a new document record with a URL instead of an uploaded file.
    Returns the document_id of the created document or None if there was an error.
    
    Args:
        title: Document title
        description: Document description
        document_type: Type of document (waiver, permission_slip, etc.)
        owner_id: ID of the document owner
        owner_type: Type of the owner (admin, instructor)
        document_url: URL to the document
        program_id: ID of the associated program (optional)
        expiration_date: Date when the document expires (optional)
        is_template: Whether this document is a template (default: False)
        required_signatures: List of required signature roles (optional)
        metadata: Additional metadata (optional)
        check_duplicates: Whether to check for duplicates (default: True)
    """
    db = connect_to_db()
    coll = db["Documents"]
    
    # Check for duplicates if requested
    if check_duplicates and check_document_exists(title, document_url, owner_id):
        return "duplicate"
    
    now = datetime.utcnow()
    document_id = generate_document_id(title, owner_id, now)
    
    doc = {
        "document_id": document_id,
        "title": title,
        "description": description,
        "document_type": document_type,
        "program_id": program_id,
        "owner_id": owner_id,
        "owner_type": owner_type,
        "created_at": now,
        "updated_at": now,
        "expiration_date": expiration_date,
        "template": is_template,
        "document_url": document_url,  # Store the URL instead of file location
        "status": "active",
        "required_signatures": required_signatures or [],
        "metadata": metadata or {}
    }
    
    result = coll.insert_one(doc)
    if result.inserted_id:
        return document_id
    else:
        return None
    
def list_documents(owner_id: Optional[str] = None, 
                  program_id: Optional[int] = None,
                  document_type: Optional[str] = None,
                  status: Optional[str] = None,
                  is_template: Optional[bool] = None) -> List[Dict]:
    """
    List documents with optional filters.
    Returns a list of document objects.
    """
    db = connect_to_db()
    coll = db["Documents"]
    
    # Build query based on provided filters
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    if program_id:
        query["program_id"] = program_id
    if document_type:
        query["document_type"] = document_type
    if status:
        query["status"] = status
    if is_template is not None:
        query["template"] = is_template
        
    # Get documents matching query
    documents = list(coll.find(query))
    
    # Process ObjectId for JSON serialization
    for doc in documents:
        doc["_id"] = str(doc["_id"])
        
    return documents

def create_document_instance(document_id: str, recipient_id: str, 
                           recipient_type: str, recipient_name: str,
                           recipient_email: str, expiration_days: int = 30) -> str:
    """
    Create a document instance to be sent to a recipient.
    Returns the instance_id of the created instance.
    
    Args:
        document_id: Reference to parent document
        recipient_id: Student ID or other recipient
        recipient_type: "student", "instructor", etc.
        recipient_name: Name of recipient
        recipient_email: Email of recipient
        expiration_days: Number of days until link expires (default: 30)
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    # Generate unique IDs for tracking and security
    instance_id = str(uuid.uuid4())
    access_token = str(uuid.uuid4())
    
    # Create access link (in production, this would use your domain)
    access_link = f"/sign/{instance_id}?token={access_token}"
    
    now = datetime.utcnow()
    expiration = now + timedelta(days=expiration_days)  # Use the passed parameter
    
    instance = {
        "instance_id": instance_id,
        "document_id": document_id,
        "recipient_id": recipient_id,
        "recipient_type": recipient_type,
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "status": "ready",  # Not sent yet
        "sent_at": None,
        "viewed_at": None,
        "signed_at": None,
        "declined_at": None,
        "declined_reason": None,
        "expiration_date": expiration,
        "reminder_count": 0,
        "last_reminder_sent": None,
        "access_link": access_link,
        "access_token": access_token,
        "signature_data": {},
        "form_data": {},
        "activity_log": [
            {
                "action": "created",
                "timestamp": now,
                "actor_id": "system",
                "actor_type": "system",
                "details": "Document instance created"
            }
        ]
    }
    
    result = coll.insert_one(instance)
    if result.inserted_id:
        return instance_id
    else:
        return None

# def send_document(instance_id: str, base_url: str = None, 
#                  email_subject: str = None, email_message: str = None) -> bool:
#     """
#     Send a document to the recipient.
#     Returns True if successful, False otherwise.
    
#     Args:
#         instance_id: The ID of the document instance to send
#         base_url: Base URL for the signing link (e.g., "https://clubstride.org")
#                   If None, will use the value from configuration
#         email_subject: Custom email subject line (if None, uses default)
#         email_message: Additional text to include in the email (if None, uses default)
#     """
#     db = connect_to_db()
#     coll = db["DocumentInstances"]
    
#     # Find the instance
#     instance = coll.find_one({"instance_id": instance_id})
#     if not instance:
#         return False
    
#     # Find the parent document
#     docs_coll = db["Documents"]
#     document = docs_coll.find_one({"document_id": instance["document_id"]})
#     if not document:
#         return False
    
#     # Mark the instance as sent
#     now = datetime.utcnow()
#     result = coll.update_one(
#         {"instance_id": instance_id},
#         {
#             "$set": {
#                 "status": "sent",
#                 "sent_at": now
#             },
#             "$push": {
#                 "activity_log": {
#                     "action": "sent",
#                     "timestamp": now,
#                     "actor_id": "system",
#                     "actor_type": "system",
#                     "details": "Document sent to recipient"
#                 }
#             }
#         }
#     )
    
#     # Send email notification (using your existing email system)
#     if result.modified_count > 0:
#         from mailersend import emails
        
#         MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]
#         mailer = emails.NewEmail(MAILERSEND_API_KEY)
#         mail_body = {}
        
#         mail_from = {
#             "name": "Club Stride Documents",
#             "email": "javier@clubstride.org"
#         }
        
#         recipients = [{
#             "name": instance["recipient_name"],
#             "email": instance["recipient_email"]
#         }]
        
#         # Use provided base_url or get from configuration
#         if not base_url:
#             # Default to configuration or environment variable
#             base_url = st.session_state.get("base_url", "https://clubstride.org")
        
#         # Create a document signing URL
#         signing_url = f"{base_url.rstrip('/')}{instance['access_link']}"
        
#         # Use custom subject if provided
#         if not email_subject:
#             email_subject = f"Please sign your document: {document['title']}"
        
#         # Base email text
#         base_email_text = f"""
# Hello {instance["recipient_name"]},

# You have a document that requires your signature: {document['title']}

# Please click the link below to view and sign the document:
# {signing_url}

# This link will expire on {instance['expiration_date'].strftime('%B %d, %Y')}.
# """
        
#         # Add custom message if provided
#         if email_message:
#             body_text = f"{base_email_text}\n{email_message}\n\nThank you,\nClub Stride Team"
#         else:
#             body_text = f"{base_email_text}\n\nThank you,\nClub Stride Team"
        
#         mailer.set_mail_from(mail_from, mail_body)
#         mailer.set_mail_to(recipients, mail_body)
#         mailer.set_subject(email_subject, mail_body)
#         mailer.set_plaintext_content(body_text, mail_body)
        
#         try:
#             response = mailer.send(mail_body)
#             print(f"MailerSend document notification response: {response}")
#             return True
#         except Exception as e:
#             print(f"Error sending document email: {e}")
#             return False
    
#     return False

def send_document(instance_id: str, base_url: str = None, 
                 email_subject: str = None, email_message: str = None) -> bool:
    """
    Send a document to the recipient.
    Returns True if successful, False otherwise.
    
    Args:
        instance_id: The ID of the document instance to send
        base_url: Base URL for the signing link (e.g., "https://clubstride.org")
                  If None, will use the value from configuration
        email_subject: Custom email subject line (if None, uses default)
        email_message: Additional text to include in the email (if None, uses default)
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    # Find the instance
    instance = coll.find_one({"instance_id": instance_id})
    if not instance:
        return False
    
    # Find the parent document
    docs_coll = db["Documents"]
    document = docs_coll.find_one({"document_id": instance["document_id"]})
    if not document:
        return False
    
    # Mark the instance as sent
    now = datetime.utcnow()
    result = coll.update_one(
        {"instance_id": instance_id},
        {
            "$set": {
                "status": "sent",
                "sent_at": now
            },
            "$push": {
                "activity_log": {
                    "action": "sent",
                    "timestamp": now,
                    "actor_id": "system",
                    "actor_type": "system",
                    "details": "Document sent to recipient"
                }
            }
        }
    )
    
    # Send email notification (using your existing email system)
    if result.modified_count > 0:
        from mailersend import emails
        
        MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]
        mailer = emails.NewEmail(MAILERSEND_API_KEY)
        mail_body = {}
        
        mail_from = {
            "name": "Club Stride Documents",
            "email": "javier@clubstride.org"
        }
        
        recipients = [{
            "name": instance["recipient_name"],
            "email": instance["recipient_email"]
        }]
        
        # Use provided base_url or get from configuration
        if not base_url:
            # Default to configuration or environment variable
            base_url = st.session_state.get("base_url", "https://clubstride.org")
        
        # Create a document signing URL
        signing_url = f"{base_url.rstrip('/')}{instance['access_link']}"
        
        # Use custom subject if provided
        if not email_subject:
            email_subject = f"Please sign your document: {document['title']}"
        
        # Base email text with document URL if available
        document_url_section = ""
        if document.get("document_url"):
            document_url_section = f"""
            You can view the document at: {document['document_url']}

            """

            base_email_text = f"""
            Hello {instance["recipient_name"]},

            You have a document that requires your signature: {document['title']}

            {document_url_section}

            This link will expire on {instance['expiration_date'].strftime('%B %d, %Y')}.
            """
        
        # Add custom message if provided
        if email_message:
            body_text = f"{base_email_text}\n{email_message}\n\nThank you,\nClub Stride Team"
        else:
            body_text = f"{base_email_text}\n\nThank you,\nClub Stride Team"
        
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject(email_subject, mail_body)
        mailer.set_plaintext_content(body_text, mail_body)
        
        try:
            response = mailer.send(mail_body)
            print(f"MailerSend document notification response: {response}")
            return True
        except Exception as e:
            print(f"Error sending document email: {e}")
            return False
    
    return False


def update_document_status(instance_id: str, status: str, 
                          user_agent: str = None, ip_address: str = None,
                          form_data: dict = None, signature_data: dict = None,
                          declined_reason: str = None) -> bool:
    """
    Update the status of a document instance.
    Returns True if successful, False otherwise.
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    # Find the instance
    instance = coll.find_one({"instance_id": instance_id})
    if not instance:
        return False
    
    # Build the update
    now = datetime.utcnow()
    update = {
        "status": status,
        f"{status}_at": now  # Sets viewed_at, signed_at, or declined_at based on status
    }
    
    # Add additional data based on status
    if status == "signed" and signature_data:
        update["signature_data"] = {
            "signature_type": signature_data.get("type", "typed"),
            "signature_image": signature_data.get("image", ""),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": now,
            "location": signature_data.get("location", "")
        }
        
    if form_data:
        update["form_data"] = form_data
        
    if status == "declined" and declined_reason:
        update["declined_reason"] = declined_reason
    
    # Track activity
    activity = {
        "action": status,
        "timestamp": now,
        "actor_id": instance["recipient_id"],
        "actor_type": instance["recipient_type"],
        "details": f"Document {status}"
    }
    
    # Update the instance
    result = coll.update_one(
        {"instance_id": instance_id},
        {
            "$set": update,
            "$push": {"activity_log": activity}
        }
    )
    
    return result.modified_count > 0

def get_document_status_counts(document_id: str) -> dict:
    """
    Get counts of document instances by status for a specific document.
    Returns a dictionary with counts for each status.
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    pipeline = [
        {"$match": {"document_id": document_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    results = list(coll.aggregate(pipeline))
    
    # Convert to a simple dictionary
    counts = {
        "sent": 0,
        "viewed": 0,
        "signed": 0,
        "declined": 0,
        "expired": 0
    }
    
    for r in results:
        counts[r["_id"]] = r["count"]
        
    return counts
def send_reminder(instance_id: str, base_url: str = None) -> bool:
    """
    Send a reminder email for an unsigned document.
    Returns True if successful, False otherwise.
    """
    db = connect_to_db()
    coll = db["DocumentInstances"]
    
    # Find the instance
    instance = coll.find_one({"instance_id": instance_id})
    if not instance or instance["status"] in ["signed", "declined"]:
        return False
    
    # Find the parent document
    docs_coll = db["Documents"]
    document = docs_coll.find_one({"document_id": instance["document_id"]})
    if not document:
        return False
    
    # Update reminder count
    now = datetime.utcnow()
    new_reminder_count = instance.get("reminder_count", 0) + 1
    
    result = coll.update_one(
        {"instance_id": instance_id},
        {
            "$set": {
                "reminder_count": new_reminder_count,
                "last_reminder_sent": now
            },
            "$push": {
                "activity_log": {
                    "action": "reminder_sent",
                    "timestamp": now,
                    "actor_id": "system",
                    "actor_type": "system",
                    "details": f"Reminder #{new_reminder_count} sent"
                }
            }
        }
    )
    
    # Send reminder email
    if result.modified_count > 0:
        from mailersend import emails
        
        MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]
        mailer = emails.NewEmail(MAILERSEND_API_KEY)
        mail_body = {}
        
        mail_from = {
            "name": "Club Stride Documents",
            "email": "javier@clubstride.org"
        }
        
        recipients = [{
            "name": instance["recipient_name"],
            "email": instance["recipient_email"]
        }]
        
        # Use provided base_url or get from configuration
        if not base_url:
            # Default to configuration or environment variable
            base_url = st.session_state.get("base_url", "https://clubstride.org")
        
        # Create a document signing URL
        signing_url = f"{base_url.rstrip('/')}{instance['access_link']}"
        
        reminder_subject = f"REMINDER: Please sign your document: {document['title']}"
        reminder_body = f"""
Hello {instance["recipient_name"]},

This is a reminder that you have a document waiting for your signature: {document['title']}

Please click the link below to view and sign the document:
{signing_url}

This link will expire on {instance['expiration_date'].strftime('%B %d, %Y')}.

Thank you,
Club Stride Team
        """
        
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject(reminder_subject, mail_body)
        mailer.set_plaintext_content(reminder_body, mail_body)
        
        try:
            response = mailer.send(mail_body)
            print(f"MailerSend reminder response: {response}")
            return True
        except Exception as e:
            print(f"Error sending reminder email: {e}")
            return False
    
    return False

def get_documents_for_recipient(recipient_id: str, recipient_type: str) -> List[Dict]:
    """
    Get all document instances for a specific recipient.
    Returns a list of document instances with document information.
    """
    db = connect_to_db()
    instances_coll = db["DocumentInstances"]
    docs_coll = db["Documents"]
    
    # Find all instances for this recipient
    instances = list(instances_coll.find({
        "recipient_id": recipient_id,
        "recipient_type": recipient_type
    }))
    
    # Enrich with document information
    result = []
    for instance in instances:
        document = docs_coll.find_one({"document_id": instance["document_id"]})
        if document:
            # Convert ObjectIds to strings
            instance["_id"] = str(instance["_id"])
            document["_id"] = str(document["_id"])
            
            # Combine data
            result.append({
                "instance": instance,
                "document": document
            })
    
    return result


def search_documents_by_recipient(search_term: str) -> list:
    """
    Search for document instances by recipient name or email.
    Returns a list of document instances matching the search term.
    """
    db = connect_to_db()
    instances_coll = db["DocumentInstances"]
    docs_coll = db["Documents"]
    
    # Case-insensitive search on name or email
    query = {
        "$or": [
            {"recipient_name": {"$regex": search_term, "$options": "i"}},
            {"recipient_email": {"$regex": search_term, "$options": "i"}}
        ]
    }
    
    instances = list(instances_coll.find(query))
    
    # Enrich with document information
    result = []
    for instance in instances:
        document = docs_coll.find_one({"document_id": instance["document_id"]})
        if document:
            # Convert ObjectIds to strings for JSON serialization
            instance["_id"] = str(instance["_id"])
            if document.get("_id"):
                document["_id"] = str(document["_id"])
            
            # Format dates for display
            for date_field in ["sent_at", "viewed_at", "signed_at", "declined_at", "expiration_date"]:
                if instance.get(date_field):
                    if isinstance(instance[date_field], datetime):
                        instance[f"{date_field}_formatted"] = instance[date_field].strftime("%Y-%m-%d %H:%M")
            
            # Combine data
            result.append({
                "instance": instance,
                "document": document
            })
    
    return result

def delete_document(document_id: str) -> bool:
    """
    Delete a document and all its instances.
    Returns True if the document was deleted successfully, False otherwise.
    """
    db = connect_to_db()
    docs_coll = db["Documents"]
    instances_coll = db["DocumentInstances"]
    
    # First, find all instances of this document and delete them
    instances_coll.delete_many({"document_id": document_id})
    
    # Then delete the document itself
    result = docs_coll.delete_one({"document_id": document_id})
    
    return result.deleted_count > 0

def get_document_analytics() -> dict:
    """
    Generate analytics for all documents in the system.
    Returns a dictionary with various metrics.
    """
    db = connect_to_db()
    docs_coll = db["Documents"]
    instances_coll = db["DocumentInstances"]
    
    # Get total counts
    total_documents = docs_coll.count_documents({})
    total_instances = instances_coll.count_documents({})
    
    # Status distribution
    status_counts = {}
    for status in ["ready", "sent", "viewed", "signed", "declined", "expired"]:
        status_counts[status] = instances_coll.count_documents({"status": status})
    
    # Calculate completion rate (signed documents / total instances)
    completion_rate = (status_counts["signed"] / total_instances) * 100 if total_instances > 0 else 0
    
    # Documents with most views (top 5)
    pipeline = [
        {"$match": {"viewed_at": {"$ne": None}}},
        {"$group": {
            "_id": "$document_id",
            "view_count": {"$sum": 1}
        }},
        {"$sort": {"view_count": -1}},
        {"$limit": 5}
    ]
    most_viewed = list(instances_coll.aggregate(pipeline))
    
    # Enrich with document titles
    for item in most_viewed:
        doc = docs_coll.find_one({"document_id": item["_id"]})
        if doc:
            item["title"] = doc.get("title", "Untitled")
    
    # Documents with most declines (top 5)
    pipeline = [
        {"$match": {"declined_at": {"$ne": None}}},
        {"$group": {
            "_id": "$document_id",
            "decline_count": {"$sum": 1}
        }},
        {"$sort": {"decline_count": -1}},
        {"$limit": 5}
    ]
    most_declined = list(instances_coll.aggregate(pipeline))
    
    # Enrich with document titles
    for item in most_declined:
        doc = docs_coll.find_one({"document_id": item["_id"]})
        if doc:
            item["title"] = doc.get("title", "Untitled")
    
    # Average time to sign (in hours)
    pipeline = [
        {"$match": {"signed_at": {"$ne": None}, "sent_at": {"$ne": None}}},
        {"$project": {
            "sign_time": {"$subtract": ["$signed_at", "$sent_at"]}
        }},
        {"$group": {
            "_id": None,
            "avg_sign_time": {"$avg": "$sign_time"}
        }}
    ]
    avg_time_result = list(instances_coll.aggregate(pipeline))
    avg_sign_time = (avg_time_result[0]["avg_sign_time"] / (1000 * 60 * 60)) if avg_time_result else 0  # Convert ms to hours
    
    # Recently signed documents (last 7 days)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    recently_signed_count = instances_coll.count_documents({
        "signed_at": {"$gte": one_week_ago}
    })
    
    # Return analytics
    return {
        "total_documents": total_documents,
        "total_instances": total_instances,
        "status_counts": status_counts,
        "completion_rate": completion_rate,
        "most_viewed": most_viewed,
        "most_declined": most_declined,
        "avg_sign_time": avg_sign_time,
        "recently_signed_count": recently_signed_count
    }

def get_document_status_report(program_id=None, days=30):
    """
    Generate a report of document statuses for the specified program and time period.
    
    Args:
        program_id: Filter by program ID (optional)
        days: Number of days to look back (default: 30)
    
    Returns:
        List of document instances with status information
    """
    db = connect_to_db()
    instances_coll = db["DocumentInstances"]
    docs_coll = db["Documents"]
    
    # Start date for filtering
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Basic query for time period
    query = {"sent_at": {"$gte": start_date}}
    
    # Add program filter if specified
    if program_id is not None:
        # First get document IDs for the program
        program_docs = docs_coll.find({"program_id": program_id}, {"document_id": 1})
        program_doc_ids = [doc["document_id"] for doc in program_docs]
        
        # Add to query
        query["document_id"] = {"$in": program_doc_ids}
    
    # Get instances
    instances = list(instances_coll.find(query))
    
    # Enrich with document information
    result = []
    for instance in instances:
        document = docs_coll.find_one({"document_id": instance["document_id"]})
        if document:
            # Convert ObjectIds to strings
            instance["_id"] = str(instance["_id"])
            if document.get("_id"):
                document["_id"] = str(document["_id"])
            
            # Format dates for display
            for date_field in ["sent_at", "viewed_at", "signed_at", "declined_at", "expiration_date"]:
                if instance.get(date_field):
                    if isinstance(instance[date_field], datetime):
                        instance[f"{date_field}_formatted"] = instance[date_field].strftime("%Y-%m-%d %H:%M")
            
            # Add time elapsed calculations
            if instance.get("sent_at") and instance.get("signed_at"):
                time_to_sign = instance["signed_at"] - instance["sent_at"]
                instance["time_to_sign_hours"] = time_to_sign.total_seconds() / 3600
            elif instance.get("sent_at") and instance.get("viewed_at"):
                time_to_view = instance["viewed_at"] - instance["sent_at"]
                instance["time_to_view_hours"] = time_to_view.total_seconds() / 3600
            
            # Add document info
            result.append({
                "instance": instance,
                "document": document
            })
    
    return result

# Add this function to the page_manage_documents.py file

def display_document_reports():
    """Display the document reports and analytics interface."""
    st.subheader("📊 Document Reports & Analytics")
    
    # Fetch analytics data
    with st.spinner("Loading document analytics..."):
        analytics = get_document_analytics()
    
    # 1. Key Metrics Section
    st.markdown("### 📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Documents", 
            analytics["total_documents"],
            help="Total number of documents in the system"
        )
    
    with col2:
        st.metric(
            "Document Instances", 
            analytics["total_instances"],
            help="Total number of document instances sent to recipients"
        )
    
    with col3:
        st.metric(
            "Completion Rate", 
            f"{analytics['completion_rate']:.1f}%",
            help="Percentage of documents that have been signed"
        )
    
    with col4:
        st.metric(
            "Recently Signed", 
            analytics["recently_signed_count"],
            help="Documents signed in the last 7 days"
        )
    
    # 2. Status Distribution
    st.markdown("### 📊 Document Status Distribution")
    
    status_data = []
    for status, count in analytics["status_counts"].items():
        status_data.append({"status": status.capitalize(), "count": count})
    
    status_df = pd.DataFrame(status_data)
    
    if not status_df.empty:
        fig = px.bar(
            status_df,
            x="status",
            y="count",
            title="Document Status Distribution",
            color="status",
            color_discrete_map={
                "Ready": "#6c757d",
                "Sent": "#007bff",
                "Viewed": "#17a2b8",
                "Signed": "#28a745",
                "Declined": "#dc3545",
                "Expired": "#ffc107"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 3. Document Activity Report
    st.markdown("### 📋 Document Activity Report")
    
    # Program filter
    all_programs = list_programs()
    program_options = [(None, "All Programs")] + [(p["program_id"], p["program_name"]) for p in all_programs]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_program = st.selectbox(
            "Filter by Program",
            options=[po[0] for po in program_options],
            format_func=lambda pid: "All Programs" if pid is None else next((p[1] for p in program_options if p[0] == pid), "Unknown")
        )
    
    with col2:
        time_period = st.selectbox(
            "Time Period",
            options=[7, 30, 90, 365],
            format_func=lambda d: f"Last {d} days",
            index=1  # Default to 30 days
        )
    
    # Generate report based on filters
    with st.spinner("Generating document activity report..."):
        report_data = get_document_status_report(selected_program, time_period)
    
    if report_data:
        # Convert to DataFrame for easier manipulation
        rows = []
        for item in report_data:
            instance = item["instance"]
            document = item["document"]
            
            row = {
                "Document Title": document.get("title", "Untitled"),
                "Type": document.get("document_type", "").replace("_", " ").title(),
                "Recipient": instance.get("recipient_name", "Unknown"),
                "Email": instance.get("recipient_email", "Unknown"),
                "Sent Date": instance.get("sent_at_formatted", "N/A"),
                "Status": instance.get("status", "unknown").capitalize(),
                "Viewed Date": instance.get("viewed_at_formatted", "N/A"),
                "Signed Date": instance.get("signed_at_formatted", "N/A"),
                "Time to Sign (hrs)": round(instance.get("time_to_sign_hours", 0), 1) if instance.get("time_to_sign_hours") else "N/A"
            }
            rows.append(row)
        
        report_df = pd.DataFrame(rows)
        
        # Show the report table
        st.dataframe(report_df, use_container_width=True)
        
        # Allow CSV download
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Report as CSV",
            data=csv,
            file_name=f"document_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Show average time metrics
        if "Time to Sign (hrs)" in report_df.columns:
            sign_times = report_df[report_df["Time to Sign (hrs)"] != "N/A"]["Time to Sign (hrs)"]
            if not sign_times.empty:
                avg_sign_time = sign_times.mean()
                st.info(f"📊 Average time to sign a document: {avg_sign_time:.1f} hours")
    else:
        st.info("No document activity found for the selected filters.")
    
    # 4. Top Documents Section
    st.markdown("### 🔝 Top Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Most Viewed Documents")
        if analytics["most_viewed"]:
            for idx, doc in enumerate(analytics["most_viewed"]):
                st.write(f"{idx+1}. **{doc.get('title', 'Untitled')}** - {doc['view_count']} views")
        else:
            st.info("No viewed documents found.")
    
    with col2:
        st.subheader("Most Declined Documents")
        if analytics["most_declined"]:
            for idx, doc in enumerate(analytics["most_declined"]):
                st.write(f"{idx+1}. **{doc.get('title', 'Untitled')}** - {doc['decline_count']} declines")
        else:
            st.info("No declined documents found.")