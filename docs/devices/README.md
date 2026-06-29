# Supported devices index

This folder contains the documentation catalog for supported instrument drivers.
Each device has its own subfolder with a manifest and a reference page describing the expected file structure, metadata, and variable names.

## Current supported devices

- KT20 magnetic susceptibility scanner
  - Docs: [kt20/README.md](kt20/README.md)
  - Manifest: [kt20/manifest.yaml](kt20/manifest.yaml)
  - Sample data: [../../data/kt20/kt20_0467](../../data/kt20/kt20_0467)

## Contributing a new device

When a new driver is added, create a new subfolder here with:

1. a manifest file describing the device and its expected inputs
2. a reference page documenting the output schema and metadata
3. example data under [../../data](../../data) using the same device subfolder naming convention
