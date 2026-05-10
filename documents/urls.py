from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload_document'),
    path('ask/<int:doc_id>/', views.ask_question, name='ask_question'),
]