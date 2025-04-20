from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class AppointmentConfig(models.Model):
    """Configuration for appointment limits and restrictions"""
    max_daily_appointments = models.PositiveIntegerField(default=30)
    max_per_hour = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Appointment Config (Last updated: {self.updated_at})"
    
    class Meta:
        verbose_name = "Appointment Configuration"
        verbose_name_plural = "Appointment Configurations"

class Appointment(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES,default='O')
    date = models.DateField()
    time = models.TimeField(default="09:00:00")
    department = models.CharField(max_length=255, default='General Medicine')
    doctor = models.CharField(max_length=255) 
    token_number = models.PositiveIntegerField(blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=[("Pending", "Pending"), ("Paid", "Paid")], default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date} {self.time} (Token: {self.token_number})"

@receiver(pre_save, sender=Appointment)
def assign_token(sender, instance, **kwargs):
    if not instance.token_number:
        from django.db import transaction
        with transaction.atomic():
            # Get the highest token number for that date and increment
            highest_token = Appointment.objects.filter(date=instance.date).order_by('-token_number').first()
            instance.token_number = (highest_token.token_number + 1) if highest_token else 1

# Profile management
class PatientProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_profiles')
    profile_name = models.CharField(max_length=100)  # A unique name to identify this profile
    patient_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=Appointment.SEX_CHOICES, default='O')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'profile_name']  # Ensure profile names are unique per user

    def __str__(self):
        return f"{self.profile_name} - {self.patient_name}"