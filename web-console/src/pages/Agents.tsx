import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentApi } from '../api';
import { Bot, Plus, Trash2, Edit, Play } from 'lucide-react';

export default function Agents() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: agentApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => agentApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Agents</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Agent
        </button>
      </div>

      {isLoading ? (
        <div className="text-center text-gray-400 py-12">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {agents?.data?.map((agent: any) => (
            <div
              key={agent.id}
              className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-indigo-500 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-indigo-600 rounded-lg">
                    <Bot className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{agent.name}</h3>
                    <p className="text-sm text-gray-400">{agent.status}</p>
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-400 mb-4">{agent.description}</p>

              <div className="flex items-center justify-between">
                <a
                  href={`/agents/${agent.id}`}
                  className="flex items-center px-3 py-1.5 text-sm text-indigo-400 hover:text-indigo-300"
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </a>
                <button
                  onClick={() => deleteMutation.mutate(agent.id)}
                  className="flex items-center px-3 py-1.5 text-sm text-red-400 hover:text-red-300"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
