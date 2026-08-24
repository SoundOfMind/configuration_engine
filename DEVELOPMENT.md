# Development Guide

## Prerequisites

- Python 3.14+
- Git

## Clone the Repository

```powershell
git clone https://github.com/<your-account>/configuration_engine.git
cd configuration_engine
```

## Create a Virtual Environment - you should see (.venv) at the start of the powershell prompt

```powershell
python -m venv .venv
```

Activate it:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

## Install Dependencies

```powershell
python -m pip install -e ".[dev]"
```

## Verify the Environment

```powershell
python --version
python -m pip --version
```

## Run Quality Checks

```powershell
ruff check .
mypy src
pytest
```

## Git Workflow

Create a feature branch:

```powershell
git switch -c feature/<feature-name>
```

Commit small, focused changes.

Merge back to `main` only after all checks pass.

Development Workflow
1. Discover

Use small, disposable development code to answer a question.

Examples:

Can we connect to MQTT?
What does Zigbee2MQTT publish?
How are writes performed?
How does a refresh work?

No concern for production quality.

2. Understand

Discuss what we learned.

Separate observations from assumptions.

Yesterday's observation:

Zigbee2MQTT publishes what appears to be a complete device snapshot.

That changed the architecture.

3. Distill
Ask:
What single concept did we just discover?

Yesterday's answer wasn't "MQTT."

It was

DeviceSnapshot

4. Implement

Write the smallest production-quality class that captures that concept.

Every class should have one sentence that describes it.

For example:

DeviceSnapshot — "A backend-native snapshot of a device."
SnapshotParser — "Converts backend JSON into a DeviceSnapshot."
Zigbee2MqttBackend — "Translates Zigbee2MQTT concepts into engine concepts."

If I can't describe a class in one sentence, it's probably doing too much.

5.Test

Prefer real data whenever possible.

Yesterday's MQTT payload is worth far more than ten mocked payloads.

6. Commit

Every commit should represent a completed idea.

Not:

"Fixed stuff."

But:

"Add DeviceSnapshot."

or

"Parse Zigbee2MQTT snapshots."

---------------------------------------------
Sprint 2 Complete

✓ Production MQTT client
✓ Connection management
✓ Publish / Subscribe / Unsubscribe
✓ Message dispatch
✓ Request/response foundation
✓ Ruff clean
✓ Mypy clean
✓ Tests passing
