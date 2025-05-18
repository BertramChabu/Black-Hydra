from django.db import models

# Create your models here.
class ScanResult(models.Model):
    target = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default="pending")
    result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.target} ({self.status})"
    