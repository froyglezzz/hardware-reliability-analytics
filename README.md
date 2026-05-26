# Hardware Reliability & Thermal Analytics Tool
### HPC Packaging — Solder Joint Fatigue Analysis & Real-Time Thermal Monitoring

[![Python Tests](https://github.com/froyglezzz/hardware-reliability-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/froyglezzz/hardware-reliability-analytics/actions)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](hardware_monitor/CMakeLists.txt)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Problem Statement: Warpage and Thermal Stress in Multi-Chip Modules

IBM POWER10 and z16 multi-chip modules (MCMs) integrate multiple processor dies on organic
substrates up to 68.5 × 68.5 mm. The coefficient of thermal expansion (CTE) mismatch between
silicon dies (~2.6 ppm/°C), organic substrates (~3.2–18 ppm/°C), and PCBs (~16 ppm/°C)
subjects C4 solder interconnects to cyclic shear strain during qualification thermal cycling
per **IPC-9701A TC2** (−40°C to +125°C, 1500+ cycles).

Corner bumps at maximum distance-from-neutral-point (**DNP > 15 mm**) accumulate plastic
strain that leads to intergranular cracking and electrical open failures — the leading
wear-out mechanism in high-density MCM packaging.

**This tool provides three integrated capabilities:**

1. **Automated solder joint lifetime prediction** using the Coffin-Manson / Engelmaier model
   on FEA-exported simulation data
2. **Publication-quality visualizations** — S-N (Wöhler) diagram, cumulative Miner's damage
   curve, per-cycle damage bar chart
3. **Real-time C++17 hardware monitor** simulating thermal throttling on IBM HPC nodes,
   implementing the same decision logic as a BMC firmware thermal subsystem

---

## Repository Structure

```
hardware-reliability-analytics/
├── simulations/
│   ├── thermal_data/                   # FEA-exported thermal cycle reports
│   │   ├── sample_thermal_cycles.json  # Full report with material properties
│   │   └── sample_thermal_cycles.csv   # Tabular format for quick import
│   └── results/                        # Generated plots (gitignored)
│
├── scripts_analysis/                   # Python analytics pipeline
│   ├── data_loader.py                  # Parses JSON/CSV simulation reports
│   ├── coffin_manson.py                # Coffin-Manson, Engelmaier, Miner's rule
│   ├── visualization.py                # Degradation curve, Wöhler S-N, damage bar
│   ├── analyzer.py                     # Orchestrator + CLI entry point
│   └── tests/                          # pytest suite (33 tests)
│       ├── test_data_loader.py
│       ├── test_coffin_manson.py
│       ├── test_visualization.py
│       └── test_analyzer.py
│
├── hardware_monitor/                   # C++17 thermal monitor daemon
│   ├── include/
│   │   └── thermal_monitor.h           # ThermalMonitor class declaration
│   ├── src/
│   │   ├── thermal_monitor.cpp         # Sensor simulation, throttling logic
│   │   └── main.cpp                    # CLI entry point
│   └── CMakeLists.txt
│
├── docs_technical/
│   ├── methodology.md                  # FEA setup, Anand model, DOE, solver config
│   └── root_cause_analysis.md         # Failure modes: IBM POWER10 & z16
│
├── cad_models/                         # SolidWorks / STEP geometry (Parasolid exports)
├── requirements.txt
└── README.md
```

---

## Quick Start

### Python Analysis Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run full analysis on sample data
python -m scripts_analysis.analyzer \
    simulations/thermal_data/sample_thermal_cycles.json \
    --output-dir simulations/results/
```

**Output:**
```
=== Analysis Complete ===
Simulation ID    : IBM_POWER10_PKG_001
Estimated life   : 311 cycles
Cumulative damage: 0.032185
Risk level       : LOW

Plots saved to   : simulations/results
  -> simulations/results/IBM_POWER10_PKG_001_degradation.png
  -> simulations/results/IBM_POWER10_PKG_001_woehler.png
  -> simulations/results/IBM_POWER10_PKG_001_damage.png
```

Exits with code `0` (LOW/MODERATE risk) or `1` (HIGH/CRITICAL risk) for CI integration.

### C++ Hardware Monitor

```bash
# Build (requires CMake 3.20+ and C++17 compiler)
cd hardware_monitor
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# Run monitor for 10 seconds
./build/Release/thermal_monitor 10
```

**Sample output:**
```
=== IBM HPC Thermal Monitor Daemon ===
Component : POWER10 Multi-Chip Module
Thresholds: WARNING=75C  THROTTLE=90C  CRITICAL=105C

Monitoring for 10 seconds...

[WARNING ] [ms]  PROC0_DIE_TEMP        78.3 C  -> WARNING
[THROTTLE] [ms]  DIMM_B0_TEMP          91.2 C  -> THROTTLE
           -> Reducing P-state on DIMM_B0_TEMP
```

### Run Test Suite

```bash
pytest scripts_analysis/tests/ -v --cov=scripts_analysis --cov-report=term-missing
```

---

## Simulation Methodology

**FEA Tool:** Ansys Mechanical 2024 R1 | **CAD:** SolidWorks 2024

| Setup Parameter | Value |
|---|---|
| Element type | SOLID186 (20-node hexahedral) |
| Total elements | ~187,000 |
| Solder constitutive model | Anand viscoplastic (9 constants) |
| Thermal profile | IPC-9701A TC2: −40/+125°C, 15-min ramps, 10-min dwell |
| Symmetry | Quarter-model |
| Convergence criterion | 1×10⁻⁵ |

### Fatigue Life Equations

**Coffin-Manson Relation:**

$$N_f = \frac{1}{2} \left( \frac{\Delta\varepsilon_p}{\varepsilon_f'} \right)^{1/c}$$

**Engelmaier Temperature- and Frequency-Dependent Exponent:**

$$c = -0.442 - 6\times10^{-4}\,T_m + 1.74\times10^{-2}\,\ln(1 + f)$$

*Tm* = mean cyclic solder temperature (°C); *f* = cycling frequency (cycles/day)

**Miner's Linear Damage Accumulation:**

$$D = \sum_i \frac{n_i}{N_{f,i}} \qquad \text{failure predicted at } D = 1.0$$

Conservative IBM qualification target: **D ≤ 0.8**

---

## Root-Cause Analysis: IBM Power & zSystems

See [`docs_technical/root_cause_analysis.md`](docs_technical/root_cause_analysis.md) for
detailed analysis covering:

| Failure Mode | Primary Cause | Detection |
|---|---|---|
| C4 solder joint fatigue | CTE mismatch at max-DNP corner bumps | X-ray CT + SEM |
| Package warpage | Asymmetric substrate layer stackup | Shadow Moiré |
| TIM delamination | Pump-out and void growth under cycling | C-SAM acoustics |
| Electromigration | Current crowding at 7 nm node bump pitch | SEM/FIB cross-section |

---

## Developer Profile

**Background:** Nanotechnologist with expertise in:
- FEA modeling: Ansys Mechanical, nonlinear material models (Anand viscoplastic)
- CAD: SolidWorks 2024 parametric design, Parasolid/STEP export
- Scientific computing: Python (NumPy · SciPy · Pandas · Matplotlib), C++17
- Qualification standards: JEDEC JESD22-A104, IPC-9701A, IPC-7095D

---

## License

MIT — see [LICENSE](LICENSE) for details.
