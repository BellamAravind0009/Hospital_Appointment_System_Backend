import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import BookAppointment from "./pages/BookAppointment";
import ViewAppointments from "./pages/ViewAppointments";
import UpdateAppointment from "./pages/UpdateAppointment";
import Navbar from "./components/Navbar";
import Payment from "./pages/payment";

// Authentication check
const isAuthenticated = () => !!localStorage.getItem("token");

const ProtectedRoute = ({ element }) => {
  return isAuthenticated() ? element : <Navigate to="/login" />;
};

function App() {
  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute element={<Home />} />} />
        <Route path="/book" element={<ProtectedRoute element={<BookAppointment />} />} />
        <Route path="/appointments" element={<ProtectedRoute element={<ViewAppointments />} />} />
        <Route path="/update" element={<ProtectedRoute element={<UpdateAppointment />} />} />
        <Route path="/payment" element={<ProtectedRoute element={<Payment />} />} />  {/* ✅ Protected */}
      </Routes>
    </div>
  );
}

export default App;
