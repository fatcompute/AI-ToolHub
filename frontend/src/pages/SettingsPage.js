import React, { useContext, useState, useEffect } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import { AuthContext } from '../context/AuthContext';
import api from '../api';

function SettingsPage() {
    const { theme, toggleTheme } = useContext(ThemeContext);
    const { user, refreshUser } = useContext(AuthContext);

    // State for default training parameters
    const [defaultEpochs, setDefaultEpochs] = useState(1);
    const [defaultBatchSize, setDefaultBatchSize] = useState(1);
    const [settingsMessage, setSettingsMessage] = useState('');

    // State for system config (admin only)
    const [systemConfig, setSystemConfig] = useState(null);

    useEffect(() => {
        if (user?.settings) {
            setDefaultEpochs(user.settings.default_epochs || 1);
            setDefaultBatchSize(user.settings.default_batch_size || 1);
        }
        // Fetch system config if user is admin
        if (user?.role === 'admin') {
            const fetchConfig = async () => {
                try {
                    const response = await api.get('/system/config');
                    setSystemConfig(response.data);
                } catch (error) {
                    console.error("Failed to fetch system config", error);
                }
            };
            fetchConfig();
        }
    }, [user]);

    const handleSaveTrainingSettings = async (e) => {
        e.preventDefault();
        setSettingsMessage('Saving...');
        try {
            const settings = {
                default_epochs: parseInt(defaultEpochs, 10),
                default_batch_size: parseInt(defaultBatchSize, 10),
            };
            await api.put('/users/settings', { settings });
            setSettingsMessage('Settings saved successfully!');
            refreshUser(); // Refresh user context to get new settings
        } catch (error) {
            setSettingsMessage('Failed to save settings.');
        }
    };

    return (
        <div className="settings-page">
            <h2>Settings</h2>

            <div className="settings-section">
                <h3>Theme</h3>
                <p>Current Mode: <strong>{theme}</strong></p>
                <button onClick={toggleTheme}>
                    Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
                </button>
            </div>

            <div className="settings-section">
                <h3>Default Training Parameters</h3>
                <form onSubmit={handleSaveTrainingSettings}>
                    <label>Default Epochs</label>
                    <input
                        type="number"
                        value={defaultEpochs}
                        onChange={e => setDefaultEpochs(e.target.value)}
                        min="1"
                    />
                    <label>Default Batch Size</label>
                    <input
                        type="number"
                        value={defaultBatchSize}
                        onChange={e => setDefaultBatchSize(e.target.value)}
                        min="1"
                    />
                    <button type="submit">Save Defaults</button>
                    {settingsMessage && <p>{settingsMessage}</p>}
                </form>
            </div>

            {user?.role === 'admin' && systemConfig && (
                <div className="settings-section">
                    <h3>System Configuration (Admin View)</h3>
                    <div className="config-item">
                        <strong>Models Directory:</strong>
                        <code>{systemConfig.models_dir}</code>
                    </div>
                    <div className="config-item">
                        <strong>Datasets Directory:</strong>
                        <code>{systemConfig.upload_folder}</code>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SettingsPage;
