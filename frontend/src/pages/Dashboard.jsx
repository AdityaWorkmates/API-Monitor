import React, { useEffect, useState } from 'react';
import { getEndpoints } from '../services/api';
import { CheckCircle, XCircle, Clock, Activity } from 'lucide-react';
import clsx from 'clsx';
import { Card, CardContent, CardHeader, CardTitle } from '../components/Card';

const Dashboard = () => {
    const [endpoints, setEndpoints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const response = await getEndpoints();
            setEndpoints(response.data);
            setLoading(false);
        } catch (err) {
            setError('Failed to fetch data');
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
    if (error) return <div className="p-8 text-destructive">{error}</div>;

    const total = endpoints.length;
    const up = endpoints.filter(e => e.current_status === 'up').length;
    const down = endpoints.filter(e => e.current_status === 'down').length;
    
    // Calculate average latency of UP endpoints
    const upEndpoints = endpoints.filter(e => e.current_status === 'up' && e.last_response_time);
    const avgLatency = upEndpoints.length > 0 
        ? Math.round(upEndpoints.reduce((acc, curr) => acc + curr.last_response_time, 0) / upEndpoints.length) 
        : 0;

    const stats = [
        { name: 'Total Endpoints', value: total, icon: Activity, color: 'text-blue-600', bg: 'bg-blue-50' },
        { name: 'Services Up', value: up, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
        { name: 'Services Down', value: down, icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
        { name: 'Avg Latency', value: `${avgLatency}ms`, icon: Clock, color: 'text-orange-600', bg: 'bg-orange-50' },
    ];

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight text-gray-900">Dashboard</h1>
            </div>
            
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {stats.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Card key={item.name}>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">
                                    {item.name}
                                </CardTitle>
                                <Icon className={clsx("h-4 w-4 text-muted-foreground", item.color)} />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{item.value}</div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            <div className="space-y-4">
                <h2 className="text-xl font-semibold tracking-tight text-gray-900">Recent Status</h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {endpoints.length === 0 ? (
                        <Card className="col-span-full">
                            <CardContent className="py-8 text-center text-muted-foreground">
                                No endpoints monitored yet. Add one to get started.
                            </CardContent>
                        </Card>
                    ) : (
                        endpoints.map((endpoint) => (
                            <Card key={endpoint._id} className="hover:bg-accent/50 transition-colors">
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="font-medium truncate pr-4">
                                        {endpoint.name}
                                    </CardTitle>
                                    <div className={clsx(
                                        "px-2.5 py-0.5 rounded-full text-xs font-semibold",
                                        endpoint.current_status === 'up' ? 'bg-green-100 text-green-700' : 
                                        endpoint.current_status === 'down' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                                    )}>
                                        {endpoint.current_status ? endpoint.current_status.toUpperCase() : 'PENDING'}
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-xs text-muted-foreground mb-2 truncate" title={endpoint.url}>
                                        {endpoint.url}
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <div className="flex items-center text-muted-foreground">
                                            <Clock className="mr-1 h-3 w-3" />
                                            {endpoint.last_response_time ? `${endpoint.last_response_time}ms` : '-'}
                                        </div>
                                        <div className="text-muted-foreground text-xs">
                                            {endpoint.last_checked ? new Date(endpoint.last_checked).toLocaleTimeString() : 'Never'}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
