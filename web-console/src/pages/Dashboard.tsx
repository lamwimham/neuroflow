import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../api';
import { Activity, Users, Wrench, Zap } from 'lucide-react';

export default function Dashboard() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: monitoringApi.metrics,
    refetchInterval: 5000,
  });

  const stats = [
    {
      name: 'Active Agents',
      value: metrics?.data?.agents?.active || 3,
      icon: Users,
      change: '+2',
      changeType: 'positive',
    },
    {
      name: 'Available Skills',
      value: metrics?.data?.skills?.total || 12,
      icon: Wrench,
      change: '+4',
      changeType: 'positive',
    },
    {
      name: 'Requests/min',
      value: metrics?.data?.requests?.perMinute || 42,
      icon: Activity,
      change: '+12%',
      changeType: 'positive',
    },
    {
      name: 'Avg Latency',
      value: `${metrics?.data?.performance?.avgLatency || 45}ms`,
      icon: Zap,
      change: '-8ms',
      changeType: 'positive',
    },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-gray-800 rounded-lg p-6 border border-gray-700"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-10 w-10 text-indigo-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">{stat.name}</p>
                <p className="text-2xl font-semibold text-white">{stat.value}</p>
              </div>
            </div>
            <div className="mt-4">
              <span className="text-sm text-green-400">{stat.change}</span>
              <span className="text-sm text-gray-500 ml-2">from last hour</span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-start space-x-3 pb-4 border-b border-gray-700 last:border-0">
              <div className="h-2 w-2 mt-2 bg-indigo-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm text-gray-300">Agent executed tool "search"</p>
                <p className="text-xs text-gray-500">2 minutes ago</p>
              </div>
              <span className="text-xs text-gray-500">123ms</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
