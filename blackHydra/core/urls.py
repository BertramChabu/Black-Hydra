from django.urls import path
from .views import start_scan, scan_status, list_scans

urlpatterns = [
    path('scan/', start_scan),
    path('scan/<int:scan_id>/', scan_status),
    path('scans/', list_scans),

]
