Every piece of information should have one authoritative source.

Trust the backend.

Adapt to the user's environment whenever practical. Avoid requiring users to reorganize their home or naming conventions just to use the tool.

Avoid duplicate sources of truth.

Commands should read like short English sentences.

Never write a property that doesn't need to change.

Don't create a new domain object until you discover information that cannot naturally live in an existing one.

Never leave the user wondering whether the program is working.

Verification is based on observed device state, not acknowledgements.

Configuration Engine does not create configurations; it reproduces known-good configurations. Device-specific editing belongs in Home Assistant or Zigbee2MQTT.

