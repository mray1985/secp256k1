========================================================================================
ALL FOUR FACTORADIC PHASE DEFS  +  STRATIFIED NULLS
========================================================================================
N=70 puzzles 1..70; trials=2000; seed=20260711; thresh=0.1
Lead step locked: term=a*k!; rem=d-term; rebuild sum a_i*i!.

Reconstruction: 70/70 exact

----------------------------------------------------------------------------------------
DEF digit_frac
  observed  r_hi=+0.6097  r_lo=+0.1127  gap=+0.4970
            H_hi=43/70  H_lo=26/70  Hgap=+17
            residualized r_hi=+0.5844
  S1_block5    P(r>=0.610)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.497)=0.0015  (null_mean_r=+0.116)
  S1_block10   P(r>=0.610)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.497)=0.0015  (null_mean_r=+0.118)
  S2_near10    P(r>=0.610)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.497)=0.0015  (null_mean_r=+0.084)
  global       P(r>=0.610)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.497)=0.0015  (null_mean_r=+0.000)
  S3_residual  residual_real=+0.5844  P(r_res>=real)=0.0005  null_mean=-0.002
  STATUS (digit_frac): PAIRING-DEPENDENT
----------------------------------------------------------------------------------------
DEF cell_frac
  observed  r_hi=+0.1185  r_lo=+0.0506  gap=+0.0679
            H_hi=20/70  H_lo=17/70  Hgap=+3
            residualized r_hi=+0.0959
  S1_block5    P(r>=0.119)=0.3063  P(H>=20)=0.0980  P(gap_r>=0.068)=0.3538  (null_mean_r=+0.058)
  S1_block10   P(r>=0.119)=0.2734  P(H>=20)=0.0910  P(gap_r>=0.068)=0.3943  (null_mean_r=+0.043)
  S2_near10    P(r>=0.119)=0.2439  P(H>=20)=0.0545  P(gap_r>=0.068)=0.4388  (null_mean_r=+0.037)
  global       P(r>=0.119)=0.1639  P(H>=20)=0.0390  P(gap_r>=0.068)=0.3588  (null_mean_r=-0.000)
  S3_residual  residual_real=+0.0959  P(r_res>=real)=0.2209  null_mean=+0.002
  STATUS (cell_frac): NULL
----------------------------------------------------------------------------------------
DEF plateau_frac
  observed  r_hi=+0.5452  r_lo=+0.1606  gap=+0.3846
            H_hi=43/70  H_lo=28/70  Hgap=+15
            residualized r_hi=+0.5448
  S1_block5    P(r>=0.545)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.385)=0.0100  (null_mean_r=+0.031)
  S1_block10   P(r>=0.545)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.385)=0.0080  (null_mean_r=+0.014)
  S2_near10    P(r>=0.545)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.385)=0.0055  (null_mean_r=+0.016)
  global       P(r>=0.545)=0.0005  P(H>=43)=0.0005  P(gap_r>=0.385)=0.0105  (null_mean_r=+0.002)
  S3_residual  residual_real=+0.5448  P(r_res>=real)=0.0005  null_mean=-0.000

See LEDGER_HIGH_SLICE_FACTORADIC_PHASE_COUPLING.md for the locked suite.
