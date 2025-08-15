import React from 'react';
import { Link } from 'react-router-dom'; // This will be removed, but keeping for now to avoid breaking the build

function Header() {
    return (
        <header className="App-header">
            <div className="header-content">
                {/* The Link will be replaced with a simple 'a' tag or just text, as routing is removed */}
                <a href="/" className="logo"><h1>AI Toolkit</h1></a>
                <nav>
                    {/* All user-specific navigation is removed */}
                </nav>
            </div>
        </header>
    );
}

export default Header;
