from __future__ import annotations

from configuration_engine.property_catalog import PropertyCatalog


def test_known_property() -> None:
    metadata = PropertyCatalog.metadata(
        "linkquality",
    )

    assert not metadata.writable


def test_unknown_property() -> None:
    metadata = PropertyCatalog.metadata(
        "minimumLevel",
    )

    assert metadata.writable
