// ==============================================================================
// PROJECT: PERSONAL_WEB_SPACE
// LOCATION: /frontend/src/App.tsx
// DESCRIPTION: Главный контейнер приложения.
// ==============================================================================

import React from 'react';
import { BotBuilder } from './components/BotBuilder';
import './App.css'; // Убедись, что этот файл существует, иначе React выдаст ошибку

function App() {
  return (
    // Чистый контейнер для BotBuilder, без лишних элементов шаблона Vite
    <div className="w-screen h-screen overflow-hidden bg-[#020617]">
      <BotBuilder />
    </div>
  );
}

export default App;