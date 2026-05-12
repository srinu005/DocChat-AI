from celery import shared_task
from .models import Document
from .services import ingest_document

@shared_task
def process_document_task(doc_id):
    try:
        doc = Document.objects.get(id=doc_id)
        doc.status = 'processing'
        doc.save()

        # Call our service
        success = ingest_document(
            document_path=doc.file.path,
            document_id=doc.id,
            user_id=doc.user.id
        )

        if success:
            doc.status = 'ready'
        else:
            doc.status = 'error'
        
        doc.save()
    except Exception as e:
        print(f"Error processing document: {e}")
        doc = Document.objects.get(id=doc_id)
        doc.status = 'error'
        doc.save()