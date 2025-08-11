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
    const [selectedTrainDataset, setSelectedTrainDataset] = useState('');
    const [selectedEvalDataset, setSelectedEvalDataset] = useState('');
    const [epochs, setEpochs] = useState(1);
    const [batchSize, setBatchSize] = useState(1);
    const [isStartingJob, setIsStartingJob] = useState(false);

    // State for monitoring
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDetails, setJobDetails] = useState(null);

    const [error, setError] = useState('');

    // --- Data Fetching Callbacks ---
    const fetchDatasets = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/datasets`);
            setDatasets(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to fetch datasets.');
        }
    }, []);

    const fetchJobs = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/jobs`);
            setJobs(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to fetch jobs.');
        }
    }, []);

    const fetchJobDetails = useCallback(async (jobId) => {
        if (!jobId) return;
        try {
            const response = await api.get(`/jobs/${jobId}`);
            setJobDetails(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to fetch job details.');
        }
    }, []);

    // --- Initial Data Load and Polling ---
    useEffect(() => {
        fetchDatasets();
        fetchJobs();
    }, [fetchDatasets, fetchJobs]);

    // Pre-fill form with user's default settings
    useEffect(() => {
        if (currentUser?.settings) {
            setEpochs(currentUser.settings.default_epochs || 1);
            setBatchSize(currentUser.settings.default_batch_size || 1);
        }
    }, [currentUser]);

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
        if (!selectedModelForTraining || !selectedTrainDataset) {
            setError('Please select a base model and a training dataset.');
            return;
        }
        setIsStartingJob(true);
        setError('');
        try {
            const payload = {
                model_id: selectedModelForTraining,
                dataset_id: selectedTrainDataset,
                num_train_epochs: epochs,
                per_device_train_batch_size: batchSize,
            };
            if (selectedEvalDataset) {
                payload.eval_dataset_id = selectedEvalDataset;
            }

            await api.post('/jobs/start', payload);
            await fetchJobs(); // Refresh job list
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to start job.');
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
                <form onSubmit={handleStartJob} className="start-job-form-grid">
                    <select value={selectedModelForTraining} onChange={e => setSelectedModelForTraining(e.target.value)} required>
                        <option value="">Select a Base Model</option>
                        {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                    </select>
                    <select value={selectedTrainDataset} onChange={e => setSelectedTrainDataset(e.target.value)} required>
                        <option value="">Select Training Dataset</option>
                        {datasets.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
                    </select>
                    <select value={selectedEvalDataset} onChange={e => setSelectedEvalDataset(e.target.value)}>
                        <option value="">Select Evaluation Dataset (Optional)</option>
                        {datasets.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
                    </select>

                    <input type="number" value={epochs} onChange={e => setEpochs(e.target.value)} placeholder="Epochs" min="1" />
                    <input type="number" value={batchSize} onChange={e => setBatchSize(e.target.value)} placeholder="Batch Size" min="1" />

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
