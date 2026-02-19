import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tantml:react-query';
import { agentApi, skillApi } from '../api';
import { ArrowLeft, Send, Bot, Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AgentDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState<any[]>([]);

  const { data: agent } = useQuery({
    queryKey: ['agent', id],
    queryFn: () => agentApi.get(id!),
  });

  const executeMutation = useMutation({
    mutationFn: (msg: string) => agentApi.execute(id!, msg),
    onSuccess: (response) => {
      setConversation(prev => [...prev, { role: 'user', content: message }]);
      setConversation(prev => [...prev, { role: 'assistant', content: response.data.result }]);
      setMessage('');
    },
  });

  const handleSend = () => {
    if (message.trim()) {
      executeMutation.mutate(message);
    }
  };

  return (
    <div>
      <Link to="/agents" className="flex items-center text-gray-400 hover:text-white mb-6">
        <ArrowLeft className="h-5 w-5 mr-2" />
        Back to Agents
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Info */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-indigo-600 rounded-lg">
                <Bot className="h-8 w-8 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{agent?.data?.name}</h2>
                <p className="text-sm text-gray-400">{agent?.data?.status}</p>
              </div>
            </div>

            <p className="text-sm text-gray-400 mb-4">{agent?.data?.description}</p>

            <div className="border-t border-gray-700 pt-4">
              <h3 className="text-sm font-semibold text-white mb-3">Skills</h3>
              <div className="space-y-2">
                {agent?.data?.skills?.map((skill: any) => (
                  <div key={skill} className="flex items-center text-sm text-gray-400">
                    <Wrench className="h-4 w-4 mr-2" />
                    {skill}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">Debug Console</h3>
            </div>

            <div className="h-96 overflow-y-auto p-4 space-y-4">
              {conversation.length === 0 ? (
                <div className="text-center text-gray-500 py-12">
                  Start a conversation with the agent...
                </div>
              ) : (
                conversation.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-700 text-gray-100'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-gray-700">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Type a message..."
                  className="flex-1 bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleSend}
                  disabled={executeMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
