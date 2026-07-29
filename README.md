# configuration_engine

Deterministic configuration management for home automation devices

Rather than manually configuring every Zigbee device through Zigbee2MQTT,
z2m_config_manager treats device configuration as code.

Features:

- Snapshot device configuration
- Compare devices
- Detect configuration drift
- Generate reusable profiles
- Plan changes before applying them
- Verify every applied change