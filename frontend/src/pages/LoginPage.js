import React, { useState, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useContext(AuthContext);
    const navigate = useNavigate();
    const location = useLocation();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await login(username, password);
            const from = location.state?.from?.pathname || "/";
            navigate(from, { replace: true });
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to log in. Please check your credentials.');
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-form">
                <h2>Login or Create Account</h2>
                <p>Enter a username and password. If the account doesn't exist, it will be created for you.</p>
                {error && <p className="error-message">{error}</p>}
                <form onSubmit={handleSubmit}>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Username"
                        required
                    />
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                        required
                    />
                    <button type="submit">Continue</button>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;
