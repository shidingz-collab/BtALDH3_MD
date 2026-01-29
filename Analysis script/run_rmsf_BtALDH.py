import subprocess
import sys

def run_gmx(command, inputs=None):
    """
    Executes a GROMACS command with specific inputs.
    """
    print(f"\n[INFO] Executing: {command.split()[0]} ...")
    
    # Prepare input bytes if needed
    input_bytes = None
    if inputs:
        input_bytes = inputs.encode('utf-8')

    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Check for non-zero exit code
        if result.returncode != 0:
            print(f"[ERROR] Command failed:\n{command}")
            print(f"[ERROR] GROMACS Output:\n{result.stderr.decode('utf-8')}")
            sys.exit(1)
        else:
            print("[OK] Success.")
            
    except Exception as e:
        print(f"[CRITICAL] Script failed: {e}")
        sys.exit(1)

# ================= USER SETTINGS =================
# Modify these if your group numbers differ from the standard defaults
center_group_id = "17"   # The ID assigned to 'a 6391' in step 1
rmsf_group_id   = "17"   # The ID assigned to 'r 333-337 & a CA' in step 7
fit_group_id    = "4"    # Usually Backbone
system_group_id = "0"    # System

# ================= WORKFLOW =================

# 1. Create index for centering (Atom 6391)
# Input: 'a 6391', then 'q' to save and quit
cmd1 = "gmx_mpi make_ndx -f em.gro -o center.ndx"
inp1 = "a 6391\nq\n"
run_gmx(cmd1, inp1)

# 2. Process .gro: Make PBC whole
# Input: 0 (System)
cmd2 = "gmx_mpi trjconv -f md-250ns.gro -s md-250ns.tpr -pbc whole -o md-250ns_pbc.gro"
inp2 = f"{system_group_id}\n"
run_gmx(cmd2, inp2)

# 3. Process .gro: Center the molecule
# Input: 17 (Center atom), then 0 (System)
cmd3 = "gmx_mpi trjconv -f md-250ns_pbc.gro -s md-250ns.tpr -pbc mol -center -o md-250ns_pbc_center.gro -n center.ndx"
inp3 = f"{center_group_id}\n{system_group_id}\n"
run_gmx(cmd3, inp3)

# 4. Process .xtc: Make PBC whole
# Input: 0 (System)
cmd4 = "gmx_mpi trjconv -f md-250ns.xtc -s md-250ns.tpr -pbc whole -o md-250ns_pbc.xtc"
inp4 = f"{system_group_id}\n"
run_gmx(cmd4, inp4)

# 5. Process .xtc: Center the molecule
# Input: 17 (Center atom), then 0 (System)
cmd5 = "gmx_mpi trjconv -f md-250ns_pbc.xtc -s md-250ns.tpr -pbc mol -center -o md-250ns_pbc_center.xtc -n center.ndx"
inp5 = f"{center_group_id}\n{system_group_id}\n"
run_gmx(cmd5, inp5)

# 6. Fit rotation and translation
# Input: 4 (Fit group, usually Backbone), then 0 (System)
cmd6 = "gmx_mpi trjconv -f md-250ns_pbc_center.xtc -s md-250ns_pbc_center.gro -o md-250ns_aligned_for_RMSF.xtc -fit rot+trans"
inp6 = f"{fit_group_id}\n{system_group_id}\n"
run_gmx(cmd6, inp6)

# 7. Create index for RMSF calculation
# Input: 'r 333-337 & a CA', then 'q'
cmd7 = "gmx_mpi make_ndx -f md-250ns.gro -o rmsf_cal.ndx"
inp7 = "r 333-337 & a CA\nq\n"
run_gmx(cmd7, inp7)

# 8. Calculate RMSF
# Input: 17 (Your specific residue group)
# Note: I added filenames for -o and -od to ensure safety
cmd8 = "gmx_mpi rmsf -f md-250ns_aligned_for_RMSF.xtc -s md-250ns_pbc_center.gro -n rmsf_cal.ndx -od rmsf_deviations.xvg"
inp8 = f"{rmsf_group_id}\n"
run_gmx(cmd8, inp8)

print("\n[DONE] Processing complete.")