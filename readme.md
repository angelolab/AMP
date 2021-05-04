## Overview

`AMP`, the Augmentable Mibi Pipeline, is a GUI environment for dynamically processing multiplexed
image data via a configurable plugin-style architecture.  With no plugins active, AMP acts as a 
simple image viewer.  For now, AMP's standard plugins will be direct clones of those in MAUI.

This project is under active development, so exact details of functionality are subject to change.

## Features

- Easily view distinct channels of multiplexed image data
- Loadable plugin interface for highly configurable data processing
- Direct installation; doesn't require MATLAB, python, docker, etc.

### Current plugins

- ✔️ MAUI style background removal

### Planned plugins

- ❌ MAUI style KNN-denoising
- ❌ MAUI style aggregate removal

## Getting Started

 - [Installation](./docs/installation.md)
 - [Main Viewer](./docs/main_viewer.md)
 - [Plugin Loading](./docs/plugin_loading.md)

## Support

## License