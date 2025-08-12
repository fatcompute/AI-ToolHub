import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import ProtectedRoute from './ProtectedRoute';

function AdminRoute({ children }) {
    const { user, loading } = useContext(AuthContext);
    const location = useLocation();

    if (loading) {
        return <div>Loading...</div>;
    }

    if (user?.role !== 'admin') {
        // Redirect them to the home page if they are not an admin.
        // Pass a message in the state if you want to show an "Access Denied" message.
        return <Navigate to="/" state={{ from: location }} replace />;
    }

    return children;
}

// Wrap with ProtectedRoute to ensure the user is logged in first
const ProtectedAdminRoute = ({ children }) => (
    <ProtectedRoute>
        <AdminRoute>
            {children}
        </AdminRoute>
    </ProtectedRoute>
);

export default ProtectedAdminRoute;
