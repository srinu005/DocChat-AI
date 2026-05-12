__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Model & Task Imports
from .models import Document, ChatMessage
from .tasks import process_document_task

# MODERN LANGCHAIN (LCEL) IMPORTS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

@login_required
def index(request):
    """
    Main Dashboard. Shows user documents and chat history.
    """
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    active_doc = None
    chats = []
    
    doc_id = request.GET.get('doc_id')
    if doc_id:
        active_doc = get_object_or_404(Document, id=doc_id, user=request.user)
        chats = active_doc.messages.all().order_by('timestamp')

    return render(request, 'index.html', {
        'documents': documents,
        'active_doc': active_doc,
        'chats': chats
    })

@login_required
def upload_document(request):
    """
    Handles PDF upload and triggers the background Celery task.
    """
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            return HttpResponse("No file uploaded", status=400)

        # 1. Save document to DB
        doc = Document.objects.create(
            user=request.user, 
            file=file, 
            title=file.name
        )
        
        # 2. Trigger Celery Task (Asynchronous)
        process_document_task.delay(doc.id)
        
        # 3. Return the HTMX partial for the sidebar
        return render(request, 'partials/doc_item.html', {'doc': doc})

@login_required
def ask_question(request, doc_id):
    if request.method == 'POST':
        question = request.POST.get('question')
        doc = get_object_or_404(Document, id=doc_id, user=request.user)

        # 1. Setup Gemini
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )

        # 2. Load Vector DB
        vector_db = Chroma(persist_directory="./vector_db", embedding_function=embeddings)
        retriever = vector_db.as_retriever(search_kwargs={"filter": {"document_id": doc_id}})

        # 3. Define the Prompt
        template = """Answer the question based only on the following context:
        {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        # 4. THE LCEL CHAIN (This replaces create_retrieval_chain)
        # This is a pipe-line: Context -> Prompt -> LLM -> Text
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        # 5. Execute
        try:
            ai_response = rag_chain.invoke(question)
        except Exception as e:
            ai_response = f"AI Error: {str(e)}"

        # 6. Save and Return
        chat = ChatMessage.objects.create(
            document=doc, 
            user_question=question, 
            ai_response=ai_response
        )
        return render(request, 'partials/chat_snippet.html', {'chat': chat})