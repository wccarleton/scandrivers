# Supported devices index

The published device documentation lives in the repository-level `devices/` pages. This folder retains manifests and detailed reference notes for maintainers.

## Current supported devices

- KT20 magnetic susceptibility scanner
  - Site page: [../../devices/kt20.qmd](../../devices/kt20.qmd)
  - Maintainer docs: [kt20/README.md](kt20/README.md)
  - Manifest: [kt20/manifest.yaml](kt20/manifest.yaml)
  - Demo data: [../../src/scandrivers/demo_data/kt20/kt20_0467](../../src/scandrivers/demo_data/kt20/kt20_0467)

- pXRF portable X-ray fluorescence
  - Site page: [../../devices/pxrf.qmd](../../devices/pxrf.qmd)
  - Demo data: [../../src/scandrivers/demo_data/pxrf/Final](../../src/scandrivers/demo_data/pxrf/Final)

## Contributing a new device

When a new driver is added, create a new subfolder here with:

1. a manifest file describing the device and its expected inputs
2. a reference page documenting the output schema and metadata
3. a small representative fixture under [../../src/scandrivers/demo_data](../../src/scandrivers/demo_data) when it is needed for demos or tests
