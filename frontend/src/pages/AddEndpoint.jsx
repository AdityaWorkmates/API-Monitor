import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createEndpoint } from '../services/api';

const AddEndpoint = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        url: '',
        method: 'GET',
        interval: 60,
        timeout: 5
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await createEndpoint(formData);
            navigate('/endpoints');
        } catch (err) {
            setError('Failed to create endpoint. Please check your inputs.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Add New Endpoint</h1>
            
            <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
                {error && <div className="text-red-600 text-sm">{error}</div>}
                
                <div className="grid grid-cols-1 gap-6">
                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700">Friendly Name</label>
                        <input
                            type="text"
                            name="name"
                            id="name"
                            required
                            className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 p-2 border"
                            placeholder="e.g. Google Health Check"
                            value={formData.name}
                            onChange={handleChange}
                        />
                    </div>

                    <div>
                        <label htmlFor="url" className="block text-sm font-medium text-gray-700">URL</label>
                        <input
                            type="url"
                            name="url"
                            id="url"
                            required
                            className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 p-2 border"
                            placeholder="https://api.example.com/health"
                            value={formData.url}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="method" className="block text-sm font-medium text-gray-700">HTTP Method</label>
                            <select
                                name="method"
                                id="method"
                                className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                value={formData.method}
                                onChange={handleChange}
                            >
                                <option value="GET">GET</option>
                                <option value="POST">POST</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                                <option value="HEAD">HEAD</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="interval" className="block text-sm font-medium text-gray-700">Interval (seconds)</label>
                            <input
                                type="number"
                                name="interval"
                                id="interval"
                                min="10"
                                className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 p-2 border"
                                value={formData.interval}
                                onChange={handleChange}
                            />
                        </div>
                    </div>
                     <div>
                        <label htmlFor="timeout" className="block text-sm font-medium text-gray-700">Timeout (seconds)</label>
                        <input
                            type="number"
                            name="timeout"
                            id="timeout"
                            min="1"
                            className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 p-2 border"
                            value={formData.timeout}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={loading}
                        className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
                    >
                        {loading ? 'Creating...' : 'Start Monitoring'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default AddEndpoint;
