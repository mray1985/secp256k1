# Secp256k1 Key Cascade Generator

A deterministic key generator that rotates through the entire secp256k1 keyspace without storing the full rolladex. Computes any position on demand.

## Features

- Generate private keys, WIF, public keys, and Base58 addresses
- Jump to any position (1 to 2^256-1)
- Roll through ranges sequentially
- Search specific ranges (e.g., 2^134 to 2^135-1, N-2^134 to N-2^135-1)
- Supports compressed and uncompressed formats
- Mainnet and testnet support

## Usage

```bash
# Show key at position 1
python cascade.py -p 1

# Jump to position and show details
python cascade.py --position 1000 -o json

# Roll forward 10 positions
python cascade.py -r 10

# Roll forward with limit (safety)
python cascade.py -r 1000 -l 10

# Search a specific range
python cascade.py --range "2^134:2^135-1" -l 1000

# Search high range (near curve order)
python cascade.py --range "N-2^135:N-2^134-1" -l 1000

# Use testnet prefixes
python cascade.py -p 1 --testnet

# Output formats: text (default), json, csv
python cascade.py -p 1 -o csv
```

## Range Syntax

- `2^134` = 2 raised to power 134
- `2^135-1` = (2^135) - 1
- `N-2^134` = Curve order (N) minus 2^134
- `N-2^135-1` = Curve order minus (2^135 - 1)
- Use `:` to separate start and end of range

## Examples for Your Ranges

```bash
# Range: 2^134 to 2^135-1
python cascade.py --range "2^134:2^135-1" -l 100

# Range: N-2^134 to N-2^135-1
python cascade.py --range "N-2^134:N-2^135-1" -l 100

# Range: 2^159 to 2^160-1
python cascade.py --range "2^159:2^160-1" -l 100

# Range: N-2^159 to N-2^160-1
python cascade.py --range "N-2^159:N-2^160-1" -l 100
```

## Python API

```python
from cascade import Secp256k1Cascade

cascade = Secp256k1Cascade()

# Jump to position
cascade.jump(1000)

# Get current key data
key_data = cascade.current()
print(key_data['address_compressed'])

# Roll through range
for key_data in cascade.search_range(2**134, 2**135, limit=1000):
    print(key_data['wif_compressed'], key_data['address_compressed'])

# Next/previous
cascade.next()
cascade.prev()
```

## Output Fields

- `position`: 1-indexed position in keyspace
- `wif_compressed`: Private key in WIF format (compressed)
- `wif_uncompressed`: Private key in WIF format (uncompressed)
- `address_compressed`: Base58 public address (compressed)
- `address_uncompressed`: Base58 public address (uncompressed)

## Files

- `cascade.py` - CLI version for command-line use
- `cascade_gui.py` - Simple GUI with slider jump navigation
- `cascade_scroll_gui.py` - Window-based GUI (10K keys per page)
- `cascade_infinite_scroll.py` - **Infinite scroll GUI** (keys produced in the moment)

## Requirements

- Python 3.7+
- `ecdsa` package: `pip install ecdsa`
- `tkinter` (usually included with Python)

## Quick Start

### For Infinite Scroll (Recommended)
```bash
python cascade_infinite_scroll.py
```

**How it works:**
- **Only visible keys exist** - produced in the moment
- Scroll **UP**: keys above appear, keys below fade away
- Scroll **DOWN**: keys below appear, keys above fade away
- Mouse wheel or drag scrollbar to navigate
- **<< First** / **Last >>** buttons jump to curve beginning/end
- **Jump** to any position (type: 1, 2^134, N-2^159, etc.)
- Preset buttons for your target ranges

### For Window-Based Scrolling
```bash
python cascade_scroll_gui.py
```
- Displays 10,000 keys per window
- Slide bar to jump to position
- Scroll through window
- Adjustable window size

### For Simple Navigation
```bash
python cascade_gui.py
```

### For Command-Line
```bash
python cascade.py --range "2^134:2^135-1" -l 100
```
