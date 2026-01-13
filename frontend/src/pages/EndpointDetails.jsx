import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { endpointAPI } from "../services/api";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from "chart.js";
import { ArrowLeft, Clock, CheckCircle, XCircle, RefreshCw, Settings, Save } from "lucide-react";
import { format } from "date-fns";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function EndpointDetails() {
  const { id } = useParams();
  const [endpoint, setEndpoint] = useState(null);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [editData, setEditData] = useState({ slack_webhook_url: "", alert_email: "" });

  const fetchData = async () => {
    try {
      const [epRes, statsRes, logsRes] = await Promise.all([
        endpointAPI.get(id),
        endpointAPI.getStats(id),
        endpointAPI.getLogs(id),
      ]);
      setEndpoint(epRes.data);
      setStats(statsRes.data);
      setLogs(logsRes.data);
      setEditData({ 
        slack_webhook_url: epRes.data.slack_webhook_url || "",
        alert_email: epRes.data.alert_email || ""
      });
    } catch (err) {
      console.error("Error fetching details:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      await endpointAPI.update(id, editData);
      alert("Settings updated successfully");
      fetchData();
    } catch (err) {
      alert("Failed to update settings");
    } finally {
      setUpdating(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [id]);

  if (loading) return (
    <div className="flex justify-center items-center min-h-screen">
      <RefreshCw className="animate-spin text-indigo-600" size={48} />
    </div>
  );
  if (!endpoint) return <div className="p-8 text-center">Endpoint not found</div>;

  const chartLogs = [...logs].reverse();
  const chartData = {
    labels: chartLogs.map((log) => format(new Date(log.checked_at), "HH:mm:ss")),
    datasets: [
      {
        label: "Response Time (ms)",
        data: chartLogs.map((log) => log.response_time_ms),
        borderColor: "rgb(79, 70, 229)",
        backgroundColor: "rgba(79, 70, 229, 0.5)",
        tension: 0.2,
        fill: true,
      },
    ],
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="inline-flex items-center text-indigo-600 hover:text-indigo-900 font-medium">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard
        </Link>
      </div>

      <div className="bg-white shadow-xl rounded-2xl overflow-hidden mb-8">
        <div className="bg-indigo-600 px-6 py-8 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">{endpoint.name}</h1>
              <p className="opacity-80 mt-1">{endpoint.url}</p>
            </div>
            <div className={`px-4 py-2 rounded-full font-bold border-2 ${endpoint.is_active ? "bg-green-500/20 border-green-400" : "bg-red-500/20 border-red-400"}`}>
              {endpoint.is_active ? "SYSTEMS ACTIVE" : "SYSTEMS DOWN"}
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x border-t">
          <div className="p-6 text-center">
            <p className="text-sm text-gray-500 uppercase font-semibold">Uptime Percentage</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.uptime_percentage}%</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-sm text-gray-500 uppercase font-semibold">Avg Response Time</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.average_response_time} ms</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-sm text-gray-500 uppercase font-semibold">Total Checks</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_checks}</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-sm text-gray-500 uppercase font-semibold">Method / Interval</p>
            <p className="text-2xl font-bold text-gray-900">{endpoint.method} / {endpoint.interval}s</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white shadow-lg rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Clock className="text-indigo-600" /> Response Time History
          </h2>
          <div className="h-[400px]">
            <Line 
              data={chartData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true } }
              }} 
            />
          </div>
        </div>

        <div className="bg-white shadow-lg rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b bg-gray-50">
            <h2 className="text-xl font-bold">Recent Incident Log</h2>
          </div>
          <div className="divide-y max-h-[480px] overflow-y-auto">
            {logs.map((log) => (
              <div key={log.id} className="p-4 hover:bg-gray-50 transition">
                <div className="flex justify-between items-start">
                  <div className="flex gap-3">
                    {log.success ? (
                      <CheckCircle className="text-green-500 mt-1" size={18} />
                    ) : (
                      <XCircle className="text-red-500 mt-1" size={18} />
                    )}
                    <div>
                      <p className="font-bold text-gray-800">
                        {log.success ? `Success: ${log.status_code}` : "Request Failed"}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(log.checked_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-mono text-gray-400">{log.response_time_ms}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 bg-white shadow-lg rounded-2xl p-6 border-l-4 border-indigo-600">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Settings className="text-gray-600" size={20} /> Notification Settings
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Slack Webhook URL</label>
            <input
              type="url"
              className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
              value={editData.slack_webhook_url}
              onChange={(e) => setEditData({ ...editData, slack_webhook_url: e.target.value })}
              placeholder="https://hooks.slack.com/services/..."
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Alert Email</label>
            <input
              type="email"
              className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500 outline-none"
              value={editData.alert_email}
              onChange={(e) => setEditData({ ...editData, alert_email: e.target.value })}
              placeholder="alerts@example.com"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            onClick={handleUpdate}
            disabled={updating}
            className="bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-indigo-700 shadow-lg flex items-center gap-2 disabled:opacity-50"
          >
            {updating ? <RefreshCw className="animate-spin" size={20} /> : <Save size={20} />}
            Save Changes
          </button>
        </div>
        <p className="mt-4 text-sm text-gray-500 italic">
          We will notify these channels whenever the status of this API changes.
        </p>
      </div>
    </div>
  );
}