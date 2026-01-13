import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getEndpoints, deleteEndpoint } from '../services/api';
import { Trash2, ExternalLink, RefreshCw } from 'lucide-react';
import clsx from 'clsx';

const EndpointList = () => {
    const [endpoints, setEndpoints] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadEndpoints();
    }, []);

    const loadEndpoints = async () => {
        setLoading(true);
        try {
            const response = await getEndpoints();
            setEndpoints(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this endpoint?')) {
            try {
                await deleteEndpoint(id);
                loadEndpoints();
            } catch (error) {
                console.error(error);
                alert('Failed to delete endpoint');
            }
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Monitored Endpoints</h1>
                <div className="space-x-2">
                    <button onClick={loadEndpoints} className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                        <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                    </button>
                    <Link to="/endpoints/new" className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700">
                        Add New Endpoint
                    </Link>
                </div>
            </div>

            <div className="flex flex-col">
                <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                    <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                        <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interval</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Check</th>
                                        <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {endpoints.map((endpoint) => (
                                        <tr key={endpoint._id}>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div>
                                                        <div className="text-sm font-medium text-gray-900">{endpoint.name}</div>
                                                        <div className="text-sm text-gray-500">{endpoint.url}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={clsx(
                                                    "px-2 inline-flex text-xs leading-5 font-semibold rounded-full",
                                                    endpoint.current_status === 'up' ? 'bg-green-100 text-green-800' : 
                                                    endpoint.current_status === 'down' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                                                )}>
                                                    {endpoint.current_status ? endpoint.current_status.toUpperCase() : 'PENDING'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{endpoint.method}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{endpoint.interval}s</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {endpoint.last_checked ? new Date(endpoint.last_checked).toLocaleString() : '-'}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <Link to={`/endpoints/${endpoint._id}`} className="text-indigo-600 hover:text-indigo-900 mr-4">
                                                    Details
                                                </Link>
                                                <button onClick={() => handleDelete(endpoint._id)} className="text-red-600 hover:text-red-900">
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EndpointList;
