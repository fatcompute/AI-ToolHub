import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';
import ReactDiffViewer from 'react-diff-viewer-continued';

function CodeHealthPage() {
    const [errors, setErrors] = useState([]);
    const [selectedError, setSelectedError] = useState(null);
    const [errorDetails, setErrorDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [pageError, setPageError] = useState('');

    const fetchErrors = useCallback(async () => {
        setLoading(true);
        try {
            const response = await api.get('/agent/errors');
            setErrors(response.data);
        } catch (err) {
            setPageError(err.response?.data?.error || 'Failed to fetch errors.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchErrors();
    }, [fetchErrors]);

    const handleSelectError = async (errorId) => {
        setSelectedError(errorId);
        setLoading(true);
        try {
            const response = await api.get(`/agent/errors/${errorId}`);
            setErrorDetails(response.data);
        } catch (err) {
            setPageError(err.response?.data?.error || 'Failed to fetch error details.');
        } finally {
            setLoading(false);
        }
    };

    const newStyles = {
        variables: {
            dark: {
                diffViewerBackground: '#242424',
                diffViewerColor: '#fff',
                addedBackground: '#044B53',
                addedColor: 'white',
                removedBackground: '#632F34',
                removedColor: 'white',
                wordAddedBackground: '#055d67',
                wordRemovedBackground: '#7d383f',
                addedGutterBackground: '#034148',
                removedGutterBackground: '#542a2f',
                gutterBackground: '#2c2c2c',
                gutterBackgroundDark: '#262626',
                highlightBackground: '#2A3967',
                highlightGutterBackground: '#2d4077',
                codeFoldGutterBackground: '#262626',
                codeFoldBackground: '#242424',
                emptyLineBackground: '#363636',
                gutterColor: '#999',
                addedGutterColor: '#adff2f',
                removedGutterColor: '#ff6347',
                codeFoldContentColor: '#999',
                diffViewerTitleBackground: '#2f2f2f',
                diffViewerTitleColor: '#fff',
                diffViewerTitleBorderColor: '#353535',
            },
        },
    };

    return (
        <div className="code-health-page">
            <h2>Code Health Dashboard</h2>
            {pageError && <p className="error-message">{pageError}</p>}
            <div className="health-grid">
                <div className="error-list-container">
                    <h3>Captured Errors</h3>
                    <ul className="error-list">
                        {loading && !errors.length && <p>Loading...</p>}
                        {errors.map(e => (
                            <li
                                key={e.id}
                                onClick={() => handleSelectError(e.id)}
                                className={selectedError === e.id ? 'selected' : ''}
                            >
                                <strong>{e.file_path?.split('/').pop()}:{e.line_number}</strong>
                                <span>{e.status}</span>
                                <small>{new Date(e.created_at).toLocaleString()}</small>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="error-details-container">
                    <h3>Error Details</h3>
                    {loading && !errorDetails && <p>Loading details...</p>}
                    {!errorDetails && <p>Select an error to see details.</p>}
                    {errorDetails && (
                        <div>
                            <h4>AI Analysis</h4>
                            <p className="analysis-text">{errorDetails.analysis || 'Analysis pending...'}</p>

                            <h4>Proposed Fix</h4>
                            {errorDetails.proposed_fix ? (
                                <ReactDiffViewer
                                    oldValue="" // We show a diff from nothing to the proposed fix
                                    newValue={errorDetails.proposed_fix}
                                    splitView={false}
                                    useDarkTheme={true}
                                    styles={newStyles}
                                />
                            ) : <p>No fix proposed yet.</p>}

                            <h4>Full Traceback</h4>
                            <pre className="traceback-box">{errorDetails.traceback}</pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default CodeHealthPage;
