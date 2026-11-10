from django.db import models
from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    record_count = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)

class VehicleRecord(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='records')
    time = models.CharField(max_length=50)
    vehicle_class = models.CharField(max_length=100)
    x = models.FloatField()
    y = models.FloatField()
