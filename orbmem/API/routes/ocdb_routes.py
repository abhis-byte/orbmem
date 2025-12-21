# API/routes/ocdb_routes.py

from typing import Dict
from fastapi import APIRouter, Depends

from orbmem.API.dependencies import require_auth
from orbmem.core.ocdb import OCDB
from orbmem.utils.exceptions import ValidationError

router = APIRouter(prefix="/v1", tags=["OCDB"])

# ---------------------------------------------------------
# PER-USER OCDB CACHE (IN-MEMORY)
# ---------------------------------------------------------
_OCDB_CACHE: Dict[str, OCDB] = {}


def get_ocdb_for_user(uid: str) -> OCDB:
    """
    Get or create a per-user OCDB instance.
    Ensures strict user data isolation.
    """
    ocdb = _OCDB_CACHE.get(uid)

    if ocdb is None:
        ocdb = OCDB(uid)
        _OCDB_CACHE[uid] = ocdb

    return ocdb


# =========================================================
# MEMORY ROUTES
# =========================================================

@router.post("/memory/set")
def set_memory(
    data: dict,
    auth=Depends(require_auth),
):
    key = data.get("key")
    value = data.get("value")

    if not key:
        raise ValidationError("Missing required field: key")

    session_id = data.get("session_id")
    ttl = data.get("ttl")

    ocdb = get_ocdb_for_user(auth["uid"])
    ocdb.memory_set(
        key,
        value,
        session_id=session_id,
        ttl_seconds=ttl,
    )

    return {
        "status": "ok",
        "key": key,
    }


@router.get("/memory/get")
def get_memory(
    key: str,
    auth=Depends(require_auth),
):
    ocdb = get_ocdb_for_user(auth["uid"])
    value = ocdb.memory_get(key)

    return {
        "key": key,
        "value": value,
    }


@router.get("/memory/keys")
def list_memory_keys(auth=Depends(require_auth)):
    ocdb = get_ocdb_for_user(auth["uid"])
    return {
        "keys": ocdb.memory_keys(),
    }


@router.delete("/memory/delete")
def delete_memory(
    key: str,
    auth=Depends(require_auth)
):
    ocdb = get_ocdb_for_user(auth["uid"])
    ocdb.memory.delete(key, user_id=auth["uid"])

    return {
        "status": "ok",
        "deleted": key
    }


# =========================================================
# VECTOR ROUTES
# =========================================================

@router.post("/vector/search")
def vector_search(
    data: dict,
    auth=Depends(require_auth),
):
    query = data.get("query")
    k = data.get("k", 5)

    if not query:
        raise ValidationError("Missing field: query")

    ocdb = get_ocdb_for_user(auth["uid"])
    results = ocdb.vector_search(query, k=k)

    return {
        "query": query,
        "results": results,
    }


@router.post("/vector/add")
def vector_add(
    data: dict,
    auth=Depends(require_auth),
):
    text = data.get("text")
    doc_id = data.get("id")

    if not text or not doc_id:
        raise ValidationError("Missing field: id or text")

    payload = {
        "id": doc_id,
    }

    ocdb = get_ocdb_for_user(auth["uid"])
    ocdb.vector_add(text, payload)

    return {
        "status": "ok",
        "id": doc_id,
    }


# =========================================================
# GRAPH ROUTES
# =========================================================

@router.post("/graph/add_step")
def graph_add_step(
    data: dict,
    auth=Depends(require_auth),
):
    node_id = data.get("node_id")
    content = data.get("content")
    parent = data.get("parent")

    if not node_id or not content:
        raise ValidationError("Missing field: node_id or content")

    ocdb = get_ocdb_for_user(auth["uid"])
    ocdb.graph_add(node_id, content, parent)

    return {
        "status": "ok",
        "node": node_id,
    }


@router.get("/graph/path")
def graph_path(
    node_a: str,
    node_b: str,
    auth=Depends(require_auth),
):
    ocdb = get_ocdb_for_user(auth["uid"])
    path = ocdb.graph_path(node_a, node_b)

    return {
        "from": node_a,
        "to": node_b,
        "path": path,
    }


# =========================================================
# SAFETY ROUTES
# =========================================================

@router.post("/safety/scan")
def safety_scan(
    data: dict,
    auth=Depends(require_auth),
):
    text = data.get("text")

    if not text:
        raise ValidationError("Missing field: text")

    ocdb = get_ocdb_for_user(auth["uid"])
    events = ocdb.safety_scan(text)

    return {
        "input": text,
        "events": events,
    }


# =========================================================
# ROOT
# =========================================================

@router.get("/")
def root():
    return {
        "message": "OCDB API v1 online",
    }