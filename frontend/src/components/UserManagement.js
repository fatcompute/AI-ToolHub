import React, { useState, useEffect, useCallback, useContext } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';

function UserManagement() {
    const [users, setUsers] = useState([]);
    const [error, setError] = useState('');
    const { user: currentUser } = useContext(AuthContext);

    const fetchUsers = useCallback(async () => {
        try {
            const response = await api.get('/users');
            setUsers(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to fetch users.');
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleRoleChange = async (userId, newRole) => {
        try {
            await api.put(`/users/${userId}`, { role: newRole });
            await fetchUsers(); // Refresh the list
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to update role.');
        }
    };

    const handleDeleteUser = async (userId) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            try {
                await api.delete(`/users/${userId}`);
                await fetchUsers(); // Refresh the list
            } catch (err) {
                setError(err.response?.data?.error || 'Failed to delete user.');
            }
        }
    };

    return (
        <div className="user-management">
            <h2>User Management</h2>
            {error && <p className="error-message">{error}</p>}
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((user) => (
                        <tr key={user.id}>
                            <td>{user.username}</td>
                            <td>{user.email}</td>
                            <td>
                                <select
                                    value={user.role}
                                    onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                    disabled={user.id === currentUser.id}
                                >
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </td>
                            <td>
                                <button
                                    className="delete-button"
                                    onClick={() => handleDeleteUser(user.id)}
                                    disabled={user.id === currentUser.id}
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default UserManagement;
