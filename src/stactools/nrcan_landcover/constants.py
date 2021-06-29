# flake8: noqa

from pyproj import CRS
from pystac import Provider
from pystac import Link

LANDCOVER_ID = "nrcan-landcover"
LANDCOVER_EPSG = 3978
LANDCOVER_CRS = CRS.from_epsg(LANDCOVER_EPSG)
LANDCOVER_TITLE = "Land Cover of Canada - Cartographic Product Collection"
LICENSE = "proprietary"
LICENSE_LINK = Link(
    rel="license",
    target="https://open.canada.ca/en/open-government-licence-canada",
    title="Open Government Licence - Canada",
)

DESCRIPTION = """Collection of Land Cover products for Canada as produced by Natural Resources Canada using Landsat satellite imagery. This collection of cartographic products offers classified Land Cover of Canada at a 30 metre scale, updated on a 5 year basis."""

NRCAN_PROVIDER = Provider(
    name="Natural Resources Canada | Ressources naturelles Canada",
    roles=["producer", "processor", "host"],
    url=
    "https://www.nrcan.gc.ca/maps-tools-publications/satellite-imagery-air-photos/application-development/land-cover/21755"
)

NRCAN_FTP = "http://ftp.maps.canada.ca/pub/nrcan_rncan/Land-cover_Couverture-du-sol/canada-landcover_canada-couverture-du-sol/CanadaLandcover2015.zip"
