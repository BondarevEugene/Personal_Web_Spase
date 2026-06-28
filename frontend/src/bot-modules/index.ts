// 1. Используем import.meta.glob для автоматического поиска
const modules = import.meta.glob('./*.ts', { eager: true });

// 2. ЯВНО экспортируем объект BOT_REGISTRY
export const BOT_REGISTRY: Record<string, any> = {};

// 3. Заполняем его
Object.entries(modules).forEach(([path, module]: [string, any]) => {
  const fileName = path.split('/').pop()?.replace('.ts', '');

  if (fileName && fileName !== 'index') {
    // Используем default экспорт из файлов модулей
    BOT_REGISTRY[fileName] = module.default || module;
  }
});