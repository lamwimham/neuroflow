export default function Settings() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-white mb-8">Settings</h1>

      <div className="max-w-2xl">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">General Settings</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                API Endpoint
              </label>
              <input
                type="text"
                defaultValue="http://localhost:8000"
                className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Log Level
              </label>
              <select className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-indigo-500">
                <option>DEBUG</option>
                <option>INFO</option>
                <option>WARNING</option>
                <option>ERROR</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Sandbox Settings</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Enable Seccomp</p>
                <p className="text-sm text-gray-400">Restrict system calls for security</p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-indigo-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">Network Isolation</p>
                <p className="text-sm text-gray-400">Isolate network access</p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-indigo-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
