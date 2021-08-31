# flake8: noqa

from pyproj import CRS
from pystac import Link, Provider, ProviderRole

LANDCOVER_ID = "nrcan-landcover"
LANDCOVER_EPSG = 3978
LANDCOVER_CRS = CRS.from_epsg(LANDCOVER_EPSG)
LANDCOVER_TITLE = "Land Cover of Canada - Cartographic Product Collection"
LICENSE = "OGL-Canada-2.0"
LICENSE_LINK = Link(
    rel="license",
    target="https://open.canada.ca/en/open-government-licence-canada",
    title="Open Government Licence - Canada",
)

DESCRIPTION = """Collection of Land Cover products for Canada as produced by Natural Resources Canada using Landsat satellite imagery. This collection of cartographic products offers classified Land Cover of Canada at a 30 metre scale, updated on a 5 year basis."""

NRCAN_PROVIDER = Provider(
    name="Natural Resources Canada | Ressources naturelles Canada",
    roles=[
        ProviderRole.HOST,
        ProviderRole.LICENSOR,
        ProviderRole.PROCESSOR,
        ProviderRole.PRODUCER,
    ],
    url=
    "https://www.nrcan.gc.ca/maps-tools-publications/satellite-imagery-air-photos/application-development/land-cover/21755"
)

JSONLD_HREF = "https://open.canada.ca/data/en/dataset/4e615eae-b90c-420b-adee-2ca35896caf6.jsonld"

NRCAN_FTP = "http://ftp.maps.canada.ca/pub/nrcan_rncan/Land-cover_Couverture-du-sol/canada-landcover_canada-couverture-du-sol/CanadaLandcover2015.zip"

THUMBNAIL_HREF = "https://atlas.gc.ca/lcct/images/M.png"

KEYWORDS = [
    "Land Cover",
    "Remote Sensing",
    "Landsat",
    "Reflectance",
    "Mid-latitude",
    "Western Hemisphere",
    "Northern Hemisphere",
    "North America",
    "Canada",
    "Geographical maps",
]

COLOUR_MAP = {
    0: (0, 0, 0, 0),
    1: (0, 61, 0, 255),
    2: (147, 155, 112, 255),
    5: (20, 140, 61, 255),
    6: (91, 117, 43, 255),
    8: (178, 137, 51, 255),
    10: (224, 206, 137, 255),
    11: (155, 117, 137, 255),
    12: (186, 211, 84, 255),
    13: (63, 137, 114, 255),
    14: (107, 163, 137, 255),
    15: (229, 173, 102, 255),
    16: (168, 170, 173, 255),
    17: (219, 33, 38, 155),
    18: (76, 112, 163, 255),
    19: (255, 249, 255, 255)
}

CLASSIFICATION_VALUES = {
    1: "Temperate or sub-polar needleleaf forest",
    2: "Sub-polar taiga needleleaf forest",
    5: "Temperate or sub-polar broadleaf deciduous forest",
    6: "Mixed forest",
    8: "Temperate or sub-polar shrubland",
    10: "Temperate or sub-polar grassland",
    11: "Sub-polar or polar shrubland-lichen-moss",
    12: "Sub-polar or polar grassland-lichen-moss",
    13: "Sub-polar or polar barren-lichen-moss",
    14: "Wetland",
    15: "Cropland",
    16: "Barren lands",
    17: "Urban",
    18: "Water",
    19: "Snow and Ice",
}
