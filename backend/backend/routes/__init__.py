from fastapi import APIRouter

from backend.routes import (
    chat,
    consumer,
    documents,
    geocode,
    identity,
    internal,
    layers,
    magic_links,
    net_sheet,
    posts,
    properties,
    templates,
)

router = APIRouter()
router.include_router(identity.router)
router.include_router(properties.router)
router.include_router(net_sheet.router)
router.include_router(chat.router)
router.include_router(documents.router)
router.include_router(posts.router)
router.include_router(geocode.router)
router.include_router(templates.router)
router.include_router(layers.router)
router.include_router(internal.router)
router.include_router(magic_links.router)
router.include_router(consumer.router)
