from django.conf.urls import url
from django_filemanager.views import *
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

app_name = 'django_filemanager'

router = routers.SimpleRouter()

router.register(r'folder', FolderViewSet, 'Folder')
router.register(r'filemanager', FileManagerViewSet, 'FileManager')
router.register(r'files', FileView, 'file')

urlpatterns = [
    url(r'media_files/', FileAccessView.as_view()),
] + static(settings.MEDIA_URL, document_root = settings.PERSONAL_ROOT)

urlpatterns += router.urls
