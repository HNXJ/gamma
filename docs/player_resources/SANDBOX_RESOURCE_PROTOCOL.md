# Sandbox Resource Protocol

This protocol dictates resource management within the Gamma Labyrinth world:

- **Requesting Resources:** Players can request tools or sandbox resources by outputting a `resource_request_or_null` object in their JSON action.
- **Trading Tools:** Traders can exchange tools via `trade_offer_or_null`.
- **Proposing Patches:** Patchsmiths can propose runtime prompt or artifact policy patches via `patch_proposal_or_null`.
- **Voting:** Critic Judgelets and Council stances evaluate and vote on patches to authorize hot-apply.
- **Provenance:** Archivists log decisions, trades, and patch approvals.
- **Sandbox Curation:** Sandbox Curators can bundle requested files and define requirements for out-of-band workers to implement.
- **Separation of Execution:** Any source code changes or executable execution of unverified resources requires a separate worker to execute out-of-band and commit/generate receipts.
