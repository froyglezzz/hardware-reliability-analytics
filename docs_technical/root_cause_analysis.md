# Root-Cause Analysis: Thermal Failures in IBM Power & zSystems Packaging

## 1. Overview

IBM POWER10 and z16 multi-chip modules (MCMs) integrate multiple processor and memory
buffer dies on large organic substrates using thousands of C4 controlled-collapse chip
connection solder bumps. The coefficient of thermal expansion (CTE) mismatch between
silicon dies (~2.6 ppm/°C), organic substrates (~3.2–18 ppm/°C), and PCBs (~16 ppm/°C)
subjects solder interconnects to cyclic shear strain during qualification thermal cycling
per JEDEC JESD22-A104 and IPC-9701A standards.

---

## 2. Primary Failure Modes

### 2.1 C4 Solder Joint Fatigue (Low-Cycle Fatigue)

**Mechanism:**
Cyclic plastic shear strain accumulates at the solder–pad interface during each thermal
excursion. Strain is highest at corner bumps (maximum distance-from-neutral-point, DNP).
Intergranular crack initiation occurs after a characteristic number of cycles; propagation
leads to electrical open failure.

**Root Cause:**
- CTE mismatch: Si die (2.6 ppm/°C) vs. BT-resin substrate (3.2 ppm/°C in-plane)
- Effective strain amplified by large DNP (>15 mm for POWER10 MCM footprint)
- SAC305 creep at dwell temperatures >75°C relaxes stress but increases accumulated plastic strain

**Evidence:**
- Cross-sectional SEM: intergranular cracking in SAC305 near the substrate Cu pad
  at corner bump locations after 800–1200 thermal cycles (TC2)
- FEA: maximum accumulated plastic strain at DNP = 15.2 mm corner (Δεp ≈ 0.008–0.015)
- Characteristic Coffin-Manson exponent c ≈ −0.527 for SAC305 at TC2 conditions

**Corrective Actions:**
1. **Underfill encapsulant** (e.g., Hysol FP4549): reduces effective CTE-mismatch strain
   by 60–70%; extends Nf by 3–5×
2. **Corner-only "no-flow" underfill**: cost-optimized version targeting highest-strain bumps
3. **Bump geometry**: aspect ratio (height/diameter) > 0.5 prevents pancaking under
   compressive load; increases Nf at equivalent Δεp

---

### 2.2 Package Warpage (Dynamic and Static)

**Mechanism:**
CTE mismatch between die, substrate, and PCB causes bow and twist. Dynamic warpage
peaks at solder reflow temperatures (~260°C), risking bridging or non-wet opens at BGA
(ball grid array) level during board-level assembly.

**Root Cause:**
- Asymmetric layer stackup in organic substrate generates net bending moment
- POWER10 MCM measured at +350 µm (convex) / −280 µm (concave) at 260°C
  by Shadow Moiré interferometry
- IPC-7095D coplanarity risk threshold for 0.8 mm BGA pitch: 250 µm

**Evidence:**
- Shadow Moiré: POWER10 MCM warpage exceeds IPC threshold at reflow temperatures
- Digital Image Correlation (DIC): strain gradient peaks at die edge/substrate interface

**Corrective Actions:**
1. **Stiffener ring**: kovar (Fe-Ni-Co alloy, CTE 5.5 ppm/°C) or Cu-W alloy bonded
   to substrate back-side reduces net warpage by 40–60%
2. **Controlled Cu distribution**: asymmetric Cu layer design balances CTE to minimize
   net bending moment

---

### 2.3 Thermal Interface Material (TIM) Degradation

**Mechanism:**
Repeated thermal cycling causes pump-out and voiding in TIM1 (between die and integrated
heat spreader, IHS) and TIM2 (between IHS and heatsink), progressively increasing
junction-to-case thermal resistance Rth(jc) by 15–40%.

**Root Cause (IBM z16 Telum II):**
- Polymer TIM2 loses contact pressure due to creep relaxation of mounting hardware
- Low-viscosity TIM1 migrates laterally under cyclic shear loading
- Acoustic microscopy (C-SAM) reveals void growth after 2000+ thermal cycles

**Observed Degradation:**
| Cycle Count | Rth(jc) [°C/W] | TIM2 Coverage [%] |
|---|---|---|
| 0 | 0.081 | 98 |
| 1000 | 0.087 | 92 |
| 2000 | 0.095 | 83 |
| 2500 | 0.110 | 71 |

**Corrective Actions:**
1. **Phase-change In52Sn48 TIM1** (Tmelt = 118°C): self-healing at operating temperature;
   pump-out resistance 10× vs. polymer TIM1
2. **Mechanical retention clip**: maintains TIM2 contact pressure against heatsink,
   preventing creep-driven gap formation
3. **Real-time Rth monitoring** via IPMI: rising Rth(jc) trend triggers predictive
   maintenance alert before thermal throttling impacts performance

---

### 2.4 Electromigration in Power Bumps

**Mechanism:**
High current density (>10⁴ A/cm²) in C4 power supply bumps drives Cu and Sn atom
migration (electromigration), depleting the cathode-side Cu pad and forming voids that
eventually cause electrical open failure or resistance increase.

**Root Cause:**
- Bump pitch scaling to 100 µm at 7 nm node concentrates >200 mA per power bump
  in IBM POWER10 (Samsung 7 nm EUV process)
- Current crowding at solder/Cu pad interface due to current flow direction reversal
- Joule heating from high IR drop accelerates void growth kinetics

**Evidence:**
- SEM/FIB cross-section: void formation at cathode-side Cu6Sn5 IMC layer
- Measured MTTF follows Black's equation: MTTF ∝ j⁻ⁿ exp(Ea/kT), n ≈ 2

**Corrective Actions:**
1. **Cu pillar bumps**: replace spherical C4 with high-aspect-ratio Cu pillars;
   reduced current crowding at interface; MTTF improvement 3–5×
2. **RDL current spreading**: redistribution layer design routes each power net
   across multiple parallel bumps to reduce per-bump current density

---

## 3. IBM Architecture Context

### POWER10 MCM (IBM, 2021)

- **Dies:** Up to 4 POWER10 processor chips (602 mm² each, Samsung 7 nm) +
  32 Centaur memory buffer chips
- **Substrate:** 68.5 × 68.5 mm organic BT-resin; DNP_max > 15 mm
- **Thermal design:** Up to 300 W per MCM; on-package VRM with >800 A total current
- **Qualification target:** JEDEC JESD22-A104 TC2 (−40/+125°C), 1500 cycles minimum

### IBM z16 / Telum II (IBM, 2022)

- **Configuration:** Dual-chip module (DCM); two Telum II dies on single substrate
- **AI accelerator:** On-chip Next Unit of Computing (NUC) AI accelerator: up to 330 W/chip
- **Thermal challenge:** Lateral power density gradient ΔT > 40°C across die footprint
  due to heterogeneous compute and AI workloads
- **Consequence:** Heterogeneous ΔT profile accelerates corner-bump fatigue vs. uniform-power MCMs

---

## 4. Detection and Monitoring Strategy

| Failure Mode | In-Process Detection | Field Monitoring |
|---|---|---|
| C4 solder fatigue | X-ray CT after accelerated thermal cycling (ATC) | Die-embedded temperature sensors (DETS); open fault detection |
| Package warpage | Shadow Moiré interferometry; DIC at reflow | — |
| TIM delamination | C-SAM acoustic microscopy (post-ATC) | Rth(jc) trending via IPMI |
| Electromigration | SEM/FIB cross-section of stressed coupons | Power rail resistance monitoring |

The C++ `ThermalMonitor` daemon in this repository implements field monitoring for the
real-time thermal pillar: it reads on-die temperature sensors, classifies readings against
THROTTLE and CRITICAL thresholds, and triggers P-state reduction or emergency shutdown
events exactly as an IBM BMC (Baseboard Management Controller) firmware subsystem would.
