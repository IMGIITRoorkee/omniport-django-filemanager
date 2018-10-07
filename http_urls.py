from django.conf.urls import url
from django_filemanager.views import *

app_name = 'django_filemanager'


folder = FolderViewSet.as_view({
    'get': 'list',
})

file_view = FileUploadView.as_view({
    'post': 'create',
})

urlpatterns = [
    url(r'folder/', folder),
    url(r'media_files/', FileView.as_view()),
    url(r'upload/', file_view)
]
