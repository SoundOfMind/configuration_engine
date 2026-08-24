from __future__ import annotations

from configuration_engine.device_definition import DeviceProperty


class PropertyClassifier:
    """Classify device properties using metadata."""

    def is_diagnostic(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property is diagnostic."""

        return property.category == "diagnostic"

    def is_writable(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property is writable."""

        return property.access is not None and (property.access & 0x02) != 0

    def is_readable(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property is readable."""

        return property.access is not None and (property.access & 0x01) != 0

    def is_configuration(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property represents configuration."""

        return property.category == "config"

    def is_enum(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property is an enum."""

        return property.property_type == "enum"

    def is_numeric(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property is numeric."""

        return property.property_type == "numeric"

    def has_unit(
        self,
        property: DeviceProperty,
    ) -> bool:
        """Return True if the property has an engineering unit."""

        return property.unit is not None
