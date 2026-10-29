# Beginner-entry numerical reproduction

The actual `start_here.m` entry runs 10,000 steps with CPU backend and one
computational thread. Graphics alone are disabled for this check; numerical
settings are retained. The tested entry and solver/mesh copy, console output,
saved state, complete histories and comparison manifest are archived here.

All eight geometry/history/response arrays and six peak/post-peak snapshot
arrays or values exactly equal the preserved benchmark: nodes, elements,
displacement, damage, equivalent-strain history, load, CMOD and residual.
The binary MAT hashes differ because run metadata/timers are not numerical
response arrays. The comparison tests the numerical arrays directly.
This is a numerical reproduction check, not a timing observation.

From the repository root, inspect the saved evidence:

```powershell
python softwarex/analyze_beginner_entry.py --workspace softwarex/reproducibility/beginner_entry_check
```

For a fresh execution, copy this folder into a separate workspace and run
`matlab -batch start_here` there. It calls the archived solver and mesh and
writes `student_results`. The package's ordinary entry enables graphics.
