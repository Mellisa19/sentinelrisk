import React, { useState } from 'react';
import api from '../utils/api';
import { Send, RefreshCw, ShieldAlert, ShieldCheck, Shield, Activity, Clock, Calendar } from 'lucide-react';

const Simulator = () => {
    const [formData, setFormData] = useState({
        Amount: 150.0,
        transaction_timestamp: new Date().toISOString().slice(0, 16), // Format for datetime-local input
        merchant_category: 'electronics',
        transaction_type: 'online',
    });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        // Convert timestamp to ISO format and calculate Time field for backward compatibility
        const timestamp = new Date(formData.transaction_timestamp).toISOString();
        const dateObj = new Date(formData.transaction_timestamp);
        const timeInSeconds = dateObj.getHours() * 3600 + dateObj.getMinutes() * 60 + dateObj.getSeconds();

        // Mock V1-V28 with small values for demo
        const payload = {
            Time: timeInSeconds, // Required for backward compatibility
            transaction_timestamp: timestamp, // New temporal feature
            Amount: formData.Amount,
            merchant_category: formData.merchant_category,
            transaction_type: formData.transaction_type,
            ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`).reduce((acc, key) => {
                acc[key] = Math.random() * 0.2 - 0.1;
                return acc;
            }, {})
        };

        try {
            const response = await api.post('/predict', payload);
            setResult(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Connection failed. Ensure API is running on :8000");
        } finally {
            setLoading(false);
        }
    };

    const statusMap = {
        APPROVE: { color: 'text-fraud-approve', bg: 'bg-fraud-approve/10', border: 'border-fraud-approve/30', icon: ShieldCheck },
        REVIEW: { color: 'text-fraud-review', bg: 'bg-fraud-review/10', border: 'border-fraud-review/30', icon: Shield },
        BLOCK: { color: 'text-fraud-block', bg: 'bg-fraud-block/10', border: 'border-fraud-block/30', icon: ShieldAlert },
    };

    const UI = result ? statusMap[result.decision] : null;

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            <header>
                <h2 className="text-3xl font-bold text-white">Transaction Simulator</h2>
                <p className="text-slate-400 mt-1">Run live model inference with real-world temporal features and transaction context.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
                {/* Form Column */}
                <div className="md:col-span-2 bg-graphite-800 border border-graphite-700 p-6 rounded-2xl h-fit">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">Transaction Amount ($)</label>
                            <input
                                type="number"
                                step="0.01"
                                className="w-full bg-graphite-700 border border-graphite-600 rounded-xl px-4 py-3 focus:outline-none focus:border-fraud-approve transition-colors"
                                value={formData.Amount}
                                onChange={(e) => setFormData({ ...formData, Amount: parseFloat(e.target.value) })}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">
                                <Clock className="inline mr-2" size={16} />
                                Transaction Time
                            </label>
                            <input
                                type="datetime-local"
                                className="w-full bg-graphite-700 border border-graphite-600 rounded-xl px-4 py-3 focus:outline-none focus:border-fraud-approve transition-colors"
                                value={formData.transaction_timestamp}
                                onChange={(e) => setFormData({ ...formData, transaction_timestamp: e.target.value })}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">Merchant Category</label>
                            <select
                                className="w-full bg-graphite-700 border border-graphite-600 rounded-xl px-4 py-3 focus:outline-none focus:border-fraud-approve transition-colors"
                                value={formData.merchant_category}
                                onChange={(e) => setFormData({ ...formData, merchant_category: e.target.value })}
                            >
                                <option value="electronics">Electronics</option>
                                <option value="clothing">Clothing</option>
                                <option value="food">Food & Dining</option>
                                <option value="gas">Gas Station</option>
                                <option value="grocery">Grocery</option>
                                <option value="entertainment">Entertainment</option>
                                <option value="travel">Travel</option>
                                <option value="healthcare">Healthcare</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-2">Transaction Type</label>
                            <select
                                className="w-full bg-graphite-700 border border-graphite-600 rounded-xl px-4 py-3 focus:outline-none focus:border-fraud-approve transition-colors"
                                value={formData.transaction_type}
                                onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
                            >
                                <option value="online">Online</option>
                                <option value="in_store">In Store</option>
                                <option value="atm">ATM</option>
                                <option value="mobile">Mobile</option>
                                <option value="recurring">Recurring</option>
                            </select>
                        </div>
                        <button
                            disabled={loading}
                            className="w-full bg-fraud-approve hover:bg-emerald-600 text-graphite-900 font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-transform active:scale-95 disabled:opacity-50"
                        >
                            {loading ? <RefreshCw className="animate-spin" size={20} /> : <Send size={20} />}
                            Process Transaction
                        </button>
                    </form>
                    {error && <p className="text-fraud-block text-xs mt-4 bg-fraud-block/10 p-2 rounded border border-fraud-block/20">{error}</p>}
                </div>

                {/* Results Column */}
                <div className="md:col-span-3">
                    <div className="bg-graphite-800 border border-graphite-700 rounded-2xl p-8 min-h-[350px] flex flex-col items-center justify-center text-center relative overflow-hidden">
                        {!result && !loading && (
                            <div className="space-y-4">
                                <div className="p-4 bg-graphite-700 rounded-full inline-block mx-auto">
                                    <Activity size={48} className="text-slate-500" />
                                </div>
                                <p className="text-slate-500 font-medium">Ready for input...</p>
                                <p className="text-slate-600 text-sm italic">Enhanced with real temporal features and transaction context for better fraud detection.</p>
                            </div>
                        )}

                        {loading && (
                            <div className="space-y-4">
                                <RefreshCw size={48} className="text-fraud-approve animate-spin mx-auto" />
                                <p className="text-fraud-approve font-bold tracking-widest text-sm uppercase">Calculating Risk Pattern</p>
                            </div>
                        )}

                        {result && UI && (
                            <div className={`w-full space-y-6 animate-in zoom-in-95 duration-300`}>
                                <div className={`p-6 ${UI.bg} ${UI.border} border rounded-full inline-block mx-auto`}>
                                    <UI.icon size={64} className={UI.color} />
                                </div>

                                <div>
                                    <h3 className={`text-4xl font-black ${UI.color} tracking-tight`}>{result.decision}</h3>
                                    <div className="text-slate-400 flex items-center justify-center gap-2 mt-2">
                                        <span className="text-xs uppercase font-bold tracking-widest">Risk Score:</span>
                                        <span className="font-mono text-white text-lg font-bold">{(result.risk_score * 100).toFixed(2)}%</span>
                                    </div>
                                </div>

                                <div className="bg-graphite-900/50 p-4 rounded-xl border border-graphite-700">
                                    <p className="text-sm text-slate-300 italic">"{result.explanation}"</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Simulator;
