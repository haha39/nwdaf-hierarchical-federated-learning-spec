# Hierarchical NWDAF Federated Learning — Stage 2 Draft

Status: Project proposal for review; not a 3GPP specification.

The Definitions and abbreviations section and clauses 1–3 contain proposed text.
Clause numbering is local to this draft.
The applicable TS 23.288 snapshots and clause evidence are identified in the
informative notes below. Hierarchical composition, topology instructions,
topology reporting and recovery behavior are proposed additions that reuse
existing services.

## Definitions and abbreviations

### Definitions

For the purposes of this proposal, the applicable terms and definitions in
TS 23.288 apply, together with the following:

**Root NWDAF:** The NWDAF at the top of the hierarchy.

**Intermediate NWDAF:** An NWDAF acting as an FL Client towards its parent and
as an FL Server towards its direct children.

**Realized topology:** The currently known topology formed by confirmed
parent-child relationships during formation or operation.

**Accepted realized topology:** The realized topology that the root NWDAF has
accepted as satisfying the applicable formation requirements for the
hierarchical FL procedure.

**Participant-management policy:** Policy governing a receiving NWDAF's
selection and management of its direct children.

### Abbreviations

For the purposes of this proposal, the applicable abbreviations in TS 23.288
apply.

## 1. Hierarchical Federated Learning — Functional Description

Hierarchical federated learning enables NWDAFs containing MTLF to compose the
existing FL Server and FL Client functions described in clause 5.3 of TS 23.288
into a hierarchy. It applies to the horizontal federated learning described in
that clause. FL capabilities and discovery principles follow clause 5.2 of
TS 23.288.

An NWDAF's role is relative to a parent-child relationship in the current
hierarchical FL procedure. An intermediate NWDAF acts as an FL Client towards
its parent and as an FL Server towards its direct children. It receives model
training instructions from its parent, coordinates training and aggregation
with its direct children, and reports the resulting model information to its
parent. An NWDAF with no direct children performs the assigned local training.

The composition may be repeated at successive intermediate NWDAFs at any depth.

The accepted realized topology for one hierarchical FL procedure is a rooted
tree. Each NWDAF has at most one direct parent in that topology.

Dynamic topology formation, specified in clause 2, conveys selection
instructions towards the participating NWDAFs and returns the topology actually
established. Intermediate NWDAF failure recovery, specified in clause 3,
replaces an unavailable intermediate NWDAF and repairs the affected
relationships so that training can continue.

## 2. Dynamic Topology Formation

This procedure applies before training when an NWDAF containing MTLF determines
to use hierarchical federated learning. Existing FL initiation can follow local
configuration or a model request from a consumer as described in clause 5.3 of
TS 23.288. The decision to form a hierarchy and the instructions below are
additions to that baseline.

The participating entities are the root NWDAF, intermediate NWDAFs, their
candidate direct children and the NRF used for discovery. Every FL participant
contains MTLF. Each parent establishes and manages its own direct-child Model
Training subscriptions using the service operations described in clause 7.10
of TS 23.288. The NRF supplies candidate capability and discovery information.

The procedure is as follows:

1. The root NWDAF determines the training requirements and the initial topology
   instruction. The instruction identifies intended recipients and may identify
   known or preferred candidates for their direct children, candidate preference,
   selection requirements and permission to discover additional candidates.
   Instructions for further descendants may be included recursively. A listed
   candidate is not a confirmed participant.

   Participant-management policy governs the receiving NWDAF's selection and
   management of its direct children, including a minimum available participant
   requirement and permitted responses to partial failure. Permission to add
   candidates outside the supplied list must be explicit. Other unspecified
   decisions may follow local configuration within the authority granted by
   the parent. Policy does not automatically apply to all descendants.

2. The NWDAF acting as parent, initially the root NWDAF, discovers or resolves
   its candidate direct children using the principles in clauses 5.2 and
   6.2C.2.1 of TS 23.288. For a candidate expected to be an intermediate NWDAF,
   selection considers its ability to perform both FL roles. Analytics ID,
   model interoperability, data availability, time availability and applicable
   serving-area information retain their meanings in clauses 5.2 and 6.2F.2 of
   TS 23.288. Candidate preference applies among eligible candidates.

3. The parent sends an Nnwdaf_MLModelTraining_Subscribe request to each candidate
   selected for preparation. The request carries the existing training
   requirements and ML Preparation Flag described in clauses 6.2C.2.1 and
   6.2F.2 of TS 23.288, together with the proposed topology instruction relevant
   to that recipient. Any nested instruction is addressed to the corresponding
   descendant.

   The same ML Correlation ID is used throughout this hierarchical FL procedure.
   Each direct subscription retains its own subscription and notification
   correlation information. Hierarchy-wide use of the ML Correlation ID is a
   project-defined binding; the existing information element identifies an FL
   procedure as described in clause 6.2F.2 of TS 23.288.

4. The candidate checks the training requirements and decides whether to
   participate, following the preparation behavior in clause 6.2C.2.1 of
   TS 23.288. It also determines whether it can fulfil the hierarchical
   instruction. If it cannot, it reports the unsuccessful outcome and reason to
   its parent. A relationship is counted as established only after support for
   the required
   hierarchical behavior and participation have been confirmed at that edge.
   Each edge requires its own confirmation.

   Preparation does not start model training, as described in clause 6.2F.1 of
   TS 23.288. Establishing downstream relationships during hierarchical
   preparation is a proposed extension. A successful subscription response
   alone does not confirm completion of a descendant subtree.

5. If the candidate is instructed to establish direct-child relationships, it
   acts as their parent and repeats steps 2–4 for those children. It may add
   candidates discovered through the NRF only within the granted selection
   authority. Identity resolution and capability checks for supplied candidates
   are independent of permission to add candidates. Each further intermediate
   NWDAF repeats this procedure for its own children.

   Training and aggregation instructions, when supplied, describe the contract
   to be fulfilled by the participating NWDAFs; they are distinct from
   participant-management policy. The intermediate NWDAF conveys the applicable
   training contract downstream. An explicitly assigned contract is not silently
   replaced by a local choice.

   A parent may also specify how much local work a child performs before
   reporting a model update, for example local training epochs or, for an
   intermediate NWDAF, direct-child training rounds. If unspecified, that child
   may determine the cadence locally. This instruction is local to the addressed
   child and is not automatically inherited by its descendants. The maximum
   response time in clauses 6.2C.2.2 and 6.2F.2 of TS 23.288 applies alongside
   the reporting cadence.

6. Each parent records the outcome for the direct-child relationships it
   manages. Reports distinguish candidates awaiting confirmation, establishment
   in progress, confirmed participation, unsuccessful establishment and later
   removal or withdrawal. An unsuccessful or removed relationship includes its
   reason. A report identifies the affected NWDAF and the relationship, together
   with the time at which the responsible parent determined its status.

   An intermediate NWDAF sends its parent a topology report through the proposed
   extension of Nnwdaf_MLModelTraining_Notify. It identifies the reporting NWDAF,
   its direct-child outcomes and available descendant reports. Descendant status
   and status times are preserved when reports are combined. The reporting
   intermediate NWDAF's upstream relationship status is maintained by its
   parent. The report may include locally resolved policy, training contract or
   reporting cadence where relevant to the parent's acceptance decision.

7. Each parent evaluates the confirmed direct children it manages against the
   participant-management policy applicable to its local FL process. Only
   established subscriptions with satisfactory participation outcomes count
   towards availability. When the policy-defined minimum available participant
   requirement is satisfied, the parent reports that its local formation
   requirement has been met. It may continue candidate establishment after
   that requirement is met and report subsequent changes.

   If the requirement is not satisfied, the parent may try further candidates
   within its granted authority or report the unmet requirement upstream. The
   applicable requirement remains in effect until revised by an authorized
   upstream instruction. Decisions outside the granted authority are referred
   upstream through the outcome report. Hierarchy-wide acceptance is determined
   by the root NWDAF as described in step 8.

8. Reports are combined successively until the root NWDAF has the confirmed
   relationships and the outstanding or unsuccessful candidate outcomes. The
   confirmed relationships form the realized topology known at that point; the
   outstanding or unsuccessful candidate outcomes are reported alongside that
   topology.

   The root NWDAF evaluates the realized topology and the reported candidate
   outcomes against the applicable formation requirements. It may accept a
   partial or unbalanced realized topology when those requirements are
   satisfied, including when not every originally listed candidate is
   established. If the requirements are not satisfied, the root NWDAF may
   revise the applicable instruction or requirements and evaluate the updated
   result, or terminate establishment of the affected part.

   The accepted realized topology is a rooted tree in which each NWDAF has at
   most one direct parent. A relationship that would duplicate an NWDAF identity
   in the tree or create an ancestor cycle is not accepted.

9. When the root NWDAF has accepted the realized topology as satisfying the
   applicable formation requirements, training is initiated using the Federated
   Learning procedure in clause 6.2C.2.2 of TS 23.288.
   When a direct relationship established during formation is no longer needed,
   the parent managing that relationship invokes
   Nnwdaf_MLModelTraining_Unsubscribe as described in
   clause 7.10.3 of TS 23.288 to remove the corresponding subscription.

NOTE: Existing FL preparation checks may be skipped under the conditions in
clause 6.2C.2.1 of TS 23.288.

## 3. Intermediate NWDAF Failure Recovery

This procedure applies when an intermediate NWDAF becomes unavailable during
training, while the root NWDAF and the NWDAFs needed to coordinate repair remain
available. It addresses replacement, reparenting and subsequent training.

The participants are the surviving parent of the unavailable intermediate NWDAF,
a replacement intermediate NWDAF and the available children of the unavailable
intermediate NWDAF, including any subtrees below those children. The parent uses
its known realized topology from clause 2 to identify affected relationships. Last
reported information is input to repair.

The surviving direct parent may coordinate local repair within its granted
participant-management and selection authority. It may select a replacement,
establish the new parent-child relationship, trigger reparenting of the affected
subtree and collect the repaired topology report. If the required repair cannot
be completed within that authority, it reports the unmet repair requirement or
failure outcome upstream. This coordination applies recursively at any depth.
Changed realized topology is reported successively to the root NWDAF.

1. **Failure detection.** The parent determines, based on available observations
   and operator policy, whether its intermediate NWDAF client is unavailable and
   replacement is needed.

2. The parent identifies the unavailable intermediate NWDAF and its affected
   parent-child relationships. It excludes that NWDAF from participant selection
   for the current repair while the NWDAF is considered unavailable, and records
   the loss of the relationship. If the parent is itself an intermediate NWDAF,
   it reports the affected subtree upstream. For its affected training round,
   the parent may apply the existing waiting, skipping and partial-aggregation
   choices described in clauses 6.2C.2.2 and 6.2C.2.3 of TS 23.288, subject to
   applicable policy. Reports from unaffected direct children may still be used
   for that round.

3. **Replacement.** The parent selects a candidate replacement able to act as
   an FL Client towards it and as an FL Server towards the affected children.
   It considers known alternatives and, where permitted, NRF discovery, using
   the selection and preparation principles in clauses 6.2C.2.1 and 6.2C.2.3
   of TS 23.288. Selection accounts for the affected training requirements and
   serving area. If no suitable replacement is available, the parent reports
   unsuccessful or incomplete repair, with subsequent action following
   applicable policy. During repair, unaffected established relationships may
   continue to be used subject to applicable training requirements and
   participant-management policy.

4. The parent sends an Nnwdaf_MLModelTraining_Subscribe request to the replacement
   to establish a new direct subscription for preparation. The request supplies
   the affected subtree instruction, the same hierarchical FL procedure's ML
   Correlation ID, and the applicable training and participant-management
   instructions. Available children identified in the previous topology are
   candidates for reattachment and undergo confirmation as specified in clause 2.
   Unaffected subtrees are retained.

5. **Reparenting.** The replacement establishes new direct-child Model Training
   subscriptions with the affected children using clause 2. Each new
   subscription is a new and independent resource and provides notification
   target and correlation information for the replacement, as described in
   clauses 6.2F.2 and 7.10 of TS 23.288. Each edge retains its own subscription
   resource and notification-correlation lifecycle. After required preparation,
   hierarchical support and participation confirmation succeed, the new
   relationship may become an accepted edge in the repaired realized topology.
   The child's notifications
   for that new subscription are directed to the replacement. Failure to
   complete cleanup of, or Unsubscribe for, the old subscription associated
   with the failed parent does not by itself block establishment of the new
   relationship. The common ML Correlation ID continues to identify the
   hierarchical FL procedure, while subscription resource and
   notification-correlation state remain local to each edge.

   If an affected child is itself an intermediate NWDAF and its own downstream
   relationships remain usable, changing that child's upstream relationship
   does not require rebuilding its descendants. Those relationships are
   reconfirmed through the child's topology report. Other unaffected
   relationships in the hierarchy are retained.

6. Each affected child reports its participation outcome and available subtree
   information. The replacement combines these outcomes and reports the
   repaired topology to its parent as in clause 2. The parent checks the
   confirmed relationships against its repair policy and conveys the changed
   topology upstream. Each successive parent conveys the changed topology until
   the root NWDAF obtains an updated hierarchy view. Incomplete repair may lead
   to further selection or adjustment within the granted authority. Confirmation
   of repair covers the accepted relationships.

7. **Training continuation.** Once the repaired relationships satisfy the
   applicable requirements, the surviving parent supplies a valid current model
   baseline and subsequent training instructions to the repaired subtree through
   the replacement. The replacement coordinates downstream training and reports
   aggregated model information upstream using the training procedure in
   clauses 6.2C.2.2 and 6.2F.1 of TS 23.288. The same ML Correlation ID continues
   to identify the hierarchical FL procedure, while subscription identities and
   iteration progress remain local to each parent-child process.

   The hierarchical FL job can thus make new training progress after repair
   without rebuilding unaffected relationships or restarting the whole hierarchy
   from initial formation. Work interrupted or not successfully delivered and
   accepted before failure is not assumed reusable. The procedure does not
   require recovery of the failed intermediate NWDAF's runtime state or its
   interrupted local round.

8. Ordinary updates of model information, local iteration and training deadlines
   use the established relationships. They do not repeat topology formation.
   Membership or parent-child changes update the affected topology and its
   reports. A change to a policy or training contract is an instruction update;
   it does not by itself require reconstructing unchanged relationships.

## Evidence and drafting notes (informative)

### Normative sources

All baseline references below are to TS 23.288. The compared snapshots are:

- R18: Release 18, V18.13.0, source archive `23288-id0.zip`. The
  specification-derived corpus and its manifest were inspected in the
  `nwdaf-docs` repository; its specification guide was used for navigation, not
  as a substitute for source text.
- R19: Release 19, V19.7.0, source archive `23288-j70.zip`.
- R20: Release 20, V20.1.0, source archive `23288-k10.zip`; primary drafting
  baseline. R19 and R20 provenance is in
  [the workspace manifest](../../references/manifest.yaml).

| Evidence | Clauses and titles | Release support and use |
| --- | --- | --- |
| B1 | 5.1 **General**; 5.3 **Federated Learning (FL) among multiple NWDAFs** (R18), **Horizontal Federated Learning (FL) among multiple NWDAFs** (R19/R20) | All three: MTLF/AnLF, general hierarchy deployment, FL roles and initiation. General hierarchy deployment is not evidence of the proposed formation/recovery protocol. |
| B2 | 5.2 **NWDAF Discovery and Selection**; 6.2C.2.1 **Registration and Discovery procedure for Federated Learning** | All three: FL capabilities, including support for both roles; discovery criteria; preparation, participation decisions and conditional omission of preparation. |
| B3 | 6.2C.2.2 **General procedure for Federated Learning among Multiple NWDAF Instances** | All three: steps 2–5 describe model distribution, reporting, delay and aggregation choices; steps 6–9 and the accompanying text describe continuation and termination. No evidence here of hierarchical reparenting. |
| B4 | 6.2C.2.3 **Procedures for Maintaining Federated Learning Processes** | All three: NF status and client reports, joining/leaving, reselection and termination. Replacement of a client is a reusable primitive, not a complete intermediate-subtree recovery procedure. |
| B5 | 6.2F.1 **ML Model Training Subscribe/Unsubscribe**; 6.2F.2 **Contents of ML Model Training**; 6.2F.3 **ML Model Training Information Request** | All three: preparation versus execution, model information, ML Correlation ID, subscription/notification correlation, training requirements and delay information. These clauses do not establish the proposed hierarchy-wide binding. |
| B6 | 7.10.1 **General**; 7.10.2 **Nnwdaf_MLModelTraining_Subscribe service operation**; 7.10.3 **Nnwdaf_MLModelTraining_Unsubscribe service operation**; 7.10.4 **Nnwdaf_MLModelTraining_Notify service operation**; 7.11.1 **General**; 7.11.2 **Nnwdaf_MLModelTrainingInfo_Request service operation** | All three: abstract service contracts and success/failure outputs. Clauses 2–3 of this draft use the subscription/notification path; no equivalent request/response extension is specified here. |
| B7 | 5.4 **Vertical Federated Learning (VFL)**; 5.2 **NWDAF Discovery and Selection**; 6.2H.2.1.2 **Registration and Discovery procedure for Vertical Federated Learning when untrusted AF is acting as the VFL server** | R19/R20: VFL and VFL client aggregation, including NEF selection of a client to aggregate other clients' intermediate results (step 8 and NOTE 5). This is a separate capability and is not used as the horizontal FL baseline. |

The core FL clause placement is stable across the compared snapshots. R19/R20
make “Horizontal” explicit in the titles of 5.3 and 6.2C; they do not relocate
the discovery, training or maintenance procedures. R18 and R19 have matching
core procedure text in 6.2C.2.1–6.2C.2.3 after conversion-format normalization.
R20 adds the single desired-metric propagation clarification in 6.2C.2.2 NOTE 1
and explicitly lists Desired ML Model Metric in 6.2F.2. Those R20 additions must
not be attributed to R18's information list. R19/R20 also qualify the scope
notes in 7.10.1 and 7.11.1 with “only for Federated Learning”; the MTLF-to-MTLF
use adopted here is supported in all three.

The later VFL capability [B7] prevents a blanket claim that 3GPP lacks client
aggregation or multi-NWDAF composition. The narrower inference from the
inspected horizontal FL clauses is that they provide reusable FL mechanisms
without specifying the topology-instruction, recursive realization reporting
and intermediate reparenting procedure proposed here. This is not a claim
about all mechanisms in all 3GPP specifications.

### Project design sources

Project scope follows
the current Human-provided Scope / Contribution Freeze.
The design inputs below were read at `nwdaf-docs` revision
`021677f0b905555703af9f40279bbb2956a0c04f`; paths are relative to that repository:

- `docs/design/hierarchical-federated-learning/protocol_design.md`, especially
  clauses 4.1–4.7 and 4.9: relative roles, shared correlation, per-edge support,
  instruction/report distinction and lifecycle separation.
- `docs/design/hierarchical-federated-learning/topology_policy_design.md`,
  clauses 2–5: selection authority, direct-child policy, training contract,
  node-local cadence, readiness and relationship-status ownership.
- `docs/design/hierarchical-federated-learning/standard_field_extension_boundary.md`,
  clauses 3–7: design intent to reuse existing information and separate
  hierarchical semantics. Its analysis is not normative evidence for
  this draft.

Project decisions reflected in clauses 1–3 define single-parent acceptance in
the realized tree, recursive repair by an authorized surviving direct parent,
acceptance of new relationships and minimum training continuation. These are
project proposal semantics, not claims of existing 3GPP behavior.

### ML Model Training subscription resource lifecycle

TS 29.520 V18.14.0, V19.7.0 and V20.0.0, clauses 4.6.2.2.2, 4.6.2.3.2,
4.6.2.4.2 and 5.5.6.2.2/5.5.6.2.8, define creation and deletion per subscription
resource. The ML Correlation ID identifies the ML training procedure, while
notification correlation correlates notifications with the corresponding
subscription. Applying those resource semantics to this proposal, a replacement
establishes a new and independent subscription resource. Failure to complete
cleanup or Unsubscribe of the old failed-parent subscription does not by itself
block that establishment. The ML Correlation ID remains procedure-level
correlation, while subscription resource identity and notification correlation
remain associated with the individual subscription.
The inspected baseline does not specify deterministic cleanup of an unreachable
stale old resource.
