import React, { useEffect, useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL; // Dynamically set API URL

const ViewAppointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          setError("Unauthorized: Please log in.");
          setLoading(false);
          return;
        }

        const response = await axios.get(`${API_BASE_URL}appointments/view/`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        setAppointments(response.data);
      } catch (err) {
        setError("Error fetching appointments. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  return (
    <div className="container mt-5">
      <h2 className="text-center text-primary mb-4">Your Appointments</h2>

      {loading ? (
        <p className="text-center text-muted">Loading...</p>
      ) : error ? (
        <p className="text-center text-danger">{error}</p>
      ) : appointments.length === 0 ? (
        <p className="text-center text-muted">No appointments found.</p>
      ) : (
        <table className="table table-striped shadow">
          <thead className="table-dark">
            <tr>
              <th>Name</th>
              <th>Doctor</th>
              <th>Date</th>
              <th>Token Number</th>
            </tr>
          </thead>
          <tbody>
            {appointments.map((appt) => (
              <tr key={appt.id}>
                <td>{appt.name}</td>
                <td>{appt.doctor}</td>
                <td>{appt.date}</td>
                <td>{appt.token_number}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ViewAppointments;
