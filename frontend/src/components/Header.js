import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Header() {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="App-header">
            <div className="header-content">
                <Link to="/" className="logo"><h1>AI Toolkit</h1></Link>
                <nav>
                    {user && (
                        <>
                            <Link to="/">Dashboard</Link>
                            <Link to="/settings">Settings</Link>
                            {user.role === 'admin' && <Link to="/code-health">Code Health</Link>}
                            <span className="user-info">
                                Welcome, {user.username} ({user.role})
                            </span>
                            <button onClick={handleLogout} className="logout-button">Logout</button>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}

export default Header;
