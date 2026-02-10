"""
Tabs-modulen innehåller separata renderingsfunktioner för varje dashboard-flik.
"""

from .owner_types import (
    render_gender_analysis,
    render_age_analysis,
    render_owner_type_comparison
)

__all__ = [
    'render_gender_analysis',
    'render_age_analysis',
    'render_owner_type_comparison'
]

