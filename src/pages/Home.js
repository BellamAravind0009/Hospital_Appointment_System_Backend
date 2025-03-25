import React from "react";
import { useNavigate } from "react-router-dom";
import { FaBook, FaEdit, FaEye, FaSignOutAlt } from "react-icons/fa";
import "bootstrap/dist/css/bootstrap.min.css";

const Home = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return (
    <div className="d-flex align-items-center justify-content-center vh-100 bg-light">
      <div className="card shadow-lg p-5 border-0 rounded-4 text-center" style={{ maxWidth: "400px" }}>
        <h1 className="fw-bold text-primary">Welcome</h1>
        <p className="text-muted">Manage your hospital appointments easily.</p>

        <div className="d-grid gap-3 mt-4">
          <button onClick={() => navigate("/book")} className="btn btn-success btn-lg d-flex align-items-center justify-content-center gap-2">
            <FaBook /> Book Appointment
          </button>
          <button onClick={() => navigate("/update")} className="btn btn-warning btn-lg d-flex align-items-center justify-content-center gap-2">
            <FaEdit /> Alter Appointment
          </button>
          <button onClick={() => navigate("/appointments")} className="btn btn-info btn-lg d-flex align-items-center justify-content-center gap-2">
            <FaEye /> View Appointments
          </button>
          <button onClick={handleLogout} className="btn btn-danger btn-lg d-flex align-items-center justify-content-center gap-2">
            <FaSignOutAlt /> Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Home;
