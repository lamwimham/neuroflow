import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../api';
import { Activity, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Monitoring() {
  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    queryFn: monitoringApi.metrics,
    refetchInterval: 5000,
  });

  // Mock data for chart
  const chartData = [
    { time: '00:00', latency: 45, requests: 120 },
    { time: '04:00', latency: 42, requests: 95 },
    { time: '08:00', latency: 48, requests: 180 },
    { time: '12:00', latency: 52, requests: 220 },
    { time: '16:00', latency: 46, requests: 195 },
    { time: '20:00', latency: 44, requests: 150 },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Monitoring</h1>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">P99 Latency</p>
              <p className="text-2xl font-bold text-white">85ms</p>
            </div>
            <Activity className="h-10 w-10 text-indigo-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Error Rate</p>
              <p className="text-2xl font-bold text-white">0.02%</p>
            </div>
            <AlertCircle className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Throughput</p>
              <p className="text-2xl font-bold text-white">245/min</p>
            </div>
            <TrendingUp className="h-10 w-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Uptime</p>
              <p className="text-2xl font-bold text-white">99.9%</p>
            </div>
            <Clock className="h-10 w-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Latency Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Line type="monotone" dataKey="latency" stroke="#6366F1" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Requests Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Line type="monotone" dataKey="requests" stroke="#10B981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Logs */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Logs</h3>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex items-start space-x-3 text-sm">
              <span className="text-gray-500 font-mono">2024-01-15 10:30:{i.toString().padStart(2, '0')}</span>
              <span className="text-green-400">INFO</span>
              <span className="text-gray-300">Agent executed successfully</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
