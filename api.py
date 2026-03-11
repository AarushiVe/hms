"""API routes entrypoint for structured backend layout.

This module re-exports the active Flask blueprint implemented in `app/api.py`.
"""

from app.api import api_bp

__all__ = ["api_bp"]
