import { useState, useCallback } from 'react';
import type { Node, Edge } from '@xyflow/react';

// Определяем интерфейс для ответа от сервера (контракт данных)
interface FlowResponse {
  nodes: { id: string | number; label: string }[];
  edges: Edge[];
}

export const useProjectFlow = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggerCoreFlow = useCallback(async (idea: string) => {
    if (!idea.trim()) {
      setError("Идея не может быть пустой");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/plan-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, timestamp: Date.now() })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Ошибка сервера: ${response.status}`);
      }

      const data: FlowResponse = await response.json();

      // Маппинг данных с приведением типов
      const formattedNodes: Node[] = (data.nodes || []).map((n, i) => ({
        id: String(n.id),
        type: 'default',
        data: { label: n.label || 'Task' },
        position: { x: 100 + (i * 200), y: 100 + (i % 2 === 0 ? 50 : -50) },
        style: {
          background: '#0f172a',
          color: '#22d3ee',
          border: '1px solid #06b6d4',
          borderRadius: '8px',
          padding: '10px'
        }
      }));

      setNodes(formattedNodes);
      setEdges(data.edges || []);

    } catch (err) {
      const message = err instanceof Error ? err.message : "Неизвестная ошибка сети";
      setError(message);
      console.error("OmniFactory Flow Error:", message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { nodes, edges, loading, error, triggerCoreFlow };
};