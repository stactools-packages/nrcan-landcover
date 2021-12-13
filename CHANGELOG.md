# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project attempts to match the major and minor versions of [stactools](https://github.com/stac-utils/stactools) and increments the patch number as needed.

## [Unreleased]

### Added

- `build-full-collection` will generate COGs, STAC Items, and a STAC Collection.
- Tiling support for the `create-cog` command.
- Label and Projection extensions on Asset, Collection, and Summary
- Keywords on the Collection.
- Thumbnail asset on Collection and Item.
- Metadata Asset on STAC Collection.

### Deprecated

- Nothing.

### Removed

- Nothing.

### Fixed

- Colormap must be applied before `gdal_translate` is called. This ensures that the correct settings are used e.g. NEAREST vs CUBIC for generating overviews.[#22](https://github.com/stactools-packages/nrcan-landcover/pull/22)
- create-item and create-collection shouldn't call save on the STAC object.
- Metadata URL on STAC Item.

## [0.2.4]

### Added

- STAC raster extension to STAC Items
- STAC file extension to STAC Items
- Colour map on COG
- Ensure that the no_data value is set properly
- STAC proj extension fields to STAC Items
- Updated with contents of the template repo (a231a37275b0590e759d7114c4d6c7f685453c22)

### Deprecated

- Nothing.

### Removed

- Nothing.

### Fixed

- Collection file name is now `collection.json` [#15](https://github.com/stactools-packages/nrcan-landcover/pull/15)
