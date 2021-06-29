ARG STACTOOLS_VERSION=latest
FROM stacutils/stactools:$STACTOOLS_VERSION

WORKDIR /opt/stactools-nrcan-landcover

# For caching purposes, install dependencies but remove the actual package
COPY pyproject.toml setup.cfg ./
COPY src/stactools/nrcan_landcover/__init__.py src/stactools/nrcan_landcover/
RUN pip install . \
    && rm -r /opt/conda/lib/python3.8/site-packages/stactools/nrcan_landcover

COPY src ./src
RUN pip install .
