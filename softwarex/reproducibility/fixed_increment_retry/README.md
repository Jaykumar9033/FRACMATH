# Smaller fixed-increment diagnostic

The fresh baseline MATLAB reference uses the exact Abaqus job mesh and
20,000 fixed increments to the target -0.2 mm. It completed and saved finite
states. The matched Abaqus run did not complete: 5,175 increments were accepted
before equilibrium failure. The input, message/status files and execution
record are supplied as diagnostics, not as a full structural comparison.
No adaptive replacement or NO STOP option was used. The final ODB export
and partial response comparison have not yet been verified for this retry.

The coarse 4,000-increment matched retry is running separately. It is not
included as a completed result here. The saved preparation plan includes its
settings for provenance, but only the finished baseline attempt is archived.
Source snapshots and the complete MATLAB baseline reference are retained.
ODB files, compiled scratch files and obsolete references are omitted.
