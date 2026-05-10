
# Create your views here.
from django.shortcuts import render, redirect
from .models import Document, ChatMessage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def index(request):
    documents = Document.objects.filter(user=request.user) if request.user.is_authenticated else []
    active_doc = None
    chats = []
    
    doc_id = request.GET.get('doc_id')
    if doc_id:
        active_doc = Document.objects.get(id=doc_id)
        chats = active_doc.messages.all()

    return render(request, 'index.html', {
        'documents': documents,
        'active_doc': active_doc,
        'chats': chats
    })

def upload_document(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        # We will manually assign a user for now, or use request.user if logged in
        doc = Document.objects.create(user=request.user, file=file, title=file.name)
        
        # This is where we will trigger Celery later!
        return render(request, 'partials/doc_item.html', {'doc': doc})

def ask_question(request, doc_id):
    if request.method == 'POST':
        question = request.POST.get('question')
        doc = Document.objects.get(id=doc_id)
        
        # Dummy AI Response for now
        ai_response = f"I will analyze the document for: '{question}' as soon as we connect LangChain!"
        
        chat = ChatMessage.objects.create(document=doc, user_question=question, ai_response=ai_response)
        
        return render(request, 'partials/chat_snippet.html', {'chat': chat})
    

# In documents/views.py


@login_required # This forces the user to log in via /admin first
def index(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    active_doc = None
    chats = []
    
    doc_id = request.GET.get('doc_id')
    if doc_id:
        active_doc = Document.objects.get(id=doc_id, user=request.user)
        chats = active_doc.messages.all()

    return render(request, 'index.html', {
        'documents': documents,
        'active_doc': active_doc,
        'chats': chats
    })


