# Omission

## What this game is
A continuous open-world biophysical neuroscience game: build, simulate, optimize, and interpret cortical circuits.

## Game loop
Data -> Model -> Simulate -> Compare -> Optimize -> Unlock -> Patch

## Flowchart
[placeholder: circuit growth flowchart]

## Core gameplay
1. Start with minimal E/PV/SST circuit.
2. Tune spontaneous dynamics.
3. Add omission paradigm.
4. Match spikes/LFP/TFR/SFC/RSA.
5. Unlock larger circuits and new mechanisms.

## Unlock tree
10 neurons  -> 7 E, 2 PV, 1 SST
40 neurons  -> VIP unlock
100 neurons -> L4 unlock
200 neurons -> second cortical area
300 neurons -> two columns in lower area
400 neurons -> upper area formation
500 neurons -> NMDA unlock

## Dashboard
The dashboard displays HTML artifacts from outputs/.
Each analysis module must write:
outputs/<artifact_id>/index.html
outputs/<artifact_id>/meta.json
