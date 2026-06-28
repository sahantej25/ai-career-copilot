from fastapi import APIRouter, Depends

from deps.auth import bind_user_context
from models.schemas import AppData
from services import storage_service as store

router = APIRouter(prefix="/api/data", tags=["data"], dependencies=[Depends(bind_user_context)])


@router.get("")
async def get_all_data() -> AppData:
    """Return the entire data.json (single source of truth)."""
    return await store.load_data()


@router.post("/clear")
async def clear_all_data():
    """Clear All Data — wipes the JSON file back to an empty state."""
    fresh = await store.reset_data()
    return {"message": "All data cleared.", "data": fresh}
