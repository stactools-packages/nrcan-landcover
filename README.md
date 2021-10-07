[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stactools-packages/nrcan-landcover/main?filepath=docs/installation_and_basic_usage.ipynb)

# stactools nrcan-landcover

- Name: nrcan-landcover
- Package: `stactools.nrcan-landcover`
- PyPI: https://pypi.org/project/stactools-nrcan-landcover/
- Owner: @sparkgeo
- Dataset homepage: [NRCAN](https://www.nrcan.gc.ca/maps-tools-publications/satellite-imagery-air-photos/application-development/land-cover/21755)
- STAC extensions used:
  - [file](https://github.com/stac-extensions/file/)
  - [proj](https://github.com/stac-extensions/projection/)
  - [raster](https://github.com/stac-extensions/raster/)

Collection of Land Cover products for Canada as produced by Natural Resources Canada using Landsat satellite imagery. This collection of cartographic products offers classified Land Cover of Canada at a 30 metre spatial resolution, updated on a 5 year basis.

This land cover dataset is the Canadian contribution to the 30 metre spatial resolution 2015 Land Cover Map of North America, which is produced by Mexican, American and Canadian government institutions under a collaboration called the North American Land Change Monitoring System (NALCMS).

## Usage

### Using the CLI

```bash
mkdir example_output
# Create a COG - creates /path/to/local_cog.tif
stac nrcanlandcover create-cog -d example_output -s tests/data-files/example2015.tif
# Create extent asset
stac nrcanlandcover create-extent-asset -d example_output -c example_output/example2015_cog.tif
# Create a STAC Item - creates /path/to/directory/local_cog.json
stac nrcanlandcover create-item -d example_output -c example_output/example2015_cog.tif -e example_output/example2015_cog_extent.geojson
# Create a STAC Collection
stac nrcanlandcover create-collection -d example_output
```
```bash
# Generate a full Collection with an Item and a COG Asset
stac nrcanlandcover build-full-collection -d "/path/to/directory"
# Generate a full Collection with tiled Items and many smaller COG Assets
stac nrcanlandcover build-full-collection -t -d "/path/to/directory"
```

### As a python module

```python
from stactools.nrcan_landcover.constants import JSONLD_HREF
from stactools.nrcan_landcover import utils, cog, stac

# Read metadata
metadata = utils.get_metadata(JSONLD_HREF)

# Create a STAC Collection
json_path = os.path.join(tmp_dir, "/path/to/nrcan-landcover.json")
stac.create_collection(metadata, json_path)

# Create a COG
cog.create_cog("/path/to/local.tif", "/path/to/cog.tif")

# Create a STAC Item
stac.create_item(metadata, "/path/to/item.json", "/path/to/cog.tif")
```
