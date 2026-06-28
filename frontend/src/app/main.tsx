import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App'; // Импорт основного компонента App
import '../index.css';    // Импорт стилей (проверьте, что index.css лежит в папке src/)
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);