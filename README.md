# BtALDH3_MD
Repository for BtALDH3 MD simulation protocol

## 1. Abstract
This repository contains molecular dynamics (MD) simulation data and analysis code for the manuscript **<ins> A Sequence Motif Enables Widespread Use of Non-Canonical Redox Cofactors</ins>** in Natural Enzymes published in Nature Chemical Biology. We performed  MD simulations (20 ns per system) on BtALDH3 WT, mutant variants R289A, H290A, H290L, R293A, and R289A/H290A/R293A to pinpoint the effect of the RH/QxxR motif in stabilizing the catalytically important E333-G337 loop.

---

## 2. MD Simulation Data
The MD data of different variants was stored in separate directories (BtALDH3 xx):
| File | Description |
|-----:|---------------|
|     Initial Structure protonated.pdb   |     GROMACS Initial input structure, whose protonation states were assigned by  H++          |
|     Final Processed Frame_replicate[1-5].gro  |   The end frame for 250ns production simulations of each system were run in quintuplicate            |

---

# Molecular Dynamics Simulation Protocol

This repository contains the workflow for reproducing the molecular dynamics (MD) simulations reported in our study.

## 1. Requirements

* **Software:** GROMACS 2025.3 (MPI-enabled, compiled with GNU compilers) 


* **Hardware:** A high-performance computing (HPC) cluster with GPU acceleration is required for the production phase.
* **Input Files:** Ensure the following files are in your working directory: `Initial Structure protonated.pdb`
* Parameter files: `ions.mdp`, `em_real.mdp`, `nvt.mdp`, `npt.mdp`, `md-250ns.mdp`



## 2. Step-by-Step Commands

### 1) System Preparation

Generate the topology, define the simulation box, solvate the system, and add ions to neutralize the charge.

```bash
# 1. Generate topology from PDB
# Input '1' selects the Force Field (Adjust based on your specific force field index)
echo 1 | gmx_mpi pdb2gmx -o protein.gro -water tip3p -ignh -f Initial Structure protonated.pdb

# 2. Define simulation box (Dodecahedron, 1.0 nm buffer)
gmx_mpi editconf -f protein.gro -o newbox.gro -bt dodecahedron -d 1.0

# 3. Solvate the system
gmx_mpi solvate -cp newbox.gro -cs spc216.gro -p topol.top -o solv.gro

# 4. Add Ions
# Prepare the ion generation run input file
gmx_mpi grompp -f ions.mdp -c solv.gro -p topol.top -o ions.tpr -maxwarn 1

# Replace solvent molecules with ions (Concentration: 0.1 M, Neutralize)
# Input '13' selects the solvent group (SOL) for replacement
echo 13 | gmx_mpi genion -s ions.tpr -o solv_ions.gro -p topol.top -pname NA -nname CL -conc 0.1 -neutral

```

### 2) Energy Minimization (EM)

Relax the structure to remove steric clashes.

```bash
# Assemble EM binary input
gmx_mpi grompp -f em_real.mdp -c solv_ions.gro -p topol.top -o em.tpr

# Run Energy Minimization
gmx_mpi mdrun -v -deffnm em

```

### 3) Equilibration

Bring the system to the desired temperature (NVT) and pressure (NPT).

> **Note:** These steps utilize GPU offloading for bonded interactions, non-bonded interactions, PME, and updates.

```bash
# --- NVT Equilibration (Temperature) ---
gmx_mpi grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr

# Run NVT with GPU acceleration
gmx_mpi mdrun -deffnm nvt -nb gpu -bonded gpu -pme gpu -update gpu -nstlist 40 -v

# --- NPT Equilibration (Pressure) ---
gmx_mpi grompp -f npt.mdp -c nvt.gro -r nvt.gro -p topol.top -o npt.tpr

# Run NPT with GPU acceleration
gmx_mpi mdrun -deffnm npt -nb gpu -bonded gpu -pme gpu -update gpu -nstlist 40 -v

```

### 4) Production Run

Perform the final data collection run.

> **⚠️ Important:** The production phase is computationally intensive and requires High-Performance Computing (HPC) resources to complete.

```bash
# Assemble production binary input
gmx_mpi grompp -f md-250ns.mdp -c npt.gro -r npt.gro -p topol.top -o md-250ns.tpr

# Run Production MD (250 ns)
gmx_mpi mdrun -deffnm md-250ns -nb gpu -bonded gpu -pme gpu -update gpu -nstlist 40 -v

```

---

# Post-Simulation Analysis: RMSF & Statistical Comparison

This section details the workflow for extracting post-simulation data and performing Root Mean Square Fluctuation (RMSF) analysis using GROMACS, automated by the provided Python script.

## 1. Methodology

For each trajectory, the following protocol was applied:

1) **Trajectory Processing:** Monomers were aligned to a reference structure to remove rotational and translational motions.
2) **RMSF Calculation:** RMSF values were computed specifically for **Cα atoms** across residues **333–337** to quantify local flexibility in this region.
3) **Statistical Analysis:**
* RMSF values were averaged across residues for each simulation.
* Values were subsequently averaged across all ten monomers.
* Pairwise statistical comparisons between RMSF values of ALDH variants were performed using a **two-tailed Welch’s t-test**.



## 2. Automated Workflow (`run_rmsf_BtALDH.py`)

We provide a wrapper script, `run_rmsf_BtALDH.py`, which automates the GROMACS processing pipeline (PBC correction, centering, fitting, and calculation).

### Prerequisites

Ensure the following files are in your working directory:

* `md-250ns.tpr` (Run input file)
* `md-250ns.xtc` (Trajectory file)
* `em.gro` (Energy minimized structure for index generation)
* `md-250ns.gro` (Final coordinates)

### How to Run

Execute the script using Python. Ensure GROMACS (`gmx_mpi`) is in your system path.

```bash
python run_rmsf_BtALDH.py

```

> **Note:** Open `run_rmsf_BtALDH.py` before running to verify the **User Settings** at the top of the file (specifically `center_group_id` or atom indices) match your specific system configuration.

## 3. Statistical Analysis (Post-Script)

After generating `rmsf.xvg` files for all variants/replicates:

1. Import the `.xvg` data into your statistical software of choice (Python/Pandas, R, etc.).
2. Compute the mean RMSF for the target region (Residues 333-337).
3. Apply **Welch’s t-test** (two-tailed) to determine significance between variants.
