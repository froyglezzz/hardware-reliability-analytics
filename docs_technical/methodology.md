# Simulation Methodology

## 1. Material Characterization

### SAC305 Solder (Sn96.5Ag3Cu0.5)

Properties extracted from isothermal mechanical tests (−40°C to 150°C) per JEDEC JESD22-A104:

| Property | Value | Condition |
|---|---|---|
| Elastic Modulus | 51 GPa | 25°C |
| Shear Modulus | 18.7 GPa | 25°C |
| Poisson's Ratio | 0.36 | — |
| CTE | 21 ppm/°C | Bulk |
| Fatigue Ductility Coefficient εf' | 0.325 | Anand model fit |
| Fatigue Ductility Exponent c | −0.527 | Engelmaier (1983) |

Creep behavior modeled with the **Anand viscoplastic model** (9 constants), calibrated from
double-lap shear tests at strain rates of 0.001–1 s⁻¹ across −40°C to 150°C.

### Organic Substrate (BT Resin / ABF)

| Property | Value |
|---|---|
| CTE in-plane α₁ | 3.2 ppm/°C |
| CTE out-of-plane α₂ | 18 ppm/°C |
| Elastic Modulus | 22 GPa |
| Poisson's Ratio | 0.39 |

---

## 2. FEA Model Setup — Ansys Mechanical 2024 R1

### Geometry

Package geometry created in **SolidWorks 2024**, exported as Parasolid (`.x_t`), and
imported via Ansys SpaceClaim for defeaturing prior to meshing.

- Package: POWER10 MCM, 68.5 × 68.5 mm footprint
- Interconnect: C4 solder bumps, 150 µm diameter, 250 µm pitch, 100 µm nominal standoff height
- DNP (distance from neutral point): up to 15.2 mm at corner location

### Mesh

| Region | Element Type | Size |
|---|---|---|
| Global | SOLID186 (20-node hexahedral) | 200 µm |
| Solder bump body | SOLID186, biased | 30–60 µm |
| Solder/pad interface | SOLID186, refined | 20 µm |
| **Total** | | ~187,000 elements |

### Boundary Conditions

- **Thermal load:** IPC-9701A TC2 profile — ramp from −40°C to +125°C at 15°C/min,
  10-min dwell at each extreme
- **Symmetry:** Quarter-model symmetry along package diagonals
- **Mechanical:** Bottom PCB surface fixed in Z; symmetry planes constrained in-plane

### Solver

- Nonlinear static analysis, Newton-Raphson iteration
- Substep size: auto, convergence criterion 1×10⁻⁵
- 3 complete thermal cycles per simulation run

---

## 3. Fatigue Life Prediction

### Coffin-Manson Law

The plastic strain range Δεp is extracted at the **critical node** — the solder bump
with maximum accumulated plastic strain, located at DNP ≈ 15.2 mm (corner position).

$$N_f = \frac{1}{2} \left( \frac{\Delta\varepsilon_p}{\varepsilon_f'} \right)^{1/c}$$

| Parameter | Description | SAC305 Value |
|---|---|---|
| Nf | Cycles to failure | — |
| Δεp | Plastic strain range (FEA output) | 0.008–0.015 |
| εf' | Fatigue ductility coefficient | 0.325 |
| c | Fatigue ductility exponent | −0.527 |

### Engelmaier Temperature-Dependent Exponent

The fatigue ductility exponent `c` is temperature- and frequency-dependent per
Engelmaier (1983), "Fatigue Life of Leadless Chip Carrier Solder Joints":

$$c = -0.442 - 6\times10^{-4} T_m + 1.74\times10^{-2} \ln(1 + f)$$

where Tm = mean cyclic solder temperature (°C) and f = cycling frequency (cycles/day).

### Miner's Linear Damage Accumulation

For multi-condition test sequences with different thermal profiles:

$$D = \sum_i \frac{n_i}{N_{f,i}} \qquad \text{(failure predicted at } D = 1.0\text{)}$$

Conservative design target for IBM qualification: **D ≤ 0.8** before end of product lifetime.

---

## 4. Design of Experiments (DOE)

SolidWorks parametric models drive a DOE sweep to map sensitivity:

| Parameter | Low | Nominal | High |
|---|---|---|---|
| Standoff height | 80 µm | 100 µm | 120 µm |
| Bump diameter | 120 µm | 150 µm | 180 µm |
| Corner fillet radius | 0 µm | — | 20 µm |

Results are exported as JSON per the schema in `simulations/thermal_data/` and processed
automatically through the analysis pipeline.
