# Thermal Printer Utility

A simple Python script for printing receipts via USB thermal printers and serial port printers.

## Features

- Support for USB thermal printers (ESC/POS)
- Support for serial port printers
- Automatic device detection
- Configuration persistence
- Test receipt printing
- Command line interface
- Optional buzzer control
- Image printing from URL

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/thermal-printer-utility.git
cd thermal-printer-utility

# Install dependencies (choose based on your needs)
pip install pyusb        # For USB printers
pip install pyserial     # For serial printers
pip install Pillow       # For image printing
pip install requests     # For downloading images
```

## Quick Start

1. List available devices:
```bash
python printer_utility.py list --type all
```

2. Configure your printer:
```bash
# For USB printer
python printer_utility.py config --type usb --device "1. 001-001: Manufacturer Printer"

# For serial printer
python printer_utility.py config --type serial --device COM3
```

3. Print a test receipt:
```bash
python printer_utility.py test
```

## Usage Examples

```python
from printer_utility import Printer, PrintFormatter

# Initialize
printer = Printer()
formatter = PrintFormatter()

# Create receipt
receipt = [
    formatter.bold("MY STORE").center(45),
    "123 Main Street".center(45),
    formatter.holder_line().center(45),
    "Thank you!".center(45)
]

# Print
printer.print_receipt(receipt)
```

## Configuration

Printer settings are saved in `printer.json` and `type_printer.json` in the script directory.

## License

MIT
```

This makes it easy for others to:
1. Understand what the script does
2. Install required dependencies
3. Configure their printer
4. Use it in their own projects
5. Extend and customize as needed
