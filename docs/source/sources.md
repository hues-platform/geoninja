# Sources

GeoNinja relies on several external hydrogeological datasets. Before first use, these datasets must be acquired and processed through the automated data pipeline as described in {ref}`Installation<installation>`.

The pipeline downloads the source data, converts them into optimized formats, and stores the processed results in thebackend data directory. These processed datasets are then used for location-based parameter lookup and the computation of ATES-related indicators.

## GLHYMPS

GLHYMPS 2.0 (GLobal HYdrogeology MaPS) is a global hydrogeological dataset that provides spatial estimates of hydraulic properties for both consolidated and unconsolidated geological units.

In GeoNinja, GLHYMPS is used to obtain hydraulic conductivity estimates at a given geographic location. These values are derived from permeability estimates associated with hydrogeological units.

Original publication:

Huscroft, J., Gleeson, T., Hartmann, J., & Börker, J. (2018).\
*Compiling and mapping global permeability of the unconsolidated and
consolidated Earth: GLobal HYdrogeology MaPS 2.0 (GLHYMPS 2.0).*\
Geophysical Research Letters, 45.doi: 10.1002/2017GL075860

Source:\
https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP2/TTJNIU

(glim)=
## GLiM

The Global Lithological Map (GLiM) provides a global classification of lithological units based on surface geology.

In GeoNinja, GLiM is used to determine the lithological class at a given location. The lithology code returned by the map is then used to retrieve representative rock properties such as density or heat capacity.

Original publication:

Hartmann, J., & Moosdorf, N. (2012).\
*The new global lithological map database GLiM.*\
Global Biogeochemical Cycles, 26, GB2034.

Source:\
https://www.geo.uni-hamburg.de/en/geologie/forschung/aquatische-geochemie/glim.html

## Hydraulic gradient map

The hydraulic Gradient Map provides spatially resolved estimates of the regional hydraulic gradient. It is currently limited to Germany. The dataset was derived from an estimated map of absolute hydraulic head and processed to compute the spatial slope of the hydraulic head field.

In GeoNinja, the hydraulic gradient is used together with hydraulic conductivity values to estimate Darcy flow velocity.

Source:\
https://zenodo.org/records/18667244

## Rock properties

The rock properties dataset provides representative thermophysical properties associated with each lithology class in the GLiM dataset. It maps GLiM lithology keys to representative rock parameters used in GeoNinja calculations.

The dataset includes:
-   Density
-   Specific heat capacity
-   Thermal conductivity

In GeoNinja, this dataset is used to translate the lithology classification returned by {ref}`glim` into the physical parameters required for ATES performance estimation.

The dataset is stored as a CSV file and distributed together with the
GeoNinja source code.
