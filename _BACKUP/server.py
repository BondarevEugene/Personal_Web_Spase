from fastapi import FastAPI
from core.lifespan import lifespan
from core.static import mount_static


app = FastAPI(
    title="OMNIFACTORY",
    lifespan=lifespan
)


mount_static(app)
