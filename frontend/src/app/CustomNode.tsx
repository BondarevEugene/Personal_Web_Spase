import { Handle, Position } from '@xyflow/react';

export const CustomNode = ({ data }: { data: any }) => (
  <div className="custom-node">
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      {data.icon && <data.icon size={18} color="#0ff" />}
      <span style={{ fontWeight: 'bold' }}>{data.label}</span>
    </div>
    <Handle type="target" position={Position.Left} style={{ background: '#0ff' }} />
    <Handle type="source" position={Position.Right} style={{ background: '#0ff' }} />
  </div>
);