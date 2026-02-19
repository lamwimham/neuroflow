import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Agent API
export const agentApi = {
  list: () => api.get('/agents'),
  get: (id: string) => api.get(`/agents/${id}`),
  create: (data: any) => api.post('/agents', data),
  update: (id: string, data: any) => api.put(`/agents/${id}`, data),
  delete: (id: string) => api.delete(`/agents/${id}`),
  execute: (id: string, message: string) => api.post(`/agents/${id}/execute`, { message }),
};

// Skill API
export const skillApi = {
  list: () => api.get('/skills'),
  get: (id: string) => api.get(`/skills/${id}`),
  assign: (agentId: string, skillId: string) => api.post(`/agents/${agentId}/skills/${skillId}`),
  remove: (agentId: string, skillId: string) => api.delete(`/agents/${agentId}/skills/${skillId}`),
};

// Monitoring API
export const monitoringApi = {
  metrics: () => api.get('/monitoring/metrics'),
  traces: () => api.get('/monitoring/traces'),
  logs: (params?: any) => api.get('/monitoring/logs', { params }),
};

// MCP API
export const mcpApi = {
  servers: () => api.get('/mcp/servers'),
  tools: (serverName: string) => api.get(`/mcp/servers/${serverName}/tools`),
  execute: (serverName: string, toolName: string, args: any) => 
    api.post(`/mcp/servers/${serverName}/tools/${toolName}/execute`, args),
};
