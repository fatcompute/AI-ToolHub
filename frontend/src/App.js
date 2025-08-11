import React, { useContext } from 'react';
import { Routes, Route } from 'react-router-dom';
import './App.css';
import { ThemeContext } from './context/ThemeContext';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SettingsPage from './pages/SettingsPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const { theme } = useContext(ThemeContext);

  // The ThemeProvider in index.js already adds the class to document.body,
  // but we can add it here as well for component-level scoping if needed.
  // For now, we'll just use the context to demonstrate it's working.
  return (
    <div className={`App ${theme}`}>
      <Header />
      <main className="App-main">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
          />
          <Route
            path="/settings"
            element={<ProtectedRoute><SettingsPage /></ProtectedRoute>}
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
