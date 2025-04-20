from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .serializers import RegisterSerializer, LoginSerializer, AppointmentSerializer,PatientProfileSerializer,AppointmentConfigSerializer
from .models import Appointment,PatientProfile,AppointmentConfig
from datetime import date,time
import razorpay
from razorpay.errors import BadRequestError, ServerError
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from razorpay.errors import BadRequestError, ServerError

import logging

logger = logging.getLogger(__name__)

# **1. User Authentication**
class RegisterView(generics.CreateAPIView):
    """User registration"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class LoginView(APIView):
    """User login to obtain JWT tokens"""
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProtectedView(APIView):
    """Protected API endpoint"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You have access!"})

# **2. Appointment Management**



class AppointmentConfigView(generics.RetrieveUpdateAPIView):
    """View for getting and updating appointment configuration"""
    serializer_class = AppointmentConfigSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Get the first config or create a default one
        config, created = AppointmentConfig.objects.get_or_create(id=1)
        return config

class CreateAppointmentView(generics.CreateAPIView):
    """Create new appointment and auto-assign token"""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        selected_date = serializer.validated_data['date']
        selected_time = serializer.validated_data['time']

        # Check if appointment date is not in the past
        if selected_date < date.today():
            raise serializer.ValidationError({"date": "Cannot book appointments for past dates."})

        # Check if date is Sunday
        if selected_date.weekday() == 6:
            raise serializer.ValidationError({"date": "Appointments are not available on Sundays."})
            
        # Check lunch break
        if selected_time.hour == 13:
            raise serializer.ValidationError({"time": "Appointments are not available during lunch break (1 PM to 2 PM)."})

        # Get configuration
        config = AppointmentConfig.objects.first()
        if not config:
            config = AppointmentConfig.objects.create()

        # Check daily appointment limit
        daily_count = Appointment.objects.filter(date=selected_date).count()
        if daily_count >= config.max_daily_appointments:
            raise serializer.ValidationError(
                {"date": f"Maximum appointments ({config.max_daily_appointments}) for this day have been reached."}
            )
            
        # Check hourly appointment limit
        start_hour_time = time(hour=selected_time.hour)
        end_hour_time = time(hour=selected_time.hour, minute=59, second=59)
        
        hourly_count = Appointment.objects.filter(
            date=selected_date,
            time__gte=start_hour_time,
            time__lte=end_hour_time
        ).count()
        
        if hourly_count >= config.max_per_hour:
            raise serializer.ValidationError({
                "time": f"Maximum appointments ({config.max_per_hour}) for this hour have been reached. Please select a different time."
            })

        # Use transaction to prevent race conditions
        from django.db import transaction
        with transaction.atomic():
            # Count all appointments on the selected date
            existing_appointments = Appointment.objects.filter(date=selected_date).count()
            token_number = existing_appointments + 1

            # Assign the logged-in user to the appointment
            serializer.save(user=self.request.user, token_number=token_number)

class UpdateAppointmentView(APIView):
    """Update appointment date and reassign token"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        appointment_id = request.data.get('id')
        new_date_str = request.data.get('date')
        new_time_str = request.data.get('time')

        if not appointment_id or not new_date_str or not new_time_str:
            return Response({"error": "Appointment ID, new date, and new time are required"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get appointment
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
            
            # Convert string to date and time objects
            from datetime import datetime
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            new_time = datetime.strptime(new_time_str, '%H:%M').time()
            
            # Validate date and time
            if new_date < date.today():
                return Response({"error": "Appointment date cannot be in the past"}, 
                                status=status.HTTP_400_BAD_REQUEST)
                                
            # Check if date is Sunday
            if new_date.weekday() == 6:
                return Response({"error": "Appointments are not available on Sundays"}, 
                                status=status.HTTP_400_BAD_REQUEST)
                                
            # Check lunch break
            if new_time.hour == 13:
                return Response({"error": "Appointments are not available during lunch break (1 PM to 2 PM)"}, 
                                status=status.HTTP_400_BAD_REQUEST)
                
            # Get configuration
            config = AppointmentConfig.objects.first()
            if not config:
                config = AppointmentConfig.objects.create()
                
            # Check if there are any changes
            if appointment.date == new_date and appointment.time == new_time:
                return Response({"message": "No changes made", "appointment": AppointmentSerializer(appointment).data}, 
                                status=status.HTTP_200_OK)
                
            # Check daily appointment limit
            daily_count = Appointment.objects.filter(date=new_date).exclude(id=appointment_id).count()
            if daily_count >= config.max_daily_appointments:
                return Response(
                    {"error": f"Maximum appointments ({config.max_daily_appointments}) for this day have been reached"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check hourly appointment limit
            start_hour_time = time(hour=new_time.hour)
            end_hour_time = time(hour=new_time.hour, minute=59, second=59)
            
            hourly_count = Appointment.objects.filter(
                date=new_date,
                time__gte=start_hour_time,
                time__lte=end_hour_time
            ).exclude(id=appointment_id).count()
            
            if hourly_count >= config.max_per_hour:
                return Response({
                    "error": f"Maximum appointments ({config.max_per_hour}) for this hour have been reached. Please select a different time."
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValueError:
            return Response({"error": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Use transaction to prevent race conditions when updating token
        from django.db import transaction
        with transaction.atomic():
            appointment.date = new_date
            appointment.time = new_time
            appointment.save()

        return Response({"message": "Appointment updated successfully", "appointment": AppointmentSerializer(appointment).data}, 
                        status=status.HTTP_200_OK)


class ViewAppointmentsView(generics.ListAPIView):
    """View only the logged-in user's appointments"""
    serializer_class = AppointmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

# **3. Payment Integration**
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    """Create a Razorpay order but do NOT finalize booking yet"""
    try:
        amount = request.data.get("amount")
        appointment_id = request.data.get("appointment_id")

        if not amount or not str(amount).isdigit() or int(amount) <= 0:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        if not appointment_id:
            return JsonResponse({"error": "Appointment ID is required"}, status=400)

        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        except:
            return JsonResponse({"error": "Invalid appointment"}, status=404)

        # Check if payment is already in progress or completed
        if appointment.payment_status == "Paid":
            return JsonResponse({"error": "Appointment is already paid for"}, status=400)

        amount = int(amount) * 100  # Convert to paise
        currency = "INR"

        try:
            razorpay_order = razorpay_client.order.create({
                "amount": amount,
                "currency": currency,
                "payment_capture": "1"
            })
        except BadRequestError as e:
            return JsonResponse({"error": f"Razorpay error: {str(e)}"}, status=400)
        except ServerError as e:
            return JsonResponse({"error": "Razorpay server error. Please try again later."}, status=503)

        # Store order ID but DO NOT finalize booking yet
        appointment.payment_id = razorpay_order.get("id")
        appointment.payment_status = "Pending"
        appointment.save()

        return JsonResponse({
            "order_id": razorpay_order.get("id", ""),
            "amount": amount,
            "currency": currency,
            "status": razorpay_order.get("status", "failed")
        })

    except Exception as e:
        logger.error(f"Error in create_razorpay_order: {str(e)}")
        return JsonResponse({"error": "An unexpected error occurred. Please try again."}, status=500)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify Razorpay payment and confirm appointment booking"""
    try:
        order_id = request.data.get("order_id")
        payment_id = request.data.get("payment_id")
        signature = request.data.get("signature")

        if not order_id or not payment_id or not signature:
            return JsonResponse({"error": "Missing payment details"}, status=400)

        appointment = get_object_or_404(Appointment, payment_id=order_id, user=request.user)

        # Verify payment using Razorpay SDK
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            appointment.payment_status = "Paid"
            appointment.save()

            # Return appointment details for the confirmation page
            appointment_data = {
                "name": appointment.name,
                "age": appointment.age,
                "date": appointment.date,
                "department": appointment.department,
                "doctor": appointment.doctor,
                "token_number": appointment.token_number,
            }

            return JsonResponse({"message": "Payment successful", "appointment": appointment_data}, status=200)

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Payment verification failed"}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Internal error: {e}"}, status=500)


#profile management 


class PatientProfileView(generics.ListCreateAPIView):
    """Create and list patient profiles"""
    serializer_class = PatientProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PatientProfile.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PatientProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a patient profile using profile_name"""
    serializer_class = PatientProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'profile_name'  
    
    def get_queryset(self):
        return PatientProfile.objects.filter(user=self.request.user)

class GetProfileForAppointmentView(APIView):
    """Fetch profile data for use in appointment booking using profile_name"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, profile_name):
        try:
            profile = PatientProfile.objects.get(profile_name=profile_name, user=request.user)
            return Response({
                "name": profile.patient_name,
                "age": profile.age,
                "sex": profile.sex
            }, status=status.HTTP_200_OK)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        


class CancelAppointmentView(generics.DestroyAPIView):
    """Cancel an appointment"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Appointment.objects.all()
    
    def get_queryset(self):
        # Ensure users can only cancel their own appointments
        return Appointment.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if appointment is in the past
        if instance.date < date.today():
            return Response(
                {"error": "Cannot cancel past appointments"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if appointment is today
        if instance.date == date.today():
            # You might want to add additional logic here
            # For example, not allowing cancellation if it's too close to the appointment time
            pass
            
        # Perform the deletion
        self.perform_destroy(instance)
        return Response(
            {"message": "Appointment cancelled successfully"}, 
            status=status.HTTP_200_OK
        )