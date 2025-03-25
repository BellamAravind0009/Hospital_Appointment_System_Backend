from django.urls import path
from .views import (
    RegisterView, LoginView, ProtectedView,
    CreateAppointmentView, UpdateAppointmentView, ViewAppointmentsView,create_razorpay_order,verify_payment
)

urlpatterns = [
    # Authentication routes
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('protected/', ProtectedView.as_view(), name='protected'),

    # Appointment routes
    path('appointments/create/', CreateAppointmentView.as_view(), name='create-appointment'),
    path('appointments/update/', UpdateAppointmentView.as_view(), name='update-appointment'),
    path('appointments/view/', ViewAppointmentsView.as_view(), name='view-appointment'),



    path("create-order/", create_razorpay_order, name="create-razorpay-order"),
    path("verify-payment/", verify_payment, name="verify-payment"),

]
