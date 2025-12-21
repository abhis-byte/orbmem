# engines/base_engine.py

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseEngine(ABC):
    """
    Abstract base class for all OCDB engines.
    Defines optional generic methods common across engines.
    """

    # -------------------------------
    # MEMORY-LIKE INTERFACES
    # -------------------------------
    def set(self, key: str, value: Any, **kwargs):
        raise NotImplementedError("set() not implemented for this engine")

    def get(self, key: str) -> Any:
        raise NotImplementedError("get() not implemented for this engine")

    def delete(self, key: str):
        raise NotImplementedError("delete() not implemented for this engine")

    # -------------------------------
    # GRAPH-LIKE INTERFACES
    # -------------------------------
    def add_node(self, *args, **kwargs):
        raise NotImplementedError("add_node() not implemented")

    def get_path(self, *args, **kwargs):
        raise NotImplementedError("get_path() not implemented")

    # -------------------------------
    # VECTOR-LIKE INTERFACES
    # -------------------------------
    def add_text(self, *args, **kwargs):
        raise NotImplementedError("add_text() not implemented")

    def search(self, *args, **kwargs):
        raise NotImplementedError("search() not implemented")

    # -------------------------------
    # SAFETY-LIKE INTERFACES
    # -------------------------------
    def scan(self, *args, **kwargs):
        raise NotImplementedError("scan() not implemented")
