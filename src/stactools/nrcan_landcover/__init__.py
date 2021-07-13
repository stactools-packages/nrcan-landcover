import stactools.core

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.nrcan_landcover import commands
    registry.register_subcommand(commands.create_nrcanlandcover_command)


__version__ = '0.2.3'
"""Library version"""
