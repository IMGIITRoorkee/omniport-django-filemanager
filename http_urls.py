from django.conf.urls import url
from django.urls import path
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
    path(r'shared_item/<str:uuid>/<str:item1>/<int:id>/<str:item2>/', ItemSharedView.as_view(), name='shared_item'),
    path(r'all_shared_items/', AllSharedItems.as_view(), name='all_shared_items'),
    path(r'all_starred_items/', AllStarredItems.as_view(), name='all_starred_items')
] + static(settings.MEDIA_URL, document_root = settings.PERSONAL_ROOT)

urlpatterns += router.urls
