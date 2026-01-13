import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { endpointAPI } from "../services/api";
import { Activity, Plus, Trash2, ExternalLink, RefreshCw, BarChart2 } from "lucide-react";

export default function Dashboard() {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newEndpoint, setNewEndpoint] = useState({ name: "", url: "", method: "GET", interval: 60, slack_webhook_url: "", alert_email: "" });
  const navigate = useNavigate();

  const fetchEndpoints = async () => {
    try {
      const response = await endpointAPI.list();
      setEndpoints(response.data);
    } catch (err) {
      console.error("Failed to fetch endpoints", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEndpoints();
    const interval = setInterval(fetchEndpoints, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAddEndpoint = async (e) => {
    e.preventDefault();
    try {
      await endpointAPI.create(newEndpoint);
      setShowAddModal(false);
      setNewEndpoint({ name: "", url: "", method: "GET", interval: 60, slack_webhook_url: "", alert_email: "" });
      fetchEndpoints();
    } catch (err) {
      alert("Failed to add endpoint");
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (window.confirm("Are you sure?")) {
      await endpointAPI.delete(id);
      fetchEndpoints();
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="text-indigo-600" /> API Monitor Dashboard
        </h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition shadow-lg"
        >
          <Plus size={20} /> Add Endpoint
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <RefreshCw className="animate-spin text-indigo-600" size={40} />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {endpoints.map((ep) => {
            const endpointId = ep._id || ep.id;
            return (
              <div 
                key={endpointId} 
                onClick={() => navigate(`/endpoint/${endpointId}`)}
                className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:border-indigo-100 transition cursor-pointer group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-xl text-gray-800 group-hover:text-indigo-600 transition">{ep.name}</h3>
                    <p className="text-sm text-gray-500 truncate max-w-[200px]">{ep.url}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${ep.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                    {ep.is_active ? "UP" : "DOWN"}
                  </span>
                </div>
                
                <div className="flex items-center justify-between mt-8">
                  <div className="flex gap-2">
                    <span className="text-xs bg-gray-50 px-2 py-1 rounded border text-gray-600 font-mono">{ep.method}</span>
                    <span className="text-xs bg-gray-50 px-2 py-1 rounded border text-gray-600">{ep.interval}s</span>
                  </div>
                  <div className="flex gap-4">
                     <BarChart2 className="text-gray-400 group-hover:text-indigo-500" size={20} />
                    <button onClick={(e) => handleDelete(e, endpointId)} className="text-gray-400 hover:text-red-600 transition">
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <h2 className="text-2xl font-bold mb-6">Monitor New API</h2>
            <form onSubmit={handleAddEndpoint} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  required
                  className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                  value={newEndpoint.name}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, name: e.target.value })}
                  placeholder="e.g. Production API"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Target URL</label>
                <input
                  type="url"
                  required
                  className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                  value={newEndpoint.url}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, url: e.target.value })}
                  placeholder="https://api.example.com/health"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">HTTP Method</label>
                  <select
                    className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                    value={newEndpoint.method}
                    onChange={(e) => setNewEndpoint({ ...newEndpoint, method: e.target.value })}
                  >
                    <option>GET</option>
                    <option>POST</option>
                    <option>PUT</option>
                    <option>DELETE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Interval (s)</label>
                  <input
                    type="number"
                    min="10"
                    className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                    value={newEndpoint.interval}
                    onChange={(e) => setNewEndpoint({ ...newEndpoint, interval: parseInt(e.target.value) })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Slack Webhook URL (Optional)</label>
                <input
                  type="url"
                  className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                  value={newEndpoint.slack_webhook_url}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, slack_webhook_url: e.target.value })}
                  placeholder="https://hooks.slack.com/services/..."
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Alert Email (Optional)</label>
                <input
                  type="email"
                  className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
                  value={newEndpoint.alert_email}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, alert_email: e.target.value })}
                  placeholder="alerts@example.com"
                />
              </div>
              <div className="flex justify-end gap-3 mt-8">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-6 py-2 text-gray-500 font-medium">Cancel</button>
                <button type="submit" className="bg-indigo-600 text-white px-8 py-2 rounded-xl font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-200">Start Monitoring</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
