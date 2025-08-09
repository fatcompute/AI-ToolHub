import React, { useState, useEffect, useCallback } from 'react';
import JobAnalytics from './JobAnalytics';

const API_URL = 'http://localhost:5000/api/v1';

function TrainingDashboard({ models }) {
    // State for datasets
    const [datasets, setDatasets] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);

    // State for training jobs
    const [jobs, setJobs] = useState([]);
    const [selectedModelForTraining, setSelectedModelForTraining] = useState('');
    const [selectedDatasetForTraining, setSelectedDatasetForTraining] = useState('');
    const [isStartingJob, setIsStartingJob] = useState(false);

    // State for monitoring
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDetails, setJobDetails] = useState(null);

    const [error, setError] = useState('');

    // --- Data Fetching Callbacks ---
    const fetchDatasets = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/datasets`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to fetch datasets');
            setDatasets(data);
        } catch (err) {
            setError(err.message);
        }
    }, []);

    const fetchJobs = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/jobs`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to fetch jobs');
            setJobs(data);
        } catch (err) {
            setError(err.message);
        }
    }, []);

    const fetchJobDetails = useCallback(async (jobId) => {
        if (!jobId) return;
        try {
            const response = await fetch(`${API_URL}/jobs/${jobId}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to fetch job details');
            setJobDetails(data);
        } catch (err) {
            setError(err.message);
        }
    }, []);

    // --- Initial Data Load and Polling ---
    useEffect(() => {
        fetchDatasets();
        fetchJobs();
    }, [fetchDatasets, fetchJobs]);

    useEffect(() => {
        // Poll for job updates and selected job details
        const interval = setInterval(() => {
            fetchJobs();
            if (selectedJob) {
                fetchJobDetails(selectedJob.id);
            }
        }, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, [fetchJobs, selectedJob, fetchJobDetails]);


    // --- Event Handlers ---
    const handleFileUpload = async (e) => {
        e.preventDefault();
        if (!selectedFile) {
            setError('Please select a file to upload.');
            return;
        }
        setIsUploading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch(`${API_URL}/datasets/upload`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Upload failed');
            await fetchDatasets(); // Refresh list
            setSelectedFile(null);
            e.target.reset(); // Clear file input
        } catch (err) {
            setError(err.message);
        } finally {
            setIsUploading(false);
        }
    };

    const handleStartJob = async (e) => {
        e.preventDefault();
        if (!selectedModelForTraining || !selectedDatasetForTraining) {
            setError('Please select a model and a dataset to start training.');
            return;
        }
        setIsStartingJob(true);
        setError('');
        try {
            const response = await fetch(`${API_URL}/jobs/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model_id: selectedModelForTraining,
                    dataset_id: selectedDatasetForTraining,
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to start job');
            await fetchJobs(); // Refresh job list
        } catch (err) {
            setError(err.message);
        } finally {
            setIsStartingJob(false);
        }
    };

    return (
        <div className="training-dashboard" style={{marginTop: '2rem'}}>
            <h2>Model Training & Fine-Tuning</h2>
            {error && <p className="error-message">{error}</p>}

            {/* Start New Job Section */}
            <div className="start-job-section">
                <h3>Start a New Training Job</h3>
                <form onSubmit={handleStartJob} className="start-job-form">
                    <select value={selectedModelForTraining} onChange={e => setSelectedModelForTraining(e.target.value)} required>
                        <option value="">Select a Base Model</option>
                        {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                    </select>
                    <select value={selectedDatasetForTraining} onChange={e => setSelectedDatasetForTraining(e.target.value)} required>
                        <option value="">Select a Dataset</option>
                        {datasets.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
                    </select>
                    <button type="submit" disabled={isStartingJob}>{isStartingJob ? 'Starting...' : 'Start Training'}</button>
                </form>
            </div>

            {/* Job Monitoring Section */}
            <div className="job-monitoring-section">
                <h3>Training Jobs</h3>
                <div className="jobs-and-logs-grid">
                    <ul className="job-list">
                        {jobs.length > 0 ? jobs.map(job => (
                            <li key={job.id} onClick={() => { setSelectedJob(job); fetchJobDetails(job.id); }} className={selectedJob?.id === job.id ? 'selected' : ''}>
                                Job {job.id} - {job.status}
                            </li>
                        )) : <p>No training jobs found.</p>}
                    </ul>
                    <div className="job-logs">
                        <h4>Job Details & Logs</h4>
                        {jobDetails ? (
                            <div>
                                <pre>{`Status: ${jobDetails.status}\n\nLogs:\n${jobDetails.logs || 'No logs yet.'}`}</pre>
                                <JobAnalytics jobDetails={jobDetails} />
                            </div>
                        ) : <p>Select a job to see details.</p>}
                    </div>
                </div>
            </div>

            {/* Dataset Management Section */}
            <div className="dataset-management-section">
                <h3>Manage Datasets</h3>
                <form onSubmit={handleFileUpload}>
                    <input type="file" onChange={e => setSelectedFile(e.target.files[0])} />
                    <button type="submit" disabled={isUploading}>{isUploading ? 'Uploading...' : 'Upload Dataset'}</button>
                </form>
                <ul>
                    {datasets.map(d => <li key={d.id}>{d.filename}</li>)}
                </ul>
            </div>
        </div>
    );
}

export default TrainingDashboard;
