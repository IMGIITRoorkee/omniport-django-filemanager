from django.conf.urls import url
from django_filemanager.views import *
from rest_framework import routers

app_name = 'django_filemanager'

router = routers.SimpleRouter()

router.register(r'folder', FolderViewSet, 'Folder')

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
    url(r'media_files/', FileAccessView.as_view()),
    url(r'edit_file/(?P<pk>[0-9]+)/$', file_edit),
    url(r'delete_file/(?P<pk>[0-9]+)/$', file_delete),
    url(r'upload/', file_view)
]
urlpatterns += router.urls
