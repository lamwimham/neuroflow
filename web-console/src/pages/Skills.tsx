import { useQuery } from '@tanstack/react-query';
import { skillApi } from '../api';
import { Wrench, Check } from 'lucide-react';

export default function Skills() {
  const { data: skills, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: skillApi.list,
  });

  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Skills</h1>

      {isLoading ? (
        <div className="text-center text-gray-400 py-12">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {skills?.data?.map((skill: any) => (
            <div
              key={skill.id}
              className="bg-gray-800 rounded-lg border border-gray-700 p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-600 rounded-lg">
                    <Wrench className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{skill.name}</h3>
                    <p className="text-sm text-gray-400">v{skill.version}</p>
                  </div>
                </div>
                {skill.installed && (
                  <Check className="h-5 w-5 text-green-500" />
                )}
              </div>

              <p className="text-sm text-gray-400 mb-4">{skill.description}</p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">{skill.category}</span>
                <button className="text-sm text-indigo-400 hover:text-indigo-300">
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
