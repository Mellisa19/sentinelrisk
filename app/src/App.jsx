import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Simulator from './components/Simulator';
import AuditLog from './components/AuditLog';

function App() {
    const [activeView, setActiveView] = useState('dashboard');

    return (
        <div className="flex h-screen bg-graphite-900 text-slate-200">
            {/* Sidebar Navigation */}
            <Sidebar activeView={activeView} setActiveView={setActiveView} />

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto p-8">
                <div className="max-w-7xl mx-auto">
                    {activeView === 'dashboard' && <Dashboard />}
                    {activeView === 'simulator' && <Simulator />}
                    {activeView === 'audit' && <AuditLog />}
                </div>
            </main>
        </div>
    );
}

export default App;
