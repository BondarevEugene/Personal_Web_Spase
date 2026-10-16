// Функция навигации без перезагрузки
async function navigateTo(workspaceId) {
    try {
        const response = await fetch(`/api/v1/workspaces/open/${workspaceId}`);
        if (!response.ok) throw new Error('Ошибка загрузки');

        const data = await response.json(); // Получаем { "content": "..." }

        const container = document.getElementById('main-content');
        if (container) {
            container.innerHTML = data.content; // Вставляем HTML
        }
    } catch (err) {
        console.error("Navigation error:", err);
    }
}

// Инициализация событий для боковой панели
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.addEventListener('click', (e) => {
            const link = e.target.closest('[data-workspace-id]');
            if (link) {
                const id = link.getAttribute('data-workspace-id');
                navigateTo(id);
            }
        });
    }
});