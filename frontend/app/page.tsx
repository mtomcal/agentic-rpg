'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api/client';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    apiClient.healthCheck()
      .then(data => setHealthStatus(data.status))
      .catch(() => setHealthStatus('error'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Agentic RPG</h1>
        <p className="text-xl mb-2">Backend Status: {healthStatus}</p>
        <p className="text-gray-600">Foundation setup complete</p>
      </div>
    </main>
  );
}
