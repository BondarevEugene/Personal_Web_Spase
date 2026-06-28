import React from 'react';
import {
  Cpu,
  Zap,
  ShoppingCart,
  MessageSquare,
  Shield,
  Code
} from 'lucide-react';

// 1. Определение интерфейса
export interface BotModule {
  id: string;
  label: string;
  cat: string;
  desc: string;
  icon: React.ElementType;
}

// 2. Объявление массива с явной типизацией BotModule[]
export const ALL_MODULES: BotModule[] = [
  {
    id: 'core_v4',
    label: 'Kernel_V4',
    cat: 'core',
    desc: 'Core system engine',
    icon: Cpu
  },
  {
    id: 'ai_neural',
    label: 'Neural_Link',
    cat: 'ai',
    desc: 'AI Neural processing',
    icon: Zap
  },
  {
    id: 'shop_matrix',
    label: 'Trans_Matrix',
    cat: 'shop',
    desc: 'E-commerce sync',
    icon: ShoppingCart
  },
  {
    id: 'logic_gate',
    label: 'Logic_Gate',
    cat: 'logic',
    desc: 'Integration logic',
    icon: Code
  }
];