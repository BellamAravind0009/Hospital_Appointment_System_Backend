from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    date = models.DateField()
    doctor = models.CharField(max_length=255, default="General") 
    token_number = models.PositiveIntegerField(blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Paid", "Paid")], default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date} (Token: {self.token_number})"

@receiver(pre_save, sender=Appointment)
def assign_token(sender, instance, **kwargs):
    if not instance.token_number:
        today_appointments = Appointment.objects.filter(date=instance.date).count()
        instance.token_number = today_appointments + 1
