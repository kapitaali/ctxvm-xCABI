# Project spec — `projects/` registry

This directory holds **standalone project specs**: end-to-end products that would be
*implemented with* the ctxvm/xCABI stack (spec, engine, validator, measurement packaging),
but are **not features of the framework** and add nothing to its code or normative files.
One file per project, candidacy status stated in each header. Go/no-go sits with the
orchestrator.

Current candidates:

| File | Working name | One-line pitch | Status |
|---|---|---|---|
| [`01-open-decision-primitive.md`](01-open-decision-primitive.md) | `umpire` | Open-source, JEV-style typed decision primitive — deterministic by construction, governed by xCABI replay + ODPS corpus packaging | proposed |
