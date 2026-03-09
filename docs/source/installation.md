(installation)=
# Installation

GeoNinja can either be installed natively or in a Docker container. Both use cases require you to clone the [GitHub repository](https://github.com/hues-platform/geoninja) first.

```
cd YOUR_PARENT_DIR
git clone https://github.com/hues-platform/geoninja
```

For the rest of these instructions, the location of the cloned repo will be assumed to be located at ```REPO_ROOT = YOUR_PARENT_DIR/geoninja```.

## Native installation

For the native installation instructions, we assume that you are using [Anaconda](https://www.anaconda.com/download) for Python installation and dependency management. Alternative ways depending on your own local development setup viable as well if you adapt the steps accordingly.

### Install Python and set up environment

Take a look at ```backend/pyroject.toml``` about which Python versions are supported and prepare a GeoNinja Python environment:

```
conda create --name geoninja python=3.13
conda activate geoninja
```

Since the project is configured using [Poetry](https://python-poetry.org/),  make sure that you have it available:

```
conda install -c conda-forge poetry
```

Finally, you need to install both GeoNinja's data pipeline and backend projects:

```
cd REPO_ROOT/data_pipeline
poetry install
cd REPO_ROOT/backend
poetry install
```

### Run the data pipeline

Before GeoNinja can be used, the data pipeline needs to be run, downloading and preparing the geospatial maps which the app is based on.

```
cd REPO_ROOT/data_pipeline
python -m geoninja_dp.run
```

The pipeline places the prepared maps into the ```REPO_ROOT/backend/data/``` directory, alongside data manifest files which detail the steps taken during data processing.


### Run the backend

To run the backend, it needs to be invoced in a dedicated terminal where it will start listening for queries. The native code sequence for this is:

```
cd REPO_ROOT/backend
python -m uvicorn geoninja_backend.main:app --host 127.0.0.1 --port 8000
```

Alternatively, a launch configuration and dedicated task for this is included in the repository's .vscode folder.

### Run the frontend

To run the frontend, make sure to have [node.js](https://nodejs.org/en) installed and available on your system. The frontend needs to be run in its own dedicated terminal via

```
cd REPO_ROOT/frontend
npm install
npm run dev
```

After that, GeoNinja is available at http://localhost:5173.

## Docker installation

For the Docker installation, make sure to have a valid Docker installation on your system. For Windows users, we recommend [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### Set container configuration

We advise to reserve a reasonable amount of processing power for the container during the first installation of GeoNinja, around 16GB. If you are running Docker Desktop and have picked WSL2 during its installation, you would do this by editing (or creating) the file ```%userprofile%/.wslconfig``` and include the following settings:

```
[wsl2]
memory=14GB
swap=16GB
```

This can be reduced drastically after the data pipeline has concluded the first time that GeoNinja is launched.

### Building the containers

```
cd REPO_ROOT
docker compose build
```

This will create three containers: ```geoninja_back```, ```geoninja_front```, and ```geoninja_dp```, responsible for the backend, frontend, and the initial data pipeline.

### Running via contianer

```
cd REPO_ROOT
docker compose up
```

The first time this is run, the data pipeline will be run automatically, downloading the maps and processing them for geospatial lookup. Afterwards, GeoNinja will be available at ```http://localhost:8080```.
