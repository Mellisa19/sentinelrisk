import React from 'react';
import { LayoutDashboard, PlayCircle, ShieldCheck, Activity } from 'lucide-react';

const Sidebar = ({ activeView, setActiveView }) => {
    const navItems = [
        { id: 'dashboard', label: 'Risk Dashboard', icon: LayoutDashboard },
        { id: 'simulator', label: 'Simulator', icon: PlayCircle },
        { id: 'audit', label: 'Audit Log', icon: ShieldCheck },
    ];

    return (
        <aside className="w-64 bg-graphite-800 border-r border-graphite-700 flex flex-col">
            <div className="p-6 flex items-center gap-3 border-b border-graphite-700">
                <Activity className="text-fraud-approve w-8 h-8" />
                <h1 className="text-xl font-bold tracking-tight text-white">Sentinel<span className="text-fraud-approve">Risk</span></h1>
            </div>

            <nav className="flex-1 p-4 space-y-2 mt-4">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeView === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveView(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isActive
                                    ? 'bg-graphite-700 text-white shadow-lg border border-graphite-600'
                                    : 'text-slate-400 hover:text-white hover:bg-graphite-700'
                                }`}
                        >
                            <Icon size={20} className={isActive ? 'text-fraud-approve' : ''} />
                            <span className="font-medium">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-6 text-xs text-slate-500 border-t border-graphite-700">
                v1.0.0 Production Stage
            </div>
        </aside>
    );
};

export default Sidebar;
