import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Plus, List } from 'lucide-react';
import clsx from 'clsx';

const Layout = ({ children }) => {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Dashboard', icon: Activity },
        { path: '/endpoints', label: 'Endpoints', icon: List },
        { path: '/endpoints/new', label: 'Add Endpoint', icon: Plus },
    ];

    return (
        <div className="min-h-screen bg-muted/20 flex flex-col font-sans">
            <nav className="bg-background border-b border-border shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex">
                            <Link to="/" className="flex-shrink-0 flex items-center">
                                <Activity className="h-6 w-6 text-primary" />
                                <span className="ml-2 text-lg font-bold text-foreground">API Monitor</span>
                            </Link>
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                                {navItems.map((item) => {
                                    const Icon = item.icon;
                                    const isActive = location.pathname === item.path;
                                    return (
                                        <Link
                                            key={item.path}
                                            to={item.path}
                                            className={clsx(
                                                isActive
                                                    ? 'border-primary text-primary'
                                                    : 'border-transparent text-muted-foreground hover:border-border hover:text-foreground',
                                                'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200'
                                            )}
                                        >
                                            <Icon className="w-4 h-4 mr-2" />
                                            {item.label}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </main>
        </div>
    );
};

export default Layout;
