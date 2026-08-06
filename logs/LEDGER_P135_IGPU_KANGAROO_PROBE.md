# P135 GPU kangaroo probe (Intel HD 530 / Vulkan)

**Status:** **EVALUATED — does not beat CPU.** 0 verified bits. Launch still **NO**.

## Clarification

Running `clBitCrack` (address HASH160) does **not** enable JeanLuc GPU kangaroo.
JeanLuc GPU requires **CUDA** (`-DWITHGPU`); this host has no NVIDIA.

What we ran instead: **oritwoen/kangaroo** (wgpu / Vulkan) against the **P135 compressed pubkey** — the correct ECDLP path.

## Hardware

| Item | Value |
|------|-------|
| Device | Intel HD Graphics 530 |
| Backend | Vulkan (wgpu) |
| Binary | `kangaroo_wgpu/target/release/kangaroo.exe` |
| JeanLuc | CPU-only build (`GPU code not compiled`) |

## Known-key check (Puzzle 40 pubkey)

| Engine | Wall | Ops | Approx rate |
|--------|-----:|----:|------------:|
| JeanLuc CPU (`-t 4`) | ≈0.3 s | \(2^{19.77}\) | ~S-02 class |
| wgpu Vulkan iGPU | **111 s** | \(3.09\times10^{7}\) | ≈ \(2.8\times10^{5}\) ops/s |

Key found: `0xe9ae4933d6` (verified). iGPU **~60× slower** than JeanLuc CPU on this host.

## P135 pubkey sample

```text
pubkey  02145d2611c823a396ef6712ce0f712f09b9b4f3135e3e0aa3230fb9b6d08d1e16
start   2^134
range   134 bits
```

Stopped at `--max-ops 5000000` (expected: no hit). Sustained iGPU rate remains ~\(3\times10^{5}\) ops/s after init.

Vs S-02 CPU baseline \(R\approx1.70\times10^{7}\) ops/s:

\[
T_{135}^{\mathrm{(iGPU)}} \gg T_{135}^{\mathrm{(CPU)}}
\]

already \(10^{5}\)–\(10^{6}\) CPU-years at JeanLuc rates — iGPU makes it worse, not better.

## Conclusion

\[
\boxed{\text{P135 kangaroo on Intel iGPU does not beat JeanLuc CPU; CUDA GPU still required to change the denominator.}}
\]

Artifacts: `logs/s02_native/wgpu_p40/`, `logs/s02_native/wgpu_p135/`.
