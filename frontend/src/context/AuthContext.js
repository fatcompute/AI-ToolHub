import React, { createContext, useState, useEffect, useCallback } from 'react';
import api from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    const fetchUserProfile = useCallback(async () => {
        // The interceptor will add the token
        try {
            const response = await api.get('/auth/profile');
            setUser(response.data);
        } catch (error) {
            console.error("Failed to fetch user profile", error);
            logout(); // Log out if token is invalid or request fails
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (token) {
            fetchUserProfile();
        } else {
            setLoading(false);
        }
    }, [token, fetchUserProfile]);

    const login = async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        setToken(access_token);
        // The useEffect will trigger fetchUserProfile
    };

    const register = async (username, email, password) => {
        await api.post('/auth/register', { username, email, password });
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('token');
    };

    const refreshUser = () => {
        if (token) {
            fetchUserProfile();
        }
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, register, loading, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};
