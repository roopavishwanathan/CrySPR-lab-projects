# Research Task: Mapping Cross-Chain Bridge Vulnerabilities to Real-World Attacks (2021–2026)

## Objective

The objective of this task is to identify vulnerabilities in cross-chain bridges discussed in existing research papers and determine how these vulnerabilities were exploited in real-world cross-chain bridge attacks between 2021 and 2026.

The final goal is to establish a **systematic mapping between vulnerabilities identified in academic literature and the actual attacks observed during this period**.

## Input Data

Two datasets will be provided:

1. **Research Papers:** A CSV file containing the titles of research publications related to cross-chain bridges, blockchain interoperability, and security.
2. **Cross-Chain Bridge Attacks:** A previously compiled dataset of cross-chain bridge attacks that occurred between 2021 and 2026.

## Task 1: Review Research Publications

Go through each publication listed in the provided CSV file and determine whether it discusses vulnerabilities in cross-chain bridges.

For every paper:

- Identify whether the paper discusses cross-chain bridge vulnerabilities.
- Extract the specific vulnerabilities identified or analyzed.
- Explain the technical cause of each vulnerability.
- Identify the affected bridge component or protocol.
- Record whether the vulnerability was theoretically identified, experimentally demonstrated, or observed in an actual attack.
- Document the relevant sections or pages of the paper supporting the findings.

Papers that do not discuss cross-chain bridge vulnerabilities should be marked as **Not Relevant**, with a brief justification.

## Task 2: Analyze Real-World Bridge Attacks (2021–2026)

Examine the previously collected cross-chain bridge attacks and identify the vulnerabilities exploited in each incident.

For every attack, document:

- Name of the affected bridge or protocol.
- Date of the attack.
- Vulnerability exploited.
- Technical explanation of how the attack was executed.
- Affected component, such as smart contracts, validators, relayers, or cross-chain message verification.
- Supporting references, including incident reports, postmortems, or technical analyses.

## Task 3: Map Vulnerabilities to Attacks

Establish a mapping between the vulnerabilities discussed in the research papers and those exploited in real-world attacks.

For each mapping:

1. Identify the research paper discussing the vulnerability.
2. Identify the corresponding vulnerability and its technical characteristics.
3. Identify the real-world attack that exploited the same or a closely related vulnerability.
4. Explain how the vulnerability enabled the attack.
5. Provide evidence supporting the relationship between the vulnerability and the attack.

Classify each mapping as:

- **Direct Match:** The paper explicitly analyzes the vulnerability exploited in the incident.
- **Technical Match:** The paper describes the same underlying vulnerability or failure mechanism, without necessarily discussing the specific incident.
- **Related:** The paper discusses a related security weakness, but a direct technical correspondence cannot be established.
- **No Match:** No corresponding vulnerability or attack was identified.

Do not assume that a vulnerability caused an attack merely because the paper and incident concern the same bridge.

## Expected Deliverables

### 1. Paper Vulnerability Analysis (`paper_vulnerabilities.csv`)

| Paper Title | Year | Relevant? | Vulnerability | Root Cause | Affected Component | Evidence |
|---|---|---|---|---|---|---|
| Paper A | 2023 | Yes | Vulnerability X | Technical cause | Smart contract | Section 4 |
| Paper B | 2024 | No | N/A | N/A | N/A | Justification |

### 2. Attack Analysis (`bridge_attacks_analysis.csv`)

| Attack | Date | Vulnerability Exploited | Exploitation Mechanism | Evidence |
|---|---|---|---|---|
| Attack A | 2022 | Vulnerability X | Explanation | Incident report |
| Attack B | 2024 | Vulnerability Y | Explanation | Technical analysis |

### 3. Vulnerability-to-Attack Mapping (`vulnerability_attack_mapping.csv`)

| Research Paper | Vulnerability | Real-World Attack | How It Was Exploited | Match Type | Evidence |
|---|---|---|---|---|---|
| Paper A | Vulnerability X | Attack A | Technical explanation | Direct Match | Paper + incident report |
| Paper B | Vulnerability Y | Attack B | Technical explanation | Technical Match | Paper + postmortem |

### 4. Summary Report (`findings.md`)

Prepare a concise summary discussing:

- The vulnerabilities most frequently identified in academic literature.
- The vulnerabilities most frequently exploited in real-world attacks.
- Which academic vulnerabilities correspond to documented attacks.
- Vulnerabilities identified in research that have not been linked to known attacks.
- Real-world attacks whose underlying vulnerabilities were not covered by the reviewed publications.
- Common security weaknesses and recurring exploitation patterns.

## Important Guidelines

- Use the provided publication CSV as the starting point.
- Review the actual papers rather than relying exclusively on their titles or abstracts.
- Every vulnerability and attack mapping must be supported by references.
- Distinguish between a vulnerability, its root cause, an exploitation technique, and the resulting attack.
- Avoid speculative mappings.
- A paper published after an attack may analyze that attack retrospectively; do not describe it as having predicted the vulnerability.
- If evidence is insufficient, explicitly mark the mapping as uncertain or unverified.
- Preserve the distinction between attacks occurring in 2021–2026 and publications discussing those attacks.

## Completion Criteria

The task is complete when every publication in the provided CSV has been reviewed, every attack in the 2021–2026 dataset has been considered, and all supported vulnerability-to-attack relationships have been documented with appropriate references.

The final output should provide a clear, reproducible understanding of **which cross-chain bridge vulnerabilities were identified in research, which were exploited in practice, and how those vulnerabilities contributed to real-world attacks**.
