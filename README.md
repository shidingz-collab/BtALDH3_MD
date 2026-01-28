# BtALDH3_MD
Repository for BtALDH3 MD simulation protocol

## Abstract
This repository contains molecular dynamics (MD) simulation data and analysis code for the manuscript A Sequence Motif Enables Widespread Use of Non-Canonical Redox Cofactors in Natural Enzymes published in Nature Chemical Biology. We performed  MD simulations (20 ns per system) on BtALDH3 WT, mutant variants R289A, H290A, H290L, R293A, and R289A/H290A/R293A to pinpoint the effect of the RH/QxxR motif in stabilizing the catalytically important E333-G337 loop.

---

## MD Simulation Data
The MD data of different variants was stored in separate directories (BtALDH3 xx):
| File | Description |
|-----:|---------------|
|     Initial Structure protonated.pdb   |     GROMACS Initial input structure, whose protonation states were assigned by  H++          |
|     Final Processed Frame_replicate[1-5].gro  |   The end frame for 250ns production simulations of each system were run in quintuplicate            |

---

# Molecular Dynamics Simulation Protocol

This repository contains the workflow for reproducing the molecular dynamics (MD) simulations reported in our study.

## Requirements

* **Software:** GROMACS 2025.3 (MPI-enabled, compiled with GNU compilers) 


* **Hardware:** A high-performance computing (HPC) cluster with GPU acceleration is required for the production phase.
* **Input Files:** Ensure the following files are in your working directory: `Initial Structure protonated.pdb`
* Parameter files: `ions.mdp`, `em_real.mdp`, `nvt.mdp`, `npt.mdp`, `md-250ns.mdp`



## Step-by-Step Commands

### 1. System Preparation

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

### 2. Energy Minimization (EM)

Relax the structure to remove steric clashes.

```bash
# Assemble EM binary input
gmx_mpi grompp -f em_real.mdp -c solv_ions.gro -p topol.top -o em.tpr

# Run Energy Minimization
gmx_mpi mdrun -v -deffnm em

```

### 3. Equilibration

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

### 4. Production Run

Perform the final data collection run.

> **⚠️ Important:** The production phase is computationally intensive and requires High-Performance Computing (HPC) resources to complete.

```bash
# Assemble production binary input
gmx_mpi grompp -f md-250ns.mdp -c npt.gro -r npt.gro -p topol.top -o md-250ns.tpr

# Run Production MD (250 ns)
gmx_mpi mdrun -deffnm md-250ns -nb gpu -bonded gpu -pme gpu -update gpu -nstlist 40 -v

```
