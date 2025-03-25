import React, { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { createOrder, verifyPayment } from "../api"; // Ensure these functions exist in api.js

const Payment = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { formData, amount } = location.state || {}; // Extract appointment data

  const token = localStorage.getItem("token"); // Get auth token

  useEffect(() => {
    if (!formData || !amount) {
      alert("Invalid appointment details!");
      navigate("/home");
    }
  }, [formData, amount, navigate]);

  const handlePayment = async () => {
    try {
      const orderResponse = await createOrder(
        { amount, appointment_id: formData.id }, 
        token
      );

      const { order_id, amount: orderAmount, currency } = orderResponse.data;

      const options = {
        key: "rzp_test_RjiPloZTcFARKZ",
        amount: orderAmount,
        currency,
        name: "Hospital System",
        description: "Appointment Payment",
        order_id,
        handler: async function (response) {
          try {
            const verifyResponse = await verifyPayment(
              {
                order_id: response.razorpay_order_id,
                payment_id: response.razorpay_payment_id,
                signature: response.razorpay_signature,
              },
              token
            );

            if (verifyResponse.status === 200) {
              alert("Payment successful! Appointment booked.");
              navigate("/home");
            } else {
              alert("Payment verification failed.");
            }
          } catch (error) {
            alert("Error verifying payment.");
          }
        },
        prefill: { name: formData.name, email: "your@email.com", contact: "9999999999" },
        theme: { color: "#3399cc" },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();

      razorpay.on("payment.failed", function () {
        alert("Payment Failed! Please try again.");
      });

    } catch (error) {
      console.error("Payment Error:", error);
      alert("Error processing payment");
    }
  };

  return (
    <div className="container text-center">
      <h2>Complete Your Payment</h2>
      <button onClick={handlePayment} className="btn btn-primary">
        Pay ₹{amount}
      </button>
    </div>
  );
};

export default Payment;
