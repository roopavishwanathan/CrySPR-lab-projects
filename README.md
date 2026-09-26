# Cross-chain bridge attacks, 2024–2026

**Everything is in one Google Sheet:**
**[Bridge attacks 2024–2026](https://docs.google.com/spreadsheets/d/1MhSCJYcW39mgKk2ZfHMcZe6_hO6vlo08x65mXzlIJcA/edit?usp=sharing)**

Start on the **Summary** tab. This page is just a guide to it.

---

## The sheet

| Tab | What it holds |
|---|---|
| **Summary** | headline numbers, this week's findings, the open questions |
| **Attacks** | the corpus: one row per attack, 13 columns |
| **Buckets** | the ten failure patterns, each with a membership test (names still to be agreed) |
| **Bucket members** | every attack under its bucket, with the reason it is there |
| **Excluded (discuss)** | the rows that did **not** make the corpus, described, grouped, with the case for and against each arguable group |
| **Legend** | column definitions |

**As of 25 September 2026: 67 attacks, $817.9M** — 61 confirmed bridge attacks plus 6 marked
*adjacent* (cross-chain, but the bridge itself was not what was attacked).
By year: 2024: 9 · 2025: 11 · 2026: 47.

## What counts as a bridge attack

Every row was checked by hand against a written test, using the project's own statement or a
detailed technical report — **not** a database's category flag.

> A bridge attack targets something that moves assets or messages **between chains**: the bridge
> contracts (lock / mint / burn / release), the verification of cross-chain messages (validators,
> relayers, light clients, verifier networks, proofs), the keys that control the bridge, or its peg.

Three questions decide a row: *did the attack cross a chain boundary, or only appear to? was the
thing attacked part of the crossing, or merely a user of it? did anything forged actually leave
over the bridge?* Evidence standard: a database category alone is never enough.

**This changed the dataset in both directions.** The scripts found 75 candidates; 61 survived.
Fifteen were not bridge attacks (privacy mixers, cross-chain lending apps, a meme coin the name
filter caught), three were duplicates, and three more attacks happened after the first pass. The
database flag wrongly *included* Kinto and Harmony, and was the only source that recorded
warp.green, which turned out to be real. Two of the excluded rows — FOOM Cash and Veil Cash — are
filed by DefiLlama under "Bridge & Cross-Chain" and neither is cross-chain at all.

## Where the data came from

Nine sources, collected by script, then verified by hand.

| Source | Method | Incidents contributed |
|---|---|---|
| DefiLlama | `api.llama.fi/hacks` | 64 |
| SlowMist Hacked | the Bridge category, paginated | 47 |
| Google News RSS + GDELT | monthly windowed queries, 406 items | 29 |
| Rekt News | leaderboard + homepage, 80 posts | 18 |
| DeFiHackLabs | GitHub READMEs + Foundry PoCs | 11 |
| Security-firm blogs | 11 sitemaps/feeds, 385 posts | 3 |
| Academic papers | Semantic Scholar + DBLP, 457 papers, 124 full texts | 0 new |
| Annual reports | public URLs (most are gated) | 0 |
| X | needs a paid API tier | not run |

Plus the projects' own post-mortems and announcements, cited row by row in the sheet.

Measured against the hand-verified set the pipeline reaches **93% recall**, and it found five
attacks the manual search had missed (Long Bridge, Butter Bridge, TeleSwap, Transit, Chainflip).

The collection scripts and the full per-attack write-ups are not in this repository — they are
large and still moving. Say the word and I will add whichever part is useful.

## Things Pending

Each is a filter over already-labelled data, so either answer is cheap — no re-work either way.

1. **Scope.** Do cross-chain *apps* count (Radiant, Tapioca — $59.2M)? Do *aggregators* count
   (LI.FI, Bungee — $15.4M, which lose users' token approvals rather than bridge funds)? Does a
   bridge's hijacked *website* count (LayerSwap)? Every case is on the **Excluded (discuss)** tab.
2. **Bucket names.** Ten patterns are defined and tested; none is named yet.
3. **Accounts affected.** Disclosed for only 8 of 67 (action item 2). Reconstruct it on-chain, or
   write to the projects?
4. **Non-bridge attacks in the paper.** Worth keeping as a contrast class, or out of scope?



