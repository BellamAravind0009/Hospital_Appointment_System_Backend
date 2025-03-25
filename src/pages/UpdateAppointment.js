import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

const UpdateAppointment = () => {
  const navigate = useNavigate();
  const [name, setName] = useState(""); // User enters name
  const [appointment, setAppointment] = useState(null); // Store appointment details
  const [newDate, setNewDate] = useState(""); // Store new date input

  const fetchAppointment = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}appointments/view/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
  
      const foundAppointment = response.data.find((appt) => appt.name === name);
      if (!foundAppointment) {
        alert("No appointment found for this name.");
        return;
      }
  
      setAppointment(foundAppointment);
    } catch (error) {
      alert("Error fetching appointment details");
    }
  };
  

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!appointment || !newDate) {
      alert("Please enter a valid name and new date.");
      return;
    }

    try {
      const response = await axios.put(
        `http://127.0.0.1:8000/api/appointments/update/`, // No ID in URL
        { name: appointment.name, date: newDate }, // Send name and new date
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );

      alert("Appointment updated successfully!");
      navigate("/appointments");
    } catch (error) {
      alert(error.response?.data?.error || "Error updating appointment");
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow p-4 w-50">
        <h2 className="text-center text-primary">Update Appointment</h2>

        {/* Step 1: Enter Name */}
        <div className="mb-3">
          <input
            type="text"
            className="form-control"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button className="btn btn-info mt-2 w-100" onClick={fetchAppointment}>
            Fetch Appointment
          </button>
        </div>

        {/* Step 2: Show Appointment Details if Found */}
        {appointment && (
          <form onSubmit={handleUpdate}>
            <div className="mb-3">
              <label>Current Date</label>
              <input type="date" className="form-control" value={appointment.date} disabled />
            </div>

            <div className="mb-3">
              <label>New Date</label>
              <input
                type="date"
                className="form-control"
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-warning w-100">
              Update Appointment
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default UpdateAppointment;
