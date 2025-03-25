import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const BookAppointment = () => {
  const [formData, setFormData] = useState({ name: "", age: "", date: "", doctor: "General" });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) {
      alert("You must be logged in to book an appointment.");
      return;
    }
  
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}appointments/create/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });
  
      const data = await response.json();
  
      if (response.ok) {
        navigate("/payment", { state: { formData: { ...formData, id: data.id }, amount: 500 } });
      } else {
        alert(`Error creating appointment: ${data.detail || "Unknown error"}`);
      }
    } catch (error) {
      alert("Failed to book appointment. Check your network or backend.");
    } finally {
      setLoading(false);
    }
  };
  

  return (
    <div className="container d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow p-4 w-50">
        <h2 className="text-center text-primary">Book an Appointment</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <input
              type="text"
              name="name"
              value={formData.name}
              className="form-control"
              placeholder="Name"
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <input
              type="number"
              name="age"
              value={formData.age}
              className="form-control"
              placeholder="Age"
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <input
              type="date"
              name="date"
              value={formData.date}
              className="form-control"
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <select name="doctor" value={formData.doctor} className="form-control" onChange={handleChange} required>
              <option value="General">General Physician</option>
              <option value="Cardiologist">Cardiologist</option>
              <option value="Dermatologist">Dermatologist</option>
              <option value="Neurologist">Neurologist</option>
            </select>
          </div>
          <button type="submit" className="btn btn-success w-100" disabled={loading}>
            {loading ? "Booking..." : "Proceed to Payment"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default BookAppointment;
