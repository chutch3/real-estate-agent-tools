from fastapi import APIRouter

from backend.routes import chat, documents, geocode, internal, layers, net_sheet, posts, properties, templates

router = APIRouter()
router.include_router(properties.router)
router.include_router(net_sheet.router)
router.include_router(chat.router)
router.include_router(documents.router)
router.include_router(posts.router)
router.include_router(geocode.router)
router.include_router(templates.router)
router.include_router(layers.router)
router.include_router(internal.router)
