# Configuration Engine Architecture

Configuration Engine is designed around a simple principle:

> **Determine the difference between the desired state and the actual state,
> then make only the changes required to eliminate that difference.**

The engine is deterministic, backend-independent, and built from small,
single-purpose components.

---

# High-Level Architecture

```
                 Desired State
                      │
        ┌─────────────┴─────────────┐
        │                           │
     Profile                     Device
        │                           │
        └─────────────┬─────────────┘
                      ▼
               DeviceSnapshot
                      │
                      ▼
             SnapshotComparer
                      │
                      ▼
             ConfigurationDiff
                      │
                      ▼
              Execution Planner
                      │
              (Dry Run / Confirm)
                      │
                      ▼
               Backend Adapter
                      │
                      ▼
                   Device
                      │
                      ▼
               Read Back / Verify
```

Every modification follows the same workflow:

1. Read the current state.
2. Determine the desired state.
3. Compare the two.
4. Display the planned changes.
5. Apply the changes.
6. Verify the result.

---

# Architecture Principles

## Single Responsibility

Every class has one responsibility.

Examples:

- `SnapshotParser` converts backend payloads into `DeviceSnapshot` objects.
- `SnapshotComparer` compares snapshots.
- `ConfigurationLoader` reads persistent application configuration.
- `Zigbee2MqttBackend` translates engine operations into Zigbee2MQTT operations.

Keeping responsibilities narrow makes code easier to understand, test, and
extend.

---

## Backend Independence

The engine contains no knowledge of:

- MQTT
- Zigbee2MQTT
- Home Assistant
- Matter
- Z-Wave
- specific device manufacturers

Those responsibilities belong entirely to backend adapters.

The engine operates only on canonical domain objects.

---

## Canonical Properties

The engine operates on canonical property names.

Backend adapters translate native protocol names into the canonical
representation used internally.

Whenever practical, canonical names should follow Python's `snake_case`
convention.

---

## Deterministic

Comparison is a pure function.

Given identical inputs, identical outputs are always produced.

Comparison never performs I/O and never modifies a device.

---

## Declarative

Profiles describe **desired state**.

Snapshots describe **actual state**.

Metadata describes **device capabilities**.

The engine determines the changes required to transform the actual state into
the desired state.

---

## Plan Before Apply

Every modifying operation is a two-phase process.

1. Compute the required changes.
2. Display the execution plan.
3. Request confirmation (unless explicitly overridden).
4. Apply the changes.
5. Verify the result.

The engine never modifies a device without first determining exactly what will
change.

---

## One Source of Truth

Every piece of information has one authoritative source.

Examples:

- Application settings come from configuration.
- Device capabilities come from metadata.
- Desired settings come from profiles.
- Actual settings come from live devices.

Information should never be duplicated unnecessarily.

---

## Immutable Domain Objects

Domain objects are immutable.

Examples include:

- `DeviceSnapshot`
- `Configuration`
- `MqttConfiguration`
- `ConfigurationDiff`

Immutable objects simplify testing, comparison, reasoning, and concurrency.

---

## Separate Models

Different concepts deserve different models.

Application configuration is not a device profile.

A device profile is not metadata.

Metadata is not a live device.

Separating these concepts keeps responsibilities clear and prevents
architectural drift.

---

# Domain Model

```
Application
│
├── Configuration
│
├── Metadata Catalog
│      │
│      ├── Device Models
│      ├── Property Metadata
│      ├── Value Ranges
│      ├── Enumerations
│      └── Read-only Properties
│
├── Profiles
│      │
│      ├── Model Profiles
│      └── User Profiles
│
└── Devices
       │
       └── DeviceSnapshot
```

---

# Terminology

## Configuration

Settings required by the application itself.

Examples:

- MQTT host
- MQTT credentials
- paths
- logging
- timeouts

Configuration describes **how the application operates**.

---

## Metadata

Information describing a device model.

Examples:

- property descriptions
- valid ranges
- available choices
- writable/read-only status

Metadata describes **what a device is capable of**.

---

## Model Profile

A profile associated with a specific hardware model.

Normally represents factory defaults or recommended starting values.

May be provided by the project or contributed by the community.

---

## User Profile

A collection of desired settings created by the user.

Examples:

- Bedroom
- Nightlight
- Movie Mode
- Vacation

Profiles describe **how the user wants a device configured**.

---

## Device

A physical device installed in a home.

Examples:

- Kitchen Dimmer
- Office Switch
- Hallway Fan

---

## Snapshot

A snapshot is the current state reported by a live device.

Snapshots are read from the backend.

---

## Diff

A `ConfigurationDiff` represents the changes required to transform one state
into another.

---

# Storage Philosophy

Application configuration, metadata, and profiles are stored as files rather
than in a database.

Reasons include:

- human readability
- version control
- pull requests
- backups
- manual editing
- portability

Persistent storage should be accessed through simple `read()` and `write()`
operations.

Storage locations should be configurable.

---

# Future Directions

The following ideas are intentionally deferred until the core engine is
complete.

- Automatic metadata discovery from supported backends.
- Community-contributed model profiles.
- Device-to-device apply operations.
- Shared profiles inferred from multiple device instances.
- Profile analysis and recommendation tools.

These are enhancements, not architectural requirements.

---

# Design Philosophy

Configuration Engine is developed using a few guiding principles.

- Build one green step at a time.
- Prefer experiments over assumptions.
- Trust, but verify.
- Keep the public API simple.
- One source of truth.
- Separate responsibilities.
- Eat spaghetti. Don't write it.

---
Public API

Planned Commands:

configuration_engine

    snapshot

    compare

    apply

    verify

    capture

    analyze

    sync

Exceptions propagate upward.
Domain classes raise.
Infrastructure raises.
The CLI catches and reports.

