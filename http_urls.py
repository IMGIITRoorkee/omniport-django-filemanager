from django.conf.urls import url
from django_filemanager.views import *

app_name = 'django_filemanager'


folder = FolderViewSet.as_view({
    'get': 'list',
})

file_view = FileView.as_view({
    'post': 'create',
})

file_edit = FileView.as_view({
    'put': 'update',
})

file_delete = FileView.as_view({
    'delete': 'destroy',
})

urlpatterns = [
    url(r'folder/', folder),
    url(r'media_files/', FileAccessView.as_view()),
    url(r'edit_file/(?P<pk>[0-9]+)/$', file_edit),
    url(r'delete_file/(?P<pk>[0-9]+)/$', file_delete),
    url(r'upload/', file_view)
]
