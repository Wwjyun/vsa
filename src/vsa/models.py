"""Small value objects shared by views and services."""

from __future__ import annotations

from dataclasses import dataclass

from vsa.paths import validate_component


@dataclass(frozen=True, slots=True)
class InspectionSelection:
    product: str
    lot_id: str
    component_id: str
    stage: str = ""

    def validated(self, *, require_stage: bool = True) -> "InspectionSelection":
        product = validate_component(self.product, "Product")
        lot_id = validate_component(self.lot_id, "Lot ID")
        component_id = validate_component(self.component_id, "Component ID")
        stage = self.stage.strip()
        if require_stage:
            stage = validate_component(stage, "Stage")
        return InspectionSelection(product, lot_id, component_id, stage)
