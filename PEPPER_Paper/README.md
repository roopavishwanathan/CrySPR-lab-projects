# PEPPER paper collection

Copied from Desktop projects on 2026-10-30. Original files were not modified.

- `SGX_BASED_AUCTION/`: SGX auction implementation, bidder/client/manager programs, Solidity contracts, deployment scripts, Go bindings, saved build artifacts, and experiment timing logs.
- `PrivacyPreservingAuction/`: earlier Solidity/Go/Python proof of concept, with its original run instructions.
- `figures/enclave_output/`: plotting script explicitly naming PEPPER and TRUSTEE, its PDF/PNG output, and saved data.
- `figures/legacy_diagrams/`: older PEC diagrams and presentations. These predate the current reputation work; exact paper usage is not independently verified.
- `legacy_from_PEC_Auction/`: price-only auction contract and associated legacy scripts, Go programs, interface, configuration, and test stub recovered from the current mixed project. Versions remain separate from the older projects.

`MANIFEST.json` records every copied file's original absolute path, size, and SHA-256. All copied files were verified byte for byte. No code was changed or executed; compatibility of these historical versions has not been tested.

The current COOKIE contract (`auction_2.sol`), reputation experiments and figures, agent marketplace experiments, and current paper drafts are excluded. Unrelated reference papers and blockchain fee-analysis projects are excluded. The mixed thesis references missing PEPPER chapter files; those missing files were not recovered here.

Private keys, .env credentials, compiled executables, Git internals, and Python caches are omitted. Existing public keys and enclave configuration are retained; generate/configure local signing credentials before building. Original source files remain in their original locations.
