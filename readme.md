## Overview

`AMP`, the Augmentable Mibi Pipeline, is a GUI environment for dynamically processing multiplexed
image data via a configurable plugin-style architecture.  With no plugins active, AMP acts as a 
simple image viewer.  For now, AMP's standard plugins will be directclones of those in MAUI.

## Features

- Quick 'whole-cohort' tiff viewing from main viewer
- Loadable plugin interface for highly configurable data processing
- Single executable; no need to run in any sort environment (MATLAB, docker, conda, etc)

### Current plugins

- 🟡 MAUI style background removal

### Planned plugins

- ❌ MAUI style KNN-denoising
- ❌ MAUI style aggregate removal

## Getting Started

 - [Installation](./docs/installation.md)
 - [Main Viewer](./docs/main_viewer.md)
 - [Plugin Loading](./docs/plugin_loading.md)

## Support

## License