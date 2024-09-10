from backend import routes
from backend.container import Container
from fastapi import FastAPI

# from fastapi.middleware.cors import CORSMiddleware
import uvicorn

container = Container()
container.config.openai.model.from_env("OPENAI_MODEL", default="gpt-3.5-turbo")
container.config.rentcast.api_key.from_env("RENTCAST_API_KEY")

app = FastAPI()
app.include_router(routes.router, prefix="/api")

# origins = [
#     "http://localhost",
#     "http://localhost:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
