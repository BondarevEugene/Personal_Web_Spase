@app.get("/api/v1/admin/telemetry")
async def get_admin_telemetry():
    return {
        "cpu": round(random.uniform(8.0, 18.0), 1),
        "ram": round(random.uniform(2.4, 3.2), 2)
    }

@app.get("/api/v1/status")
async def get_active_bots_status():
    return [
        {"id": "@Web_FactoryBot", "status": "ONLINE"},
        {"id": "Support_Agent_Bot", "status": "SYNCING"}
    ]


@app.get("/api/v1/registry", response_model=RegistryResponse, tags=["Когнитивный Реестр"])
async def get_registry():
    try:
        if hasattr(registry, 'modules') and registry.modules:
            return {"categories": registry.modules}
    except Exception:
        pass
    return {"categories": safe_load_registry_json()}

# Теперь здесь идут твои эндпоинты
@app.get("/api/admin/clients")
async def get_clients(db: Session = Depends(get_db)):
    class Registry:
        def __init__(self, path=None):
            self.modules = {"Core": {"fastapi": {"title": "FastAPI Core", "color": "purple", "fields": {}}}}

    ###################### импорты MAIN.PY ################################

    @app.get("/api/admin/clients")
    async def get_clients(db: Session = Depends(get_db)):
        # Запрос всех клиентов из БД
        clients = db.query(Client).all()
        # Конвертация в формат, понятный фронтенду
        return [
            {
                "full_name": c.full_name,
                "company": c.company,
                "phone": c.phone,
                "email": c.email,
                "bot_id": c.bot_id,
                "notes": c.notes
            } for c in clients
        ]

    @app.get("/api/registry")
    def get_registry():
        """Отдает список 51 модуля для левой панели конструктора"""
        return ModuleManager.get_ui_registry()


    @app.post("/api/deploy/{client_id}/{bot_id}")
    def deploy_bot(client_id: int, bot_id: int, graph_data: dict):
        """Принимает JSON от Drawflow и запускает генерацию кода"""
        compiler = BotCompiler(client_id, bot_id, graph_data)
        result = compiler.build()

        # Изменение статуса в БД на 'production'
        # db.update_bot_status(bot_id, 'production')

        return {"status": "success", "message": result}

@app.get("/api/admin/clients")
async def get_clients(db: Session = Depends(get_db)):
    # Запрос всех клиентов из БД
    clients = db.query(Client).all()
    # Конвертация в формат, понятный фронтенду
    return [
        {
            "full_name": c.full_name,
            "company": c.company,
            "phone": c.phone,
            "email": c.email,
            "bot_id": c.bot_id,
            "notes": c.notes
        } for c in clients
    ]
