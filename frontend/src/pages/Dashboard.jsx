import { useState, useEffect } from "react";
import { endpointAPI } from "../services/api";
import { Activity, Plus, Trash2, ExternalLink, RefreshCw } from "lucide-react";

export default function Dashboard() {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newEndpoint, setNewEndpoint] = useState({ name: "", url: "", method: "GET", interval: 60 });

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
    const interval = setInterval(fetchEndpoints, 30000); // Auto refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleAddEndpoint = async (e) => {
    e.preventDefault();
    try {
      await endpointAPI.create(newEndpoint);
      setShowAddModal(false);
      setNewEndpoint({ name: "", url: "", method: "GET", interval: 60 });
      fetchEndpoints();
    } catch (err) {
      alert("Failed to add endpoint");
    }
  };

  const handleDelete = async (id) => {
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
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition"
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
          {endpoints.map((ep) => (
            <div key={ep.id} className="bg-white p-6 rounded-xl shadow-md border border-gray-100 hover:shadow-lg transition">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-xl text-gray-800">{ep.name}</h3>
                  <p className="text-sm text-gray-500 truncate max-w-[200px]">{ep.url}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-bold ${ep.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                  {ep.is_active ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>
              
              <div className="flex items-center justify-between mt-6">
                <div className="flex gap-2">
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 font-mono">{ep.method}</span>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">{ep.interval}s</span>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => handleDelete(ep.id)} className="text-red-500 hover:text-red-700">
                    <Trash2 size={18} />
                  </button>
                  <a href={ep.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-700">
                    <ExternalLink size={18} />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-6">Add New Endpoint</h2>
            <form onSubmit={handleAddEndpoint} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                  value={newEndpoint.name}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">URL</label>
                <input
                  type="url"
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                  value={newEndpoint.url}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, url: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Method</label>
                  <select
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
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
                  <label className="block text-sm font-medium text-gray-700">Interval (s)</label>
                  <input
                    type="number"
                    min="10"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    value={newEndpoint.interval}
                    onChange={(e) => setNewEndpoint({ ...newEndpoint, interval: parseInt(e.target.value) })}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-4 mt-8">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 text-gray-600">Cancel</button>
                <button type="submit" className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
