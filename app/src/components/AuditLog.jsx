import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { Search, Download, Clock, Filter } from 'lucide-react';

const AuditLog = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await api.get('/logs?limit=50');
                setLogs(response.data);
            } catch (err) {
                setError("Failed to load audit trail.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    const filteredLogs = logs.filter(log =>
        log.request_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.decision.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const statusStyles = {
        APPROVE: 'text-fraud-approve bg-fraud-approve/10 border-fraud-approve/20',
        REVIEW: 'text-fraud-review bg-fraud-review/10 border-fraud-review/20',
        BLOCK: 'text-fraud-block bg-fraud-block/10 border-fraud-block/20',
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-500">
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold text-white">Immutable Audit Trail</h2>
                    <p className="text-slate-400 mt-1">Full historical log of all model predictions and decisions.</p>
                </div>
                <div className="flex gap-2">
                    <button className="px-4 py-2 bg-graphite-700 border border-graphite-600 rounded-lg text-sm text-slate-300 flex items-center gap-2 hover:bg-graphite-600">
                        <Download size={16} /> Export CSV
                    </button>
                </div>
            </header>

            {/* Filters Bar */}
            <div className="flex flex-col md:flex-row gap-4 bg-graphite-800 border border-graphite-700 p-4 rounded-xl">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search by Request ID or Decision..."
                        className="w-full bg-graphite-900 border border-graphite-600 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-fraud-approve text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <button className="px-4 py-2 bg-graphite-700 border border-graphite-600 rounded-lg text-sm flex items-center gap-2">
                    <Filter size={16} /> Filter
                </button>
            </div>

            {/* Table Section */}
            <div className="bg-graphite-800 border border-graphite-700 rounded-2xl overflow-hidden shadow-2xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-graphite-900/50 border-b border-graphite-700">
                                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Timestamp</th>
                                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Request ID</th>
                                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-right">Amount</th>
                                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-center">Decision</th>
                                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Explanation</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-graphite-700/50">
                            {loading ? (
                                <tr><td colSpan="5" className="px-6 py-12 text-center text-slate-500 italic">Accessing historical data...</td></tr>
                            ) : error ? (
                                <tr><td colSpan="5" className="px-6 py-12 text-center text-fraud-block">{error}</td></tr>
                            ) : filteredLogs.length === 0 ? (
                                <tr><td colSpan="5" className="px-6 py-12 text-center text-slate-500 italic">No records found matching criteria.</td></tr>
                            ) : (
                                filteredLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-graphite-700/30 transition-colors group">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2 text-sm">
                                                <Clock size={14} className="text-slate-500" />
                                                {new Date(log.timestamp).toLocaleTimeString()}
                                            </div>
                                            <div className="text-[10px] text-slate-600 font-mono mt-1">
                                                {new Date(log.timestamp).toLocaleDateString()}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <code className="text-[11px] bg-graphite-900 rounded-md px-2 py-1 text-fraud-approve/80 border border-fraud-approve/10">
                                                {log.request_id}
                                            </code>
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono text-sm font-bold text-white">
                                            ${log.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest border transition-all ${statusStyles[log.decision]}`}>
                                                {log.decision}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate group-hover:whitespace-normal group-hover:overflow-visible transition-all">
                                            {log.explanation}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AuditLog;
