import stactools.core
from stactools.nrcan_landcover.stac import create_collection, create_item
from stactools.nrcan_landcover.cog import create_cog

__all__ = [create_collection, create_item, create_cog]

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.nrcan_landcover import commands
    registry.register_subcommand(commands.create_nrcanlandcover_command)


__version__ = '0.2.4a1'
