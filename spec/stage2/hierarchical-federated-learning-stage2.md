# Hierarchical NWDAF Federated Learning — Stage 2 Draft

Status: Project proposal for review; not a 3GPP specification.

Clauses 1–3 contain proposed text. Their numbering is local to this draft.
References [B1]–[B7] identify existing specification evidence in the informative
notes below. Hierarchical composition, topology instructions, topology reporting
and recovery behavior are proposed additions, including where they reuse an
existing service. The informative notes identify a deferred Stage 3 normative
review item.

## 1. Hierarchical Federated Learning — Functional Description

Hierarchical federated learning enables NWDAFs containing MTLF to compose the
FL Server and FL Client functions described in TS 23.288 clause 5.3 into a
hierarchy. It applies to the horizontal federated learning described in that
clause. It introduces no new NWDAF NF type. Existing NWDAF logical functions,
FL capabilities and discovery principles provide the baseline [B1, B2].

An NWDAF's role is relative to a parent-child relationship in the current
hierarchical FL procedure. An intermediate NWDAF acts as an FL Client towards
its parent and as an FL Server towards its direct children. It receives model
training instructions from its parent, coordinates training and aggregation
with its direct children, and reports the resulting model information to its
parent. The NWDAF at the top of the hierarchy is referred to as the root NWDAF.
An NWDAF with no direct children performs the assigned local training.

The composition may be repeated at successive intermediate NWDAFs. The number
of levels is not fixed. The capability to support both FL roles does not, by
itself, establish a parent-child relationship or confirm participation [B2].

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
configuration or a model request from a consumer [B1]. The decision to form a
hierarchy and the instructions below are additions to that baseline.

The participating entities are the root NWDAF, intermediate NWDAFs, their
candidate direct children and the NRF used for discovery. Every FL participant
contains MTLF. Each parent establishes and manages its own direct-child Model
Training subscriptions using the subscription and notification lifecycle [B5,
B6]. The NRF supplies candidate capability and discovery information; this
proposal assigns no topology storage or orchestration responsibility to the NRF.

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
   candidates outside the supplied list must be explicit; its omission does not
   grant that permission. Other unspecified decisions may follow local
   configuration within the authority granted by the parent. Policy does not
   automatically apply to all descendants.

2. The NWDAF acting as parent, initially the root NWDAF, discovers or resolves
   its candidate direct children using the principles in TS 23.288 clauses 5.2
   and 6.2C.2.1 [B2]. For a candidate that is
   expected to be an intermediate NWDAF, selection considers its ability to
   perform both FL roles. Analytics ID, model interoperability, data availability,
   time availability and applicable serving-area information retain their
   existing meanings [B2, B5]. Candidate preference does not override eligibility.

3. The parent sends an Nnwdaf_MLModelTraining_Subscribe request to each candidate
   selected for preparation. The request carries the existing training
   requirements and ML Preparation Flag [B2, B5], together with the proposed
   topology instruction relevant to that recipient. Any nested instruction is
   addressed to the corresponding descendant, rather than treating the entire
   instruction as a command for every recipient.

   The same ML Correlation ID is used throughout this hierarchical FL procedure.
   Each direct subscription retains its own subscription and notification
   correlation information. Hierarchy-wide use of the ML Correlation ID is a
   project-defined binding; the existing information element identifies an FL
   procedure [B5, B6]. It does not replace peer identification or authorize a
   relationship.

4. The candidate checks the training requirements and decides whether to
   participate, following the preparation behavior in clause 6.2C.2.1 [B2]. It
   also determines whether it can fulfil the hierarchical instruction. If it
   cannot, it reports the unsuccessful outcome and reason to its parent. A
   relationship is not counted as established until support for the required
   hierarchical behavior and participation have been confirmed at that edge.
   Confirmation on an upstream edge does not confirm downstream support.

   Preparation does not start model training [B5]. Establishing downstream
   relationships during hierarchical preparation is a proposed extension to
   preparation, not a reinterpretation of the ML Preparation Flag as a training
   trigger. A successful subscription response alone does not confirm completion
   of a descendant subtree.

5. If the candidate is instructed to establish direct-child relationships, it
   acts as their parent and repeats steps 2–4 for those children. It may add
   candidates discovered through the NRF only within the granted selection
   authority. Resolving the identity or checking the capability of a supplied
   candidate does not require permission to add candidates. Each further
   intermediate NWDAF repeats this procedure for its own children.

   Training and aggregation instructions, when supplied, describe the contract
   to be fulfilled by the participating NWDAFs; they are distinct from
   participant-management policy. The intermediate NWDAF conveys the applicable
   training contract downstream. An explicitly assigned contract is not silently
   replaced by a local choice.

   A parent may also specify how much local work a child performs before
   reporting a model update, for example local training epochs or, for an
   intermediate NWDAF, direct-child training rounds. If unspecified, that child
   may determine the cadence locally. This instruction is local to the addressed
   child and is not automatically inherited by its descendants. It does not
   replace the maximum response time [B3, B5].

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
   intermediate NWDAF does not assign the status of its own upstream
   relationship; that status is maintained by its parent. The report may include
   locally resolved policy, training contract or reporting cadence where relevant
   to the parent's acceptance decision.

7. Each parent evaluates the confirmed direct children and reported subtree
   against its participant-management policy. Only established subscriptions
   with satisfactory participation outcomes count towards availability. A
   parent may accept a partial or unbalanced topology where its policy permits,
   try further candidates within its authority, or report that the requirements
   cannot be met. Decisions outside the granted authority are referred upstream
   through the outcome report. The upstream parent may revise the instruction
   or terminate establishment of the affected part.

   A candidate or relationship does not count as an established participant
   until required hierarchical behavior and participation have been confirmed.
   Candidate rejection or an unsupported instruction does not count as success.
   A parent may continue candidate establishment after its minimum availability
   requirement is met, and report subsequent changes.

8. Reports are combined successively until the root NWDAF has the confirmed
   relationships and the outstanding or unsuccessful candidate outcomes. This
   is the realized topology known at that point, rather than an assumption that
   the original candidate instruction has been fulfilled. Different intermediate
   NWDAFs may temporarily discover or prepare the same NWDAF as a candidate.
   Duplicate parentage or an ancestor cycle must not be accepted into the
   realized topology. Where independently selected relationships conflict, the
   upstream decision process retains or accepts one relationship and adjusts
   or removes the conflicting relationship before formation is considered
   successfully resolved.

9. When the applicable formation requirements are satisfied, training is
   initiated using the existing Model Training lifecycle [B3, B5, B6]. Topology
   preparation alone does not initiate training. If establishment is abandoned,
   each reachable parent removes the direct subscriptions it no longer needs
   using the unsubscribe lifecycle [B6]; unavailable-peer cleanup is not
   represented as confirmed remote termination.

NOTE: The baseline permits preparation checks to be skipped under the conditions
in TS 23.288 clause 6.2C.2.1 [B2]. Reusing such an eligibility determination does
not by itself supply confirmation of newly established hierarchical
relationships.

## 3. Intermediate NWDAF Failure Recovery

This procedure applies when an intermediate NWDAF becomes unavailable during
training, while the root NWDAF and the NWDAFs needed to coordinate repair remain
available. It addresses replacement, reparenting and subsequent training. It
does not require recovery of the failed intermediate NWDAF's runtime state.

The participants are the surviving parent of the unavailable intermediate NWDAF,
a replacement intermediate NWDAF and the available children of the unavailable
intermediate NWDAF, including any subtrees below those children. The parent uses
its known realized topology from clause 2 to identify affected relationships. Last
reported information is input to repair; it is not proof that descendants remain
available.

The surviving direct parent may coordinate local repair within its granted
participant-management and selection authority. It may select a replacement,
establish the new parent-child relationship, trigger reparenting of the affected
subtree and collect the repaired topology report. If it lacks sufficient
authority, it reports the unmet repair requirement or failure outcome to its
own parent for revised instructions or an upstream decision. This coordination
applies recursively at any depth; recovery need not be initiated by the root
NWDAF. Changed realized topology is reported successively to the root NWDAF.

1. **Failure detection.** The parent monitors its intermediate NWDAF client using
   existing inputs: NRF notifications of NF status changes, a client termination
   request, training status reports and absence of the expected training report
   within the maximum response time [B3, B4]. A delay notification supplies
   information for deciding whether to wait, extend the response time or stop
   waiting; its receipt alone does not prove an intermediate failure [B3].
   Operator policy and available observations determine whether replacement is
   needed. No fixed retry count or new failure-detection service is introduced.

2. The parent identifies the unavailable intermediate NWDAF and its affected
   parent-child relationships. It excludes that NWDAF from participant selection
   for the current repair while the NWDAF is considered unavailable, and records
   the loss of the relationship. If the
   parent is itself an intermediate NWDAF, it reports the affected subtree
   upstream. Existing waiting, skipping and partial-aggregation choices may be
   used for the interrupted local training round where the applicable policy
   permits [B3, B4]. This does not establish that repair has completed.

3. **Replacement.** The parent selects a candidate replacement able to act as
   an FL Client towards it and as an FL Server towards the affected children.
   It considers known alternatives and, where permitted, NRF discovery, using
   the selection and preparation principles in [B2, B4]. Selection accounts for
   the affected training requirements and serving area. A different intermediate
   NWDAF is not assumed to possess the failed NWDAF's subscriptions or training
   state. If no suitable replacement is available, the parent reports the unsuccessful
   repair and may wait, try another candidate, or proceed with a reduced
   topology only as allowed by policy. A reduced topology is not reported as
   successful restoration of the missing relationships.

4. The parent prepares a new direct subscription to the replacement and supplies
   the affected subtree instruction, the same hierarchical FL procedure's ML
   Correlation ID, and the applicable training and participant-management
   instructions. Available children identified in the previous topology are
   candidates to be reattached, not automatically confirmed participants of the
   replacement. Unaffected subtrees are not included for reconstruction.

5. **Reparenting.** The replacement establishes new direct-child Model Training
   subscriptions with the affected children using clause 2. Each new
   subscription provides notification target and correlation information for
   the replacement, reusing the meanings in [B5, B6]. After required preparation,
   hierarchical support and participation confirmation succeed, the new
   relationship may become an accepted edge in the repaired realized topology.
   The child's notifications for that new subscription are directed to the
   replacement. Inability to complete Unsubscribe with the failed old parent
   does not by itself block establishment of the new relationship. The common
   ML Correlation ID does not make this a transfer of the old subscription or
   authorize the new parent. Exact resource lifecycle, coexistence and cleanup
   behavior remains subject to the Stage 3 follow-up below.

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
   of repair covers the accepted relationships; it does not certify recovery of
   lost model updates.

7. **Training continuation.** Once the repaired relationships satisfy the
   applicable requirements, the surviving parent supplies a valid current model
   baseline and subsequent training instructions to the repaired subtree through
   the replacement. The replacement coordinates downstream training and reports
   aggregated model information upstream using the existing training lifecycle
   [B3, B5, B6]. The same ML
   Correlation ID continues to identify the hierarchy, while subscription
   identities and iteration progress remain local to each parent-child process.
   Hierarchy-wide round synchronization is not implied by sharing that ID.

   The hierarchical FL job can thus make new training progress after repair
   without rebuilding unaffected relationships or restarting the whole hierarchy
   from initial formation. Work interrupted or not successfully delivered and
   accepted before failure is not assumed reusable. The procedure does not
   require replay of partially completed work or seamless resume of the failed
   intermediate NWDAF's runtime state, and does not claim exact recovery of its
   failed local round or lossless state transfer. Retained-result reuse remains
   an optional enhancement, not a prerequisite for repair or training
   continuation.

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
[Current Scope / Contribution](https://app.notion.com/p/3d28e6f2848d80fcb66dd013d2270789).
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
  hierarchical semantics. Its Stage 3 findings are not normative evidence for
  this draft.
- `docs/design/hierarchical-federated-learning/branch_replacement_scenario.md`,
  clauses 3–5: observed-failure scenario, new subscriptions to a replacement,
  subtree reporting and expressly deferred recovery details.

The current scope makes intermediate recovery active and retained-result work
optional, taking precedence over older design text that deferred recovery or
centred the example on retained-result retrieval. No implementation-conformance
claim or candidate-schema compatibility conclusion is made here.

Project decisions reflected in clauses 1–3 define single-parent acceptance in
the realized tree, recursive repair by an authorized surviving direct parent,
acceptance of new relationships and minimum training continuation. These are
project proposal semantics, not claims of existing 3GPP behavior.

### Stage 3 follow-up

Verify against TS 29.520 the resource lifecycle, coexistence and cleanup
semantics when a replacement establishes a new Model Training subscription
with an affected child but Unsubscribe cannot be completed with the failed old
parent. In particular, determine how the new subscription and the old resource
are handled without implying subscription transfer through the common ML
Correlation ID. Exact Stage 3 behavior is unverified here; this deferred
normative review item does not leave the proposed Stage 2 acceptance rule open.

Stale-resource cleanup procedures, peer recovery races, exclusive ownership,
fencing and stateful handoff are outside the current Stage 2 scope.
