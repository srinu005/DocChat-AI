import pytest
from django.urls import reverse
from documents.models import Document

@pytest.mark.django_db
def test_index_page_requires_login(client):
    """Verify that the index page redirects to login if not authenticated."""
    url = reverse('index')
    response = client.get(url)
    assert response.status_code == 302
    assert '/admin/login/' in response.url

@pytest.mark.django_db
def test_authenticated_user_can_access_index(admin_client):
    """Verify that a logged-in user can see the dashboard."""
    url = reverse('index')
    response = admin_client.get(url)
    assert response.status_code == 200
    assert b"TalkToDoc AI" in response.content

@pytest.mark.django_db
def test_document_creation(admin_user):
    """Test that the Document model works correctly."""
    doc = Document.objects.create(
        user=admin_user,
        title="Test PDF",
        status="uploaded"
    )
    assert doc.title == "Test PDF"
    assert Document.objects.count() == 1