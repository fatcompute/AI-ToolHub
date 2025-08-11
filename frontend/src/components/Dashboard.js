import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import TrainingDashboard from './TrainingDashboard';
import UserManagement from './UserManagement';
import api from '../api';

function Dashboard() {
    const { user, logout } = useContext(AuthContext);

    // State for model management
    const [models, setModels] = useState([]);
    const [newModelId, setNewModelId] = useState('');
    const [isDownloading, setIsDownloading] = useState(false);
    const [managementError, setManagementError] = useState('');

    // State for chat
    const [selectedModel, setSelectedModel] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [chatError, setChatError] = useState('');

    const fetchModels = useCallback(async () => {
        try {
            const response = await api.get('/models');
            setModels(response.data);
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to fetch models.');
        }
    }, []);

    useEffect(() => {
        fetchModels();
    }, [fetchModels]);

    const handleDownloadModel = async (e) => {
        e.preventDefault();
        if (!newModelId) {
            setManagementError('Please enter a Hugging Face Model ID.');
            return;
        }
        setIsDownloading(true);
        setManagementError('');
        try {
            await api.post('/models/download', { huggingface_id: newModelId });
            setNewModelId('');
            await fetchModels(); // Refresh the model list
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to download model.');
        } finally {
            setIsDownloading(false);
        }
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!prompt || !selectedModel) {
            setChatError('Please select a model and enter a prompt.');
            return;
        }
        setIsGenerating(true);
        setChatError('');

        const newHistory = [...chatHistory, { role: 'user', content: prompt }];
        setChatHistory(newHistory);
        setPrompt('');

        try {
            const response = await api.post('/chat', { model_id: selectedModel.id, prompt: prompt });
            setChatHistory([...newHistory, { role: 'bot', content: response.data.response }]);
        } catch (error) {
            setChatError(error.response?.data?.error || 'Failed to get response.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <>
            <div className="dashboard-grid">
                <div className="model-management">
                    <h2>Model Management</h2>
                    {managementError && <p className="error-message">{managementError}</p>}
                <form onSubmit={handleDownloadModel} className="download-form">
                    <input
                        type="text"
                        value={newModelId}
                        onChange={(e) => setNewModelId(e.target.value)}
                        placeholder="Hugging Face Model ID"
                        disabled={isDownloading}
                    />
                    <button type="submit" disabled={isDownloading}>
                        {isDownloading ? 'Downloading...' : 'Download'}
                    </button>
                </form>
                <h3 style={{marginTop: '1.5rem'}}>Available Models</h3>
                <ul className="model-list">
                    {models.length > 0 ? models.map(model => (
                        <li
                            key={model.id}
                            className={`model-list-item ${selectedModel?.id === model.id ? 'selected' : ''}`}
                            onClick={() => setSelectedModel(model)}
                        >
                            {model.name} ({model.status})
                        </li>
                    )) : <p>No models downloaded yet.</p>}
                </ul>
            </div>
            <div className="chat-interface">
                <h2>Chat</h2>
                {chatError && <p className="error-message">{chatError}</p>}
                <div className="chat-history">
                    {chatHistory.map((msg, index) => (
                        <div key={index} className={`chat-message ${msg.role}`}>
                           <div className="message-bubble">{msg.content}</div>
                        </div>
                    ))}
                     {isGenerating && <div className="loading-message">Thinking...</div>}
                </div>
                <form onSubmit={handleChatSubmit}>
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder={selectedModel ? `Chat with ${selectedModel.name}...` : 'Select a model to start chatting'}
                        disabled={!selectedModel || isGenerating}
                    />
                    <button type="submit" disabled={!selectedModel || isGenerating}>
                        Send
                    </button>
                </form>
            </div>

            <TrainingDashboard models={models} />

            {user?.role === 'admin' && <UserManagement />}
        </div>
    );
}

export default Dashboard;
