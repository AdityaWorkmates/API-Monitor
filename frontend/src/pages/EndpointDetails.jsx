import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getEndpoint, getEndpointLogs, getEndpointStats } from '../services/api';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { ArrowLeft, Clock, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';
import { format } from 'date-fns';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const EndpointDetails = () => {
    const { id } = useParams();
    const [endpoint, setEndpoint] = useState(null);
    const [stats, setStats] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [epRes, statsRes, logsRes] = await Promise.all([
                    getEndpoint(id),
                    getEndpointStats(id),
                    getEndpointLogs(id)
                ]);
                setEndpoint(epRes.data);
                setStats(statsRes.data);
                setLogs(logsRes.data);
            } catch (error) {
                console.error('Error fetching details:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchAll();
        const interval = setInterval(fetchAll, 10000); // Live update
        return () => clearInterval(interval);
    }, [id]);

    if (loading) return <div>Loading...</div>;
    if (!endpoint) return <div>Endpoint not found</div>;

    // Prepare Chart Data
    // We want to show response time over time.
    // We'll reverse logs to show oldest to newest on graph if API returns newest first.
    const chartLogs = [...logs].reverse(); 
    const chartData = {
        labels: chartLogs.map(log => format(new Date(log.checked_at), 'HH:mm:ss')),
        datasets: [
            {
                label: 'Response Time (ms)',
                data: chartLogs.map(log => log.response_time_ms),
                borderColor: 'rgb(79, 70, 229)',
                backgroundColor: 'rgba(79, 70, 229, 0.5)',
                tension: 0.2,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Latency History' },
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'ms' }
            }
        }
    };

    return (
        <div>
            <div className="mb-6">
                <Link to="/endpoints" className="inline-flex items-center text-indigo-600 hover:text-indigo-900">
                    <ArrowLeft className="h-4 w-4 mr-2" /> Back to Endpoints
                </Link>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
                <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{endpoint.name}</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">{endpoint.url}</p>
                </div>
                <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                    <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-4">
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Current Status</dt>
                            <dd className="mt-1 text-sm text-gray-900 flex items-center">
                                {endpoint.current_status === 'up' ? (
                                    <span className="flex items-center text-green-600 font-bold"><CheckCircle className="w-4 h-4 mr-1"/> UP</span>
                                ) : (
                                    <span className="flex items-center text-red-600 font-bold"><XCircle className="w-4 h-4 mr-1"/> DOWN</span>
                                )}
                            </dd>
                        </div>
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Uptime (Total)</dt>
                            <dd className="mt-1 text-sm text-gray-900">{stats?.uptime_percentage}%</dd>
                        </div>
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Avg Latency</dt>
                            <dd className="mt-1 text-sm text-gray-900">{stats?.average_response_time} ms</dd>
                        </div>
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-gray-500">Last Checked</dt>
                            <dd className="mt-1 text-sm text-gray-900">{endpoint.last_checked ? new Date(endpoint.last_checked).toLocaleString() : 'Never'}</dd>
                        </div>
                    </dl>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white shadow rounded-lg p-4">
                    <Line options={chartOptions} data={chartData} />
                </div>

                <div className="bg-white shadow rounded-lg overflow-hidden">
                    <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Logs</h3>
                    </div>
                    <ul className="divide-y divide-gray-200 max-h-[400px] overflow-y-auto">
                        {logs.map((log) => (
                            <li key={log._id} className="px-4 py-3 hover:bg-gray-50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        {log.success ? (
                                            <CheckCircle className="h-5 w-5 text-green-500" />
                                        ) : (
                                            <XCircle className="h-5 w-5 text-red-500" />
                                        )}
                                        <div className="text-sm">
                                            <p className="font-medium text-gray-900">
                                                {log.success ? `Status ${log.status_code}` : `Error: ${log.error || 'Failed'}`}
                                            </p>
                                            <p className="text-gray-500 text-xs">
                                                {new Date(log.checked_at).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-sm text-gray-500 font-mono">
                                        {log.response_time_ms}ms
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default EndpointDetails;
