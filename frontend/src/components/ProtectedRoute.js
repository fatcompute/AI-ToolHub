import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function ProtectedRoute({ children }) {
    const { token, loading } = useContext(AuthContext);
    const location = useLocation();

    if (loading) {
        // Show a loading spinner or a blank page while checking auth status
        return <div>Loading...</div>;
    }

    if (!token) {
        // Redirect them to the /login page, but save the current location they were
        // trying to go to. This allows us to send them back to that page after they log in.
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
}

export default ProtectedRoute;
