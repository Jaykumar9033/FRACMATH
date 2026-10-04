# Three timing observations

The baseline observation is in `../scaling_study`. `observation_2` and
`observation_3` preserve two additional complete 30-configuration studies.
Each archive contains the common mesh, numerical source snapshot, MATLAB
states, Abaqus decks and diagnostic files, response histories and logs.
ODBs and compiled binaries are excluded. SHA256 manifests preserve archive,
member and supporting-file integrity.

`analysis/timings.csv` contains all three measured times, their median and
observed range. The range is not a confidence interval. MATLAB times cover
the load loop; Abaqus times cover analysis and output. These scopes and the
different equilibrium algorithms qualify comparisons between programs.

All saved MATLAB numerical arrays and exported Abaqus response arrays are
identical across observations within each setting. Timing values are not
expected to reproduce exactly. Computing configurations use the same mesh;
the third observation reverses their execution order.

From the repository root, extract and analyze each additional observation:

```powershell
python softwarex/archive_scaling_study.py extract --package softwarex/reproducibility/timing_repeats/observation_2 --workspace C:/runs/timing_repeats/observation_2
python softwarex/analyze_scaling_study.py --workspace C:/runs/timing_repeats/observation_2 --output C:/runs/timing_repeats/observation_2/analysis
python softwarex/archive_scaling_study.py extract --package softwarex/reproducibility/timing_repeats/observation_3 --workspace C:/runs/timing_repeats/observation_3
python softwarex/analyze_scaling_study.py --workspace C:/runs/timing_repeats/observation_3 --output C:/runs/timing_repeats/observation_3/analysis
python softwarex/analyze_timing_repeats.py --baseline C:/runs/scaling_study --workspace C:/runs/timing_repeats
```

Extract the baseline using the instructions in `SCALING_STUDY.md` first.
Archive extraction verifies SHA256 values and refuses to replace a differing
existing file. A fresh simulation workspace is required to rerun solves.
