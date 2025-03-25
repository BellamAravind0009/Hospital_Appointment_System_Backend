import axios from "axios";

const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
});

export const createOrder = async (appointmentData, token) => {
  return await API.post("create-order/", appointmentData, {
    headers: { Authorization: `Bearer ${token}` },
  });
};

export const verifyPayment = async (paymentData, token) => {
  return await API.post("verify-payment/", paymentData, {
    headers: { Authorization: `Bearer ${token}` },
  });
};

export default API;
