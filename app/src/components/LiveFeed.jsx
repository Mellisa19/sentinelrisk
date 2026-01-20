import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { Clock, ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

const LiveFeed = () => {
    const [stream, setStream] = useState([]);
    const [isPolling, setIsPolling] = useState(true);

    const fetchLiveTraffic = async () => {
        try {
            // Fetch latest logs that are marked as simulated
            const response = await api.get('/logs?limit=10');
            // Filter for is_simulated = 1 (or just show all for the "Real Thing" feel)
            const latest = response.data.slice(0, 6);
            setStream(latest);
        } catch (err) {
            console.error("Live Feed Error:", err);
        }
    };

    useEffect(() => {
        fetchLiveTraffic();
        const interval = setInterval(fetchLiveTraffic, 3000); // 3s Pulse
        return () => clearInterval(interval);
    }, []);

    const statusMap = {
        APPROVE: { color: 'text-fraud-approve', icon: ShieldCheck, bg: 'bg-fraud-approve/5' },
        REVIEW: { color: 'text-fraud-review', icon: Shield, bg: 'bg-fraud-review/5' },
        BLOCK: { color: 'text-fraud-block', icon: ShieldAlert, bg: 'bg-fraud-block/5' },
    };

    return (
        <div className="bg-graphite-800 border border-graphite-700 rounded-2xl overflow-hidden flex flex-col h-full">
            <header className="p-6 border-b border-graphite-700 flex justify-between items-center bg-graphite-900/30">
                <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fraud-approve opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-fraud-approve"></span>
                        </span>
                        Live Transaction Stream
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">Real-time inference pipeline active</p>
                </div>
                <div className="text-[10px] uppercase font-bold tracking-widest text-slate-500 bg-graphite-900 px-2 py-1 rounded border border-graphite-700">
                    Auto-Refreshed
                </div>
            </header>

            <div className="flex-1 divide-y divide-graphite-700/50 overflow-y-auto">
                {stream.length === 0 ? (
                    <div className="p-12 text-center text-slate-600 italic text-sm">
                        Waiting for global traffic...
                    </div>
                ) : (
                    stream.map((tx) => {
                        const style = statusMap[tx.decision] || statusMap.APPROVE;
                        const Icon = style.icon;
                        return (
                            <div key={tx.id} className={`p-4 flex items-center justify-between hover:bg-white/5 transition-colors animate-in fade-in slide-in-from-top-2 duration-300 ${tx.is_simulated ? 'border-l-2 border-l-fraud-approve/30' : ''}`}>
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-lg ${style.bg}`}>
                                        <Icon size={18} className={style.color} />
                                    </div>
                                    <div>
                                        <div className="text-sm font-bold text-white">${tx.amount.toFixed(2)}</div>
                                        <div className="text-[10px] text-slate-500 font-mono">{tx.request_id.split('-')[0]}...</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-[10px] font-black tracking-tighter ${style.color}`}>{tx.decision}</div>
                                    <div className="text-[10px] text-slate-600 flex items-center justify-end gap-1">
                                        <Clock size={10} />
                                        {new Date(tx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default LiveFeed;
