from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .serializers import RegisterSerializer, LoginSerializer, AppointmentSerializer
from .models import Appointment

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
class CreateAppointmentView(generics.CreateAPIView):
    """Create new appointment and auto-assign token"""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        selected_date = serializer.validated_data['date']

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
        name = request.data.get('name')  
        new_date = request.data.get('date')

        if not name or not new_date:
            return Response({"error": "Name and new date are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the user's appointment by name
        appointment = Appointment.objects.filter(name=name, user=request.user).first()

        if not appointment:
            return Response({"error": "No appointment found for this user with this name"}, status=status.HTTP_404_NOT_FOUND)

        # If the new date is same as current date, return early
        if appointment.date == new_date:
            return Response({"message": "No changes made", "appointment": AppointmentSerializer(appointment).data}, status=status.HTTP_200_OK)

        # **Ensure unique token numbers per date**
        existing_appointments = Appointment.objects.filter(date=new_date)
        new_token_number = existing_appointments.count() + 1

        # Update the appointment
        appointment.date = new_date
        appointment.token_number = new_token_number
        appointment.save()

        return Response(
            {"message": "Appointment updated successfully", "appointment": AppointmentSerializer(appointment).data},
            status=status.HTTP_200_OK
        )

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

        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

        amount = int(amount) * 100  # Convert to paise
        currency = "INR"

        razorpay_order = razorpay_client.order.create({
            "amount": amount,
            "currency": currency,
            "payment_capture": "1"
        })

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
        return JsonResponse({"error": f"Internal error: {e}"}, status=500)



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

            return JsonResponse({"message": "Payment successful, appointment booked!"}, status=200)

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Payment verification failed"}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Internal error: {e}"}, status=500)
