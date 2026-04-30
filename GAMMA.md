# GAMMA.md

## Arena
Omission is a continuous research game. The repo is a persistent server. Work arrives as patches.

## Law 1: No root clutter
Root contains only README.md, GAMMA.md, .gitignore.

## Law 2: Outputs are artifacts
All visual results go to outputs/.

## Law 3: Dashboard is artifact-native
Dashboard does not understand neuroscience. It only renders valid artifacts.

## Law 4: Scientific modules live in src/
Each fXXX module owns one analysis objective.

## Law 5: Context is memory, not execution
context/ stores protocols, specs, decisions, and audits.

## Law 6: Tools are operational
tools/ contains scripts that maintain, validate, migrate, or audit the repo.

## Law 7: Archive is cold storage
archive/ contains deprecated logs, old packages, test artifacts, and historical traces.

## Patch format
Every new objective must specify:
- target folder
- expected output artifact
- validation command
- dashboard visibility
- rollback plan
