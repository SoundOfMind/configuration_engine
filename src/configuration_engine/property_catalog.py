from __future__ import annotations

from typing import ClassVar

from configuration_engine.property_metadata import PropertyMetadata


class PropertyCatalog:
    """Metadata describing known properties."""

    _metadata: ClassVar[dict[str, PropertyMetadata]] = {
        "linkquality": PropertyMetadata(
            writable=False,
            display_name="Link Quality",
        ),
        "internalTemperature": PropertyMetadata(
            writable=False,
            display_name="Internal Temperature",
        ),
    }

    @classmethod
    def metadata(
        cls,
        property_name: str,
    ) -> PropertyMetadata:
        return cls._metadata.get(
            property_name,
            PropertyMetadata(),
        )
