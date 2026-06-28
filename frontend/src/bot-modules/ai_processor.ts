import { Brain } from 'lucide-react';

export default {
  id: 'ai_processor',
  name: 'Neural Engine V1',
  icon: Brain,
  // Тут можно добавить параметры, которые будут отображаться в UI
  inputs: ['text', 'context'],
  outputs: ['response']
};