import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function JobAnalytics({ jobDetails }) {
    if (!jobDetails || !jobDetails.metrics || jobDetails.metrics.length === 0) {
        return <p>No performance metrics available for this job.</p>;
    }

    // Filter for logs that contain the 'loss' key, as these are the training steps
    const trainingSteps = jobDetails.metrics.filter(m => m.loss);

    const chartData = {
        labels: trainingSteps.map(m => m.step),
        datasets: [
            {
                label: 'Training Loss',
                data: trainingSteps.map(m => m.loss),
                fill: false,
                borderColor: '#61dafb',
                tension: 0.1,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    color: '#f0f0f0'
                }
            },
            title: {
                display: true,
                text: `Training Performance for Job ${jobDetails.id}`,
                color: '#f0f0f0',
                font: {
                    size: 16
                }
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Step',
                    color: '#f0f0f0'
                },
                ticks: {
                    color: '#f0f0f0'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Loss',
                    color: '#f0f0f0'
                },
                ticks: {
                    color: '#f0f0f0'
                }
            }
        }
    };

    return (
        <div className="job-analytics">
            <h4>Performance Analytics</h4>
            <Line options={chartOptions} data={chartData} />
        </div>
    );
}

export default JobAnalytics;
