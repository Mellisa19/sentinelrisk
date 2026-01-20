import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { TrendingUp, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import LiveFeed from './LiveFeed';

const Dashboard = () => {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await api.get('/metrics?hours=24');
                setMetrics(response.data);
            } catch (err) {
                setError("Failed to fetch operational metrics.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchMetrics();
        const interval = setInterval(fetchMetrics, 30000); // Polling every 30s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="text-slate-500 animate-pulse">Loading engine metrics...</div>;
    if (error) return <div className="p-4 bg-fraud-block/20 text-fraud-block rounded-lg">{error}</div>;

    const chartData = [
        { name: 'Approve', value: metrics.decisions.APPROVE, color: '#10b981' },
        { name: 'Review', value: metrics.decisions.REVIEW, color: '#f59e0b' },
        { name: 'Block', value: metrics.decisions.BLOCK, color: '#dc2626' },
    ];

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <header>
                <h2 className="text-3xl font-bold text-white">Risk Intelligence</h2>
                <p className="text-slate-400 mt-1">Real-time model operational status and decision analytics.</p>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Volume" value={metrics.total_requests} icon={Activity} />
                <StatCard title="Avg Risk Score" value={metrics.avg_risk_score.toFixed(4)} icon={TrendingUp} />
                <StatCard
                    title="Alert Status"
                    value={metrics.alerts.length > 0 ? 'Critical' : 'Healthy'}
                    icon={AlertTriangle}
                    status={metrics.alerts.length > 0 ? 'block' : 'approve'}
                />
                <StatCard title="Active Model" value="XGBoost v1" icon={ShieldCheck} />
            </div>

            {/* Alerts Section */}
            {metrics.alerts.length > 0 && (
                <div className="bg-fraud-block/10 border border-fraud-block/20 p-4 rounded-xl flex gap-3 items-start">
                    <AlertTriangle className="text-fraud-block shrink-0" />
                    <div>
                        <h4 className="font-bold text-fraud-block text-sm">Active System Drift Alerts</h4>
                        <ul className="text-sm text-slate-300 mt-1 list-disc list-inside">
                            {metrics.alerts.map((alert, idx) => (
                                <li key={idx}>{alert}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Distribution and Live Stream */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-graphite-800 border border-graphite-700 p-6 rounded-2xl">
                    <h3 className="text-lg font-semibold mb-6">Decision Distribution (24h)</h3>
                    <div className="h-64 mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData}>
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <YAxis hide />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1a1c1e', border: '1px solid #34383d', borderRadius: '8px' }}
                                    cursor={{ fill: '#26292c' }}
                                />
                                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="lg:col-span-1">
                    <LiveFeed />
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ title, value, icon: Icon, status = 'default' }) => {
    const statusColors = {
        approve: 'text-fraud-approve bg-fraud-approve/10 border-fraud-approve/20',
        block: 'text-fraud-block bg-fraud-block/10 border-fraud-block/20',
        default: 'text-white bg-graphite-700 border-graphite-600'
    };

    return (
        <div className="bg-graphite-800 border border-graphite-700 p-6 rounded-2xl hover:border-graphite-600 transition-colors">
            <div className="flex items-center justify-between mb-4">
                <span className="text-slate-400 text-sm font-medium">{title}</span>
                <div className={`p-2 rounded-lg ${statusColors[status] || statusColors.default}`}>
                    <Icon size={18} />
                </div>
            </div>
            <div className="text-2xl font-bold">{value}</div>
        </div>
    );
};

export default Dashboard;
