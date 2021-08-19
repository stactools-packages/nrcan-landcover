import stactools.core
from stactools.cli import Registry

from stactools.nrcan_landcover.cog import create_cog
from stactools.nrcan_landcover.stac import create_collection, create_item

__all__ = [
    create_collection.__name__, create_item.__name__, create_cog.__name__
]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.nrcan_landcover import commands
    registry.register_subcommand(commands.create_nrcanlandcover_command)


__version__ = '0.2.5a1'
