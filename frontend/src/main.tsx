import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './app/App';
import './index.css'; // Убедитесь, что файл index.css существует в src/

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);