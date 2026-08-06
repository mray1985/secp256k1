# Graph Report - ECDLP  (2026-06-14)

## Corpus Check
- 2 files · ~146,469 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 163 nodes · 379 edges · 9 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]

## God Nodes (most connected - your core abstractions)
1. `run_pipeline()` - 49 edges
2. `PuzzleConfig` - 14 edges
3. `run_bridge_regression()` - 12 edges
4. `Pipeline` - 12 edges
5. `verify_n_y_compression()` - 11 edges
6. `emit_calibration_phase()` - 10 edges
7. `verify_family_bridge()` - 9 edges
8. `pubkey_from_scalar()` - 9 edges
9. `emit_ec_foundations()` - 9 edges
10. `emit_alignment_phase()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `resolve_true_r_xy()` --references--> `PuzzleConfig`  [EXTRACTED]
  ecdlp_full_pipeline.py → ecdlp_full_pipeline.py  _Bridges community 0 → community 2_
- `run_pipeline()` --references--> `PuzzleConfig`  [EXTRACTED]
  ecdlp_full_pipeline.py → ecdlp_full_pipeline.py  _Bridges community 0 → community 1_
- `verify_core_lambda_laws()` --calls--> `curve_y_ratio_mod()`  [EXTRACTED]
  ecdlp_full_pipeline.py → ecdlp_full_pipeline.py  _Bridges community 3 → community 2_
- `run_pipeline()` --calls--> `cube_root_mod_prime()`  [EXTRACTED]
  ecdlp_full_pipeline.py → ecdlp_full_pipeline.py  _Bridges community 3 → community 1_
- `emit_concat_point_phase()` --references--> `ScalarFrame`  [EXTRACTED]
  ecdlp_full_pipeline.py → ecdlp_full_pipeline.py  _Bridges community 7 → community 1_

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (16): apply_puzzle_defaults(), config_from_args(), configure_stdio_utf8(), main(), parse_int(), parse_triple(), prompt_config(), prompt_int() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.28
Nodes (20): DVerifyResult, emit_alignment_phase(), emit_calibration_phase(), emit_compression_architecture(), emit_concat_point_phase(), emit_core_lambda_laws(), emit_ec_foundations(), emit_family_bridge() (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (33): build_concat_point_frame(), compressed_slot_y2(), CompressionCheck, concat_point_xy(), CoreLambdaLaws, deconcat_point_xy(), n_slot_y_compress_constant(), NYCompressionCheck (+25 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (32): add_c_bracket_candidates(), all_cube_roots_mod(), all_cube_roots_mod_p(), band_representative(), build_d_candidates(), carry(), cube_root_mod_prime(), curve_residue_x_cubic_from_y() (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.29
Nodes (10): add_matrix_candidates(), AlignmentFrame, build_alignment_candidates(), build_bridge_offset_terms(), compute_alignment_frame(), Shelf/cube alignment: v0 shelf anchors + optional known offset to d (P115 calibr, Bridge-only offset mod LO terms (no known d). Deduped by residue., d = anchor + offset (mod LO) hypotheses from shelf/OITC — then verify d*G == P. (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (15): carry_quotient(), ColumnCStats, compute_order_in_the_court(), compute_shelf_iteration_matrix(), oitc_notebook_d_cong(), OrderInTheCourt, Exact integer quotient or decimal (lambdaN*qx - Qx) / N display., shelf^3 mod LO — d congruent residue (orderinthecourt.txt corrected dy line). (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.38
Nodes (9): beta_n(), Check, cube_root_mod_n(), is_exact_div(), main(), print_report(), Principal cube root mod N when defined; else (None, reason)., run_checks() (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (9): add_scalar_frame_candidates(), compare_bridge_to_scalar_frame(), compute_scalar_frame(), ConcatPointFrame, Append m = d*k^-1 and m_inv = k*d^-1 when ground truth is known., Anchors P = d*G, R = k*G and the direct bridge P = m*R with m = d*k^-1., 512-bit packed P and R with bridge vs true-R distinction., ScalarFrame (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (7): n_side_compress_constant(), NSideBalance, p_side_compress_carry(), N-side parallel to p-side IP+7=Py^2, with heaven carry from p., Heaven carry a = (y^2 - IP - 7) / p when the p-side x-compress law holds., N analog of +7 on p-side: 7*delta^2 + a_carry*p*delta^2 (mod N)., verify_n_side_balance()

## Knowledge Gaps
- **6 isolated node(s):** `NSideBalance`, `NYCompressionCheck`, `TextIO`, `Namespace`, `ShelfIterationMatrix` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `PuzzleConfig` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `verify_family_bridge()` connect `Community 3` to `Community 1`, `Community 2`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `NSideBalance`, `NYCompressionCheck`, `TextIO` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.12554112554112554 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07196969696969698 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._