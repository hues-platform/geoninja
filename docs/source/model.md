# Model

(static-input-parameters)=
## Static input parameters

| Symbol | Description | Display Unit | Min | Max | Default |
|------------|------------|------------|------------|------------|------------|
| $y$  | Analyis year | - | 1990 | 2023  | 2020 |
| $h_{aq}$  | Thickness | m | 10 | 200  | 30 |
| $r_{well}$  | Well radius | m | 0.05 | 2.0 | 0.2 |
| $d$  | Well distance | m | 10 | 1000  | 100 |
| $s_{max}$  | Max drawdown | m | 1.0 | 20.0  | 1.5 |
| $\rho_f$  | Fluid density | kg/m^3 | 100 | 2000  | 1000 |
| $c_f$  | Fluid specific heat capacity | J/(kg*K) | 100 | 10000  | 4180 |
| $\phi$  | Porosity | - | 0.01 | 0.5  | 0.2 |
| $\Delta T$  | Temperature difference | K | 1 | 20  | 5 |

### Analysis year

The analysis year $y$ defines the temporal reference for the analysis.
It is primarily used to determine the {ref}`heating/cooling durations <heating-cooling-duration>` based on historical temperature data for the selected year.

### Thickness

The parameter $h\_{aq}$ denotes the effective thickness of the aquifer
layer that participates in groundwater flow and heat transport.

It represents the vertical extent of the permeable geological layer that
can store and transmit fluid. A larger aquifer thickness generally
allows higher groundwater flow rates and larger effective storage
volumes.

### Well radius

The well radius $r\_{well}$ represents the radius of the extraction and injection wells used by the ATES system. It is measured from the center of the well to the inner boundary of the well casing. The well radius affects the {ref}`maximal volumetric flow rates <maximal-volumetric-flow-rates>`.

### Well distance

The parameter $d$ describes the horizontal distance between the warm and cold wells of an ATES doublet. Well distances affects the {ref}`maximal volumetric flow rates <maximal-volumetric-flow-rates>`.

### Max drawdown

The maximal drawdown $s\_{max}$ defines the maximum permitted lowering
of the hydraulic head at the boundary of an extraction well. Drawdown occurs when groundwater is pumped from the aquifer, causing a local reduction of hydraulic pressure around the well. The maximal drawdown affects the {ref}`maximal volumetric flow rates <maximal-volumetric-flow-rates>`.

### Fluid density

The parameter $\rho\f$ represents the density of the
fluid stored in the aquifer.

### Fluid specific heat capacity

The parameter $c\f$ represents the density of the
fluid stored in the aquifer.

### Porosity

The porosity $\phi_{aq}$ represents the fraction of the
aquifer volume that is occupied by fluid-filled pore space. A value of $\phi_{aq} = 0$ corresponds to a completely solid material with no pore space while a value of $\phi_{aq} = 1$ represents to a hypothetical medium consisting entirely of fluid.

### Temperature difference

The parameter $\Delta T$ represents the temperature difference between the warm and cold wells of the ATES system. This temperature difference determines the thermal energy which is produced by the aquifer relative to the mass flow rates.

(local-input-parameters)=
## Local input parameters

| Symbol | Description | Display Unit | Min | Max |
|------------|------------|------------|------------|------------|
| $\rho_s$ | Rock density | kg/m^3 | 1000 | 4000 |
| $c_s$ | Rock specific heat capacity | J/(kg*K) | 500 | 2000 |
| $k_s$ | Rock thermal conductivity | W/(m*K) | 0.1| 10.0 |
| $K_{aq}$ | Hydraulic conductivity | m/d | 8.64e-8 | 864 |
| $i_{aq}$ | Hydraulic gradient | - | 0 | 1 |
| $t_{ht,0}$ | Heating period start | - | 01.01. | 31.12. |
| $t_{ht,e}$ | Heating period end | - | 01.01. | 31.12. |
| $t_{co,0}$ | Cooling period start | - | 01.01. | 31.12. |
| $t_{co,e}$ | Cooling period end | - | 01.01. | 31.12. |

### Rock density

The parameter $\rho_s$ denotes the density of the solid
rock matrix forming the aquifer.

### Rock specific heat capacity

The parameter $c_s$ denotes the specific heat capacity of the solid
rock matrix forming the aquifer.

### Rock thermal conductivity

The parameter $k_s$ represents the thermal conductivity of the rock
matrix.

### Hydraulic conductivity

Hydraulic conductivity $K\_{aq}$ describes the ability of the aquifer to transmit groundwater.

### Hydraulic gradient

The hydraulic gradient $i\_{aq}$ represents the absolute value of the gradient of
hydraulic head driving groundwater flow. It is used to calculate the {ref}`Darcy velocity<darcy-velocity>`.

(heating-cooling-periods)=
### Heating/Cooling periods

Leave blank for now

(derived-parameters)=
## Derived parameters

| Symbol | Description | Display Unit |
|------------|------------|------------|
| $(\rho c)_f$ | Fluid volumetric heat capacity | J/(K*m^3) |
| $(\rho c)_s$ | Rock volumetric heat capacity | J/(K*m^3) |
| $(\rho c)_{aq}$ | Aquifer volumetric heat capacity | J/(K*m^3) |
| $T_{aq}$ | Hydraulic transmissivity | m^2/d |
| $v_{aq}$ | Darcy velocity | m/d |
| $v_{pore}$ | Pore velocity | m/d |
| $v_{th}$ | Thermal front velocity | m/d |
| $R_{th}$ | Thermal retardation factor | - |
| $S_{aq}$ | Storativity | - |
| $\Delta t_{ht}$ | Heating duration | d |
| $\Delta t_{co}$ | Cooling duration | d |

Derived parameters are quantities that are computed from the {ref}`static input parameters<static-input-parameters>` and {ref}`local input parameters<local-input-parameters>`. They describe hydraulic and thermal properties of the aquifer that are required for the calculation of ATES performance indicators.

### Fluid volumetric heat capacity

The fluid volumetric heat capacity $(\rho c)_f$ describes the amount of thermal energy that can be stored in a unit volume of groundwater per unit temperature change. It combines the fluid density $\rho_f$ and the specific heat capacity $c_f$ of the groundwater. This quantity is used to determine the thermal energy transported by the flowing groundwater.

$$
    \begin{align*}
        (\rho c)_f = \rho_f \cdot c_f
    \end{align*}
$$

### Rock volumetric heat capacity

The rock volumetric heat capacity $(\rho c)_s$ describes the thermal energy that can be stored in a unit volume of the solid aquifer matrix. It is calculated from the rock density $\rho_s$ and the specific heat capacity $c_s$. This parameter represents the thermal storage capacity of the solid material surrounding the pore space.

$$
    \begin{align*}
        (\rho c)_s = \rho_s \cdot c_s
    \end{align*}
$$

### Aquifer volumetric heat capacity

The effective volumetric heat capacity $(\rho c)_{aq}$ describes the combined thermal storage capacity of the aquifer system, taking into account both the fluid contained in the pore space and the surrounding rock matrix. The parameter depends on the porosity $\phi_{aq}$ and represents a weighted average of the fluid and rock volumetric heat capacities.

$$
    \begin{align*}
        (\rho c)_{aq} = \phi_{aq} \cdot (\rho c)_f + (1-\phi_{aq}) (\rho c)_s
    \end{align*}
$$

### Hydraulic transmissivity

The hydraulic transmissivity $T_{aq}$ describes the ability of the entire aquifer layer to transmit groundwater. It is defined as the product of the hydraulic conductivity $K_{aq}$ and the aquifer thickness $h_{aq}$. Higher transmissivity values indicate that groundwater can flow more easily through the aquifer layer.

$$
    \begin{align*}
        T_{aq} = K_{aq} \cdot h_{aq}
    \end{align*}
$$

(darcy-velocity)=
### Darcy velocity

The Darcy velocity $v_{aq}$ represents the volumetric groundwater flux through the aquifer. It is calculated from the hydraulic conductivity $K_{aq}$ and the hydraulic gradient $i_{aq}$. The Darcy velocity describes the apparent groundwater velocity averaged over the entire cross-section of the porous medium.

$$
    \begin{align*}
        v_{aq} = K_{aq} \cdot i_{aq}
    \end{align*}
$$

### Pore velocity

The pore velocity $v_{pore}$ represents the actual groundwater velocity inside the pore space. Since groundwater only flows through the void space of the aquifer, the pore velocity is obtained by dividing the Darcy velocity by the porosity $\phi_{aq}$. The pore velocity is therefore typically larger than the Darcy velocity.

$$
    \begin{align*}
        v_{pore} = \phi_{aq}^{-1} \cdot v_{aq}
    \end{align*}
$$

(thermal-front-velocity)=
### Thermal-front velocity

The thermal-front velocity $v_{th}$ describes the propagation speed of a temperature front through the aquifer. Because part of the transported thermal energy is stored in the solid matrix, the thermal front moves slower than the groundwater itself. The thermal-front velocity is obtained by multiplying the pore velocity by the {ref}`thermal retardation factor<thermal-retardation-factor>`.

$$
    \begin{align*}
        v_{th} = R_{th} \cdot v_{pore}
    \end{align*}
$$

(thermal-retardation-factor)=
### Thermal retardation factor

The thermal retardation factor $R_{th}$ describes the reduction of thermal transport velocity due to heat storage in the solid matrix of the aquifer. When groundwater transports heat through the aquifer, part of the thermal energy is temporarily stored in the surrounding rock material. This interaction slows the propagation of the thermal front relative to the groundwater flow.

$$
    \begin{align*}
        R_{th} = \frac{\phi_{aq} \cdot (\rho c)_f}{(\rho c)_{aq}}
    \end{align*}
$$

### Storativity

The storativity $S_{aq}$ represents the capacity of the aquifer to release or store water when the hydraulic head changes. In the simplified model used here, storativity is approximated as a fraction of the aquifer porosity. This parameter is relevant for describing hydraulic responses of the aquifer during pumping.

$$
    \begin{align*}
        S_{aq} = 0.1 \cdot \phi_{aq}
    \end{align*}
$$

(heating-cooling-duration)=
### Heating/Cooling duration

The parameters $\Delta t_{ht}$ and $\Delta t_{co}$ represent the length of durations during which the system operates in heating mode and cooling mode, respectively. These values are determined from the start dates $t_{ht,0}$, $t_{co,0}$ and end dates $t_{ht,e}$, $t_{co,e}$ of the {ref}`heating and cooling periods<heating-cooling-periods>`. They define the annual durations of thermal extraction and injection phases within the annual operating cycle.


## ATES KPIs

The original purpose of GeoNinja is the calculation of location-specific Key Performance Indicators (KPIs) of Aquifer Thermal Energy Storage (ATES). The interpretation and calculation method for each parameter will be explained further below in this section. For more details, please refer to:

```
Integration of Aquifer Thermal Energy Storage (ATES) to linear energy system models.
D. Beermann, S.N.. Sørensen, M. Tønder, C. Doughty, P. Blum, K. Menberg, M. Wetter, M. Sulzer & R. Mutschler.
Submitted to Applied Energy, 2026
```

ATES technologies store thermal energy in an aquifer layer, accessed through wells which are designated as warm or cold wells. Fluid extracted from warm wells is used for heating purposes and cold well fluid serves cooling purposes. While different strategies exist of how the wells interact with other, this KPI calculation assumes the most basic case in which they are organized in well pairs consisting of a warm and cold well. Consequently, the KPIs below relate either to a single well or a pair of wells. No statement is made about the number of installed wells or the spatial arrangement of the configuration.

Additionally, most ATES installations also contain a number of water-source heat pumps which can be used to increase heating efficiency or cooling efficiency. The ATES KPIs calculated by GeoNinja are to be understood without these heat pumps and only quantify the thermal potential based on temperature difference in the wells.


| Symbol | Description | Display Unit |
|------------|------------|------------|
| $\dot{V}^{max}_{ht}$ | Maximal volumetric flow rate (heating) | m^3/h |
| $\dot{V}^{max}_{co}$ | Maximal volumetric flow rate (cooling) | m^3/h |
| $\dot{m}^{max}_{ht}$ | Maximal mass flow rate (heating) | kg/h |
| $\dot{m}^{max}_{co}$ | Maximal mass flow rate (cooling) | kg/h |
| $P^{max}_{ht}$ | Maximal heat flow rate | kW |
| $P^{max}_{co}$ | Maximal heat flow rate | kW |
| $r_{vol,ww}$ | Volumetric-equivalent thermal radius for warm wells | m |
| $r_{vol,cw}$ | Volumetric-equivalent thermal radius for cold wells | m |
| $r_{adv,ww}$ | Advective thermal radius for warm wells | m |
| $r_{adv,cw}$ | Advective thermal radius for cold wells | m |
| $r_{ww}$ | Thermal radius for warm wells | m |
| $r_{cw}$ | Thermal radius for cold wells | m |
| $A_{th,pair}$ | Thermal area of a well pair | m^2 |
| $\overline{P}_{ht}$ | Maximal heating density | W/m^2 |
| $\overline{P}_{co}$ | Maximal cooling density | W/m^2 |

(maximal-volumetric-flow-rates)=
### Maximal volumetric flow rates

In normal operation of a dual-well paired system, fluid is extracted from the aquifer through one of the wells at a given volumetric flow rate $\dot{V}$. This fluid then passes through heat exchangers and, after the thermal exchange, is injected back into the aquifer at the other while with the same flow rate. This constant pumping procedure leads to a drawdown of the hydraulic head near the extraction well, and a corresponding lift at the injection well. The most important criterion limiting the flow rate is that the drawdown should not exceed the maximal permissible drawdown $s^{max}$, measured at the well boundary. We therefore characterize the maximal volumetric flow rate $\dot{V}^{max}$ as that flow rate which results in a drawdown of exactly that edge case. To model this effect, we first consider a singe well and a constant volumetric flow rate of $\dot{V}$ (positive values indicate extraction, negative values indicate injection), operating over a time period $\Delta t$. The resulting shift in hydraulic head is denoted as $\hat{s}$ (positive values indicate a drawdown, negative values indicate a lift). Theis's equation tells us that this shift can be calculated as:

$$
    \hat{s} = \frac{\dot{V} \cdot W \left( \frac{x^2 \, S_{aq}}{4 \, \Delta t \, T_{aq}} \right)}{4 \, \pi \, T_{aq}}
$$

where $x>0$ is the radial distance from the extraction/injection center. The function

$$
    W: \mathbb{R}_0^+ \to \mathbb{R}, \qquad W(u) = \int_u^\infty \frac{e^{-\tau}}{\tau} d\tau = -\mathrm{Ei}(-u)
$$

is called the well function and strongly relates to the exponential integral function $\mathrm{Ei}$ which can be evaluated using the ```scipy``` package in Python. The drawdown at the well boundary of the extraction well can be calculated as a superposition of the extraction and injection effects from both wells. If we denote $\hat{s}_+ > 0$ as the drawdown caused by the extraction well and $\hat{s}_- < 0$ as the lift from the injection well, both evaluated at the well boundary of the extraction well, we have

\begin{align*}
    \hat{s}_+ &= \frac{\dot{V} \, W \left( \frac{r_{well}^2 \, S_{aq}}{4 \, \Delta t \, T_{aq}} \right)}{4 \, \pi \, T_{aq}} \\
    \hat{s}_- &= \frac{-\dot{V} \, W \left( \frac{(d - r_{well})^2 \, S_{aq}}{4 \, \Delta t \, T_{aq}} \right)}{4 \, \pi \, T_{aq}}
\end{align*}

The effective drawdown after superposition is given by

$$
    s = \hat{s}_+ + \hat{s}_- = \frac{ \dot{V} }{ 4 \, \pi \, T_{aq} } \left(  W\left( \frac{r_{well}^2 \, S_{aq}}{4 \, \Delta t \, T_{aq} } \right) - W\left( \frac{(d-r_{well})^2 \, S_{aq}}{4 \, \Delta t \, T_{aq} } \right) \right)
$$

This allows to identify the maximal volumetric flow rate $\dot{V}^{max}$ using the condition $s = s^{max}$ as:

$$
    \dot{V}^{max} = \frac{ 4 \, \pi \, T_{aq} \, s^{max} }{ W\left( \frac{r_{well}^2 \, S_{aq}}{4 \, \Delta t \, T_{aq} } \right) - W\left( \frac{(d-r_{well})^2 \, S_{aq}}{4 \, \Delta t \, T_{aq} } \right) }
$$

The above derivation was intentionally done agnostic to heating or cooling scenario but can be readily applied to calculate the final KPIs:

\begin{align*}
    \dot{V}^{max}_{ht} &= \frac{ 4 \, \pi \, T_{aq} \, s^{max} }{ W\left( \frac{r_{well}^2 \, S_{aq}}{4 \, \Delta t_{ht} \, T_{aq} } \right) - W\left( \frac{(d-r_{well})^2 \, S_{aq}}{4 \, \Delta t_{ht} \, T_{aq} } \right) } \\
    \dot{V}^{max}_{co} &= \frac{ 4 \, \pi \, T_{aq} \, s^{max} }{ W\left( \frac{r_{well}^2 \, S_{aq}}{4 \, \Delta t_{co} \, T_{aq} } \right) - W\left( \frac{(d-r_{well})^2 \, S_{aq}}{4 \, \Delta t_{co} \, T_{aq} } \right) }
\end{align*}

Note the underlying assumption that well radii are identical for each well, and the fact that the maximal extraction rates between warm and cold wells are caused by differences between heating and cooling durations alone.

### Maximal mass flow rates

From the maximal volumetric flow rates, it is straightforward to calculate the maximal mass flow rates:

\begin{align*}
    \dot{m}_{ht}^{max} &= \rho_f \,\dot{V}_{ht}^{max} \\
    \dot{m}_{co}^{max} &= \rho_f \,\dot{V}_{co}^{max}
\end{align*}

(maximal-thermal-flow-rates)=
### Maximal thermal flow rates

The maximal thermal flow rates parametrize the peak thermal power which can be extracted from a pair of wells operating at maximal volumetric flow rate. They can be calculated straightforwardly as

\begin{align*}
    P^{max}_{ht} &= c_f \, \dot{m}^{max}_{ht} \, \Delta T \\
    P^{max}_{co} &= c_f \, \dot{m}^{max}_{co} \, \Delta T
\end{align*}

(volumetric-equivalent-thermal-radii)=
### Volumetric-equivalent thermal radii

A central question that needs to be considered when designing an ATES system is the underground area which is thermally affected by the installed wells. GeoNinja considers two different aspects to determine a conservative guess about this area. The first of which is the *volumetric equivalent thermal radius* which was first introduced in

```
A dimensionless parameter approach to the thermal behavior of an aquifer thermal energy storage system
C. Doughty, G. Hellström, C.F. Tsang & J. Claesson
Water Resources Research, 1082.
```

Herein, the authors consider an injection well and a fictious cylindrical volume $V_{th}$ which contains the same thermal energy as the amount of totally injected fluid $V_{in}$ during the injection cycle. This cylinder is supposed to have the same height as the aquifer thickness $h_{aq}$, and its radius $r_{vol}$ is called the *volumetric-equivalent thermal radius*. It can be calculated by the classifying condition of equivalent thermal energy as:

$$
    r_{vol} = \sqrt{\frac{V_{th}}{\pi h_{aq}}} = \sqrt{\frac{\rho_f \, c_f \, V_{in}}{\rho_{aq} \, c_{aq} \, \pi \, h_{aq}}}
$$

In general, $V_{in}$ will depend on the operation of the ATES. However, we can make a conservative estimate by acknowledging that the maximal injected volume will be reached when the system operates at peak volumetric flow rate for the entire injection duration. From this we conclude that

\begin{align*}
    r_{vol,ww} &= \sqrt{\frac{\rho_f \, c_f \, \dot{m}^{max}_{co} \, \Delta t_{co}}{\rho_{aq} \, c_{aq} \, \pi \, h_{aq}}} \\
    r_{vol,cw} &= \sqrt{\frac{\rho_f \, c_f \, \dot{m}^{max}_{ht} \, \Delta t_{ht}}{\rho_{aq} \, c_{aq} \, \pi \, h_{aq}}}
\end{align*}

Conser here that the warm well (index *ww*) is the injection well duration cooling operation while the cold well (index *cw*) is the injection well duration heating operation.

(advective-thermal-radii)=
### Advective thermal radii

The second factor to be considered in how an injection well thermally influences its surroundings is to take into account the underground flow velocity. The injected volume will be distored and displaced by this process during the entire duration of the injection cycle. Since the thermal propagation speed is characterized by the {ref}`thermal front velocity<thermal-front-velocity>` $v_{th}$, it is straightforward to calculate the spatial thermal influence by a linear motion equation:

\begin{align*}
    r_{adv,ww} &= v_{th} \, \Delta t_{co} \\
    r_{adv,cw} &= v_{th} \, \Delta t_{ht}
\end{align*}

We call these lengths the *advective thermal radii*. Take note again that the warm well (index *ww*) is the injection well duration cooling operation while the cold well (index *cw*) is the injection well duration heating operation.

(thermal-radii)=
### Thermal radii

Both the {ref}`volumetric-equivalent thermal radii <volumetric-equivalent-thermal-radii>` and the {ref}`advective thermal radii <advective-thermal-radii>` contribute to a thermal influence area around an injection well. In practice, this means that the thermal front is transported and distorted and its surface projection no longer resembles a circle in the mathematical sense. However, the goal of GeoNinja is to use a simple set of parameters (scalar, readily available) and make a conservative estimate about the subsurface dimensions. For this reason, we assume that the two effects are maximally cumulative and the farthest point of thermal influence is located at a combined distance of both radii from the center. This leads to the definition of the *thermal radii*:

\begin{align*}
    r_{ww} &= r_{vol,ww} + r_{adv,ww} \\
    r_{cw} &= r_{vol,cw} + r_{adv,cw}
\end{align*}

(thermal-well-pair-area)=
### Thermal well pair area

Since we have modeled the thermally influenced area around each well in a pair of wells, we can make a simple estimate about the space requirements of the well pair as a whole. Our approach here is to determine the smallest rectangle which contains both circles around the wells with the given {ref}`thermal radii<thermal-radii>`. The area of this rectangle can be calculated as

$$
    A_{th,pair} = (d + r_{ww} + r_{cw}) \cdot \max(r_{ww}, r_{cw})
$$

### Maximal thermal densities

From the {ref}`maximal thermal flow rates<maximal-thermal-flow-rates>` and the {ref}`thermal well pair area<thermal-well-pair-area>`, it is straightforward to calculated the *maximal thermal densities* of a well pair:

$$
    \overline{P}_{ht} &= \frac{P^{max}_{ht}}{A_{th,pair}} \\
    \overline{P}_{co} &= \frac{P^{max}_{co}}{A_{th,pair}}
$$
