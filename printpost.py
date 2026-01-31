"""
Thermal Printer Utility - USB & Serial Printer Interface
A simple Python script for printing receipts via USB thermal printers and serial port printers.
Author: Your Name
License: MIT
"""

# Standard library imports
import json
from pathlib import Path
from io import BytesIO
from typing import List, Optional, Dict, Any

# Third-party imports
try:
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

class PrinterConfig:
    """Configuration for printer settings"""
    DEFAULT_CONFIG_DIR = Path(__file__).parent
    DEVICE_CONFIG_FILE = DEFAULT_CONFIG_DIR / "printer.json"
    TYPE_CONFIG_FILE = DEFAULT_CONFIG_DIR / "type_printer.json"
    
    # Printer commands (ESC/POS)
    COMMANDS = {
        'bold_on': b'\x1B\x45\x01',
        'bold_off': b'\x1B\x45\x00',
        'large_on': b'\x1B\x21\x10',
        'large_off': b'\x1B\x21\x00',
        'buzzer': b'\x1B\x42\x05\x07',
        'cut': b'\x1D\x56\x00',
        'line_feed': b'\x0A',
        'holder_line': '-' * 44,
        'holder_asterisk': '*' * 44,
    }

# ============================================================================
# PRINTER MANAGEMENT
# ============================================================================

class PrinterManager:
    """Manages printer discovery, selection, and configuration"""
    
    @staticmethod
    def get_usb_devices() -> List[Dict[str, Any]]:
        """Get list of connected USB devices"""
        if not USB_AVAILABLE:
            print("pyusb not installed. Install with: pip install pyusb")
            return []
        
        devices = []
        try:
            usb_devices = list(usb.core.find(find_all=True))
            for i, dev in enumerate(usb_devices):
                devices.append({
                    'index': i + 1,
                    'bus': dev.bus,
                    'address': dev.address,
                    'manufacturer': getattr(dev, 'manufacturer', 'Unknown'),
                    'product': getattr(dev, 'product', 'Unknown'),
                    'description': f"{i + 1}. {dev.bus:03d}-{dev.address:03d}: "
                                 f"{getattr(dev, 'manufacturer', 'Unknown')} "
                                 f"{getattr(dev, 'product', 'Unknown')}"
                })
        except Exception as e:
            print(f"Error detecting USB devices: {e}")
        return devices
    
    @staticmethod
    def get_serial_ports() -> List[str]:
        """Get list of available serial ports"""
        if not SERIAL_AVAILABLE:
            print("pyserial not installed. Install with: pip install pyserial")
            return []
        
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except Exception as e:
            print(f"Error detecting serial ports: {e}")
            return []
    
    @staticmethod
    def save_printer_config(printer_config: Any, 
                          filename: Path = PrinterConfig.DEVICE_CONFIG_FILE):
        """Save printer configuration to file"""
        try:
            with open(filename, "w") as file:
                json.dump({"printer": printer_config}, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving printer config: {e}")
            return False
    
    @staticmethod
    def save_printer_type(printer_type: str = 'usb',
                         filename: Path = PrinterConfig.TYPE_CONFIG_FILE):
        """Save printer type to file"""
        try:
            with open(filename, "w") as file:
                json.dump({"type_printer": printer_type}, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving printer type: {e}")
            return False
    
    @staticmethod
    def load_printer_config(filename: Path = PrinterConfig.DEVICE_CONFIG_FILE):
        """Load printer configuration from file"""
        try:
            with open(filename, "r") as file:
                data = json.load(file)
                return data.get("printer")
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading printer config: {e}")
            return None
    
    @staticmethod
    def load_printer_type(filename: Path = PrinterConfig.TYPE_CONFIG_FILE):
        """Load printer type from file"""
        try:
            with open(filename, "r") as file:
                data = json.load(file)
                return data.get("type_printer", "usb")
        except FileNotFoundError:
            return "usb"
        except Exception as e:
            print(f"Error loading printer type: {e}")
            return "usb"

# ============================================================================
# PRINTING UTILITIES
# ============================================================================

class PrintFormatter:
    """Format text with printer commands"""
    
    @staticmethod
    def bold(text: str) -> str:
        """Wrap text in bold commands"""
        return f'{PrinterConfig.COMMANDS["bold_on"].decode()}{text}' \
               f'{PrinterConfig.COMMANDS["bold_off"].decode()}'
    
    @staticmethod
    def large(text: str) -> str:
        """Wrap text in large font commands"""
        return f'{PrinterConfig.COMMANDS["large_on"].decode()}{text}' \
               f'{PrinterConfig.COMMANDS["large_off"].decode()}'
    
    @staticmethod
    def center(text: str, width: int = 45) -> str:
        """Center text within given width"""
        return text.center(width)
    
    @staticmethod
    def left_align(text: str, width: int = 45) -> str:
        """Left align text within given width"""
        return text.ljust(width)
    
    @staticmethod
    def right_align(text: str, width: int = 45) -> str:
        """Right align text within given width"""
        return text.rjust(width)
    
    @staticmethod
    def holder_line(char: str = '-', length: int = 44) -> str:
        """Create a holder line"""
        return char * length
    
    @staticmethod
    def format_receipt_item(name: str, qty: int, price: float, 
                          name_width: int = 15, qty_width: int = 4, 
                          price_width: int = 7, total_width: int = 10) -> str:
        """Format a receipt item line"""
        extended_price = qty * price
        return f"{name.ljust(name_width)}" \
               f"{str(qty).ljust(qty_width)}" \
               f"{str(price).ljust(price_width)}" \
               f"{str(extended_price).rjust(total_width)}"

class Printer:
    """Main printer class for printing operations"""
    
    def __init__(self):
        self.config = PrinterConfig()
        self.manager = PrinterManager()
        self.formatter = PrintFormatter()
    
    def print_test_receipt(self):
        """Print a test receipt"""
        printer_config = self.manager.load_printer_config()
        printer_type = self.manager.load_printer_type()
        
        if not printer_config:
            print("No printer configured. Please select a printer first.")
            if TKINTER_AVAILABLE:
                messagebox.showwarning("No Printer", "No printer configured.")
            return False
        
        # Create test receipt
        receipt_lines = [
            self.formatter.holder_line().center(45),
            self.formatter.bold('Your Company Name').center(45),
            "123 Main St, City".center(45),
            "Phone: 123-456-7890".center(45),
            self.formatter.bold('Date: 2023-12-31').center(45),
            self.formatter.holder_line().center(45),
            "Item          Qty  Price     Ext Price".center(45),
            self.formatter.holder_line().center(45),
        ]
        
        # Add items
        test_items = [
            {"name": "Item 1", "qty": 2, "price": 10.00},
            {"name": "Item 2", "qty": 1, "price": 20.00},
            {"name": "Item 3", "qty": 3, "price": 5.00},
        ]
        
        for item in test_items:
            line = self.formatter.format_receipt_item(
                item['name'], item['qty'], item['price']
            )
            receipt_lines.append(line.center(45))
        
        # Add total
        total = sum(item['qty'] * item['price'] for item in test_items)
        receipt_lines.extend([
            self.formatter.holder_line().center(45),
            (f"Total".ljust(10) + f"{total}".rjust(8)).center(45),
            self.formatter.holder_line().center(45),
            "Thank you for your business!".center(45),
            self.formatter.holder_line().center(45),
        ])
        
        try:
            return self.print_receipt(receipt_lines, is_buzzer=True)
        except Exception as e:
            error_msg = f"Error printing: {e}"
            print(error_msg)
            if TKINTER_AVAILABLE:
                messagebox.showerror("Print Error", error_msg)
            return False
    
    def print_receipt(self, receipt_lines: List[str], 
                     logo_url: Optional[str] = None, 
                     is_buzzer: bool = True) -> bool:
        """Print receipt lines"""
        printer_config = self.manager.load_printer_config()
        printer_type = self.manager.load_printer_type()
        
        if not printer_config:
            print("No printer configured")
            return False
        
        try:
            if printer_type == 'serial':
                return self._print_to_serial(
                    printer_config, receipt_lines, logo_url, is_buzzer
                )
            else:
                return self._print_to_usb(
                    printer_config, receipt_lines, logo_url, is_buzzer
                )
        except Exception as e:
            print(f"Printing failed: {e}")
            return False
    
    def _print_to_usb(self, device_info, text_lines: List[str], 
                     logo_url: Optional[str], is_buzzer: bool) -> bool:
        """Print to USB device"""
        if not USB_AVAILABLE:
            print("USB printing requires pyusb")
            return False
        
        try:
            # Convert description back to device if needed
            if isinstance(device_info, str) and device_info.startswith(tuple('123456789')):
                devices = self.manager.get_usb_devices()
                for dev_info in devices:
                    if device_info == dev_info['description']:
                        # We need the actual device object
                        usb_devices = list(usb.core.find(find_all=True))
                        device = usb_devices[dev_info['index'] - 1]
                        break
                else:
                    device = None
            else:
                device = device_info
            
            if not device:
                print("USB device not found")
                return False
            
            device.set_configuration()
            cfg = device.get_active_configuration()
            intf = cfg[(0, 0)]
            
            out_endpoint = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) 
                == usb.util.ENDPOINT_OUT
            )
            
            if out_endpoint is None:
                print("OUT endpoint not found")
                return False
            
            # Print logo if provided
            if logo_url:
                self._print_image_from_url(logo_url, out_endpoint)
            
            # Print text lines
            for line in text_lines:
                out_endpoint.write(f"{line}\n".encode('utf-8'))
            
            # Add margin
            for _ in range(5):
                out_endpoint.write(self.config.COMMANDS['line_feed'])
            
            # Cut paper
            out_endpoint.write(self.config.COMMANDS['cut'])
            out_endpoint.write(self.config.COMMANDS['line_feed'])
            
            # Buzzer if enabled
            if is_buzzer:
                out_endpoint.write(self.config.COMMANDS['buzzer'])
            
            usb.util.dispose_resources(device)
            return True
            
        except Exception as e:
            print(f"USB printing error: {e}")
            return False
    
    def _print_to_serial(self, port: str, text_lines: List[str], 
                        logo_url: Optional[str], is_buzzer: bool) -> bool:
        """Print to serial port"""
        if not SERIAL_AVAILABLE:
            print("Serial printing requires pyserial")
            return False
        
        try:
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            
            # Print logo if provided
            if logo_url:
                self._print_image_from_url(logo_url, ser)
            
            # Print text lines
            for line in text_lines:
                ser.write(f"{line}\n".encode('utf-8'))
            
            # Add margin
            for _ in range(5):
                ser.write(self.config.COMMANDS['line_feed'])
            
            # Cut paper
            ser.write(self.config.COMMANDS['cut'])
            ser.write(self.config.COMMANDS['line_feed'])
            
            # Buzzer if enabled
            if is_buzzer:
                ser.write(self.config.COMMANDS['buzzer'])
            
            ser.close()
            return True
            
        except Exception as e:
            print(f"Serial printing error: {e}")
            return False
    
    def _print_image_from_url(self, image_url: str, output_device) -> bool:
        """Print image from URL"""
        if not REQUESTS_AVAILABLE:
            print("Image printing requires requests")
            return False
        if not PILLOW_AVAILABLE:
            print("Image printing requires Pillow")
            return False
        
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                image = Image.open(image_data)
                # Add your image processing and printing logic here
                print(f"Image loaded: {image.size}")
                return True
            else:
                print(f"Failed to download image: {response.status_code}")
                return False
        except Exception as e:
            print(f"Image printing error: {e}")
            return False

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def cli_interface():
    """Command line interface for printer management"""
    printer = Printer()
    manager = PrinterManager()
    formatter = PrintFormatter()
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Thermal Printer Utility - Manage and print receipts"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List devices
    list_parser = subparsers.add_parser('list', help='List available devices')
    list_parser.add_argument('--type', choices=['usb', 'serial', 'all'], 
                           default='all', help='Type of devices to list')
    
    # Configure printer
    config_parser = subparsers.add_parser('config', help='Configure printer')
    config_parser.add_argument('--type', choices=['usb', 'serial'], 
                             required=True, help='Printer type')
    config_parser.add_argument('--device', help='Device identifier')
    
    # Test print
    test_parser = subparsers.add_parser('test', help='Print test receipt')
    
    # Print custom receipt
    print_parser = subparsers.add_parser('print', help='Print custom text')
    print_parser.add_argument('text', nargs='+', help='Text to print')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        if args.type in ['usb', 'all']:
            print("USB Devices:")
            devices = manager.get_usb_devices()
            for dev in devices:
                print(f"  {dev['description']}")
        
        if args.type in ['serial', 'all']:
            print("\nSerial Ports:")
            ports = manager.get_serial_ports()
            for port in ports:
                print(f"  {port}")
    
    elif args.command == 'config':
        if args.type == 'usb':
            devices = manager.get_usb_devices()
            if not devices:
                print("No USB devices found")
                return
            
            print("Available USB devices:")
            for dev in devices:
                print(f"  {dev['description']}")
            
            if args.device:
                try:
                    index = int(args.device.split('.')[0]) - 1
                    if 0 <= index < len(devices):
                        selected = devices[index]['description']
                        manager.save_printer_config(selected)
                        manager.save_printer_type('usb')
                        print(f"Configured: {selected}")
                    else:
                        print("Invalid device index")
                except:
                    print("Invalid device format. Use format like '1. ...'")
            else:
                print("\nSpecify device with --device '1. ...'")
        
        elif args.type == 'serial':
            ports = manager.get_serial_ports()
            if not ports:
                print("No serial ports found")
                return
            
            print("Available serial ports:")
            for i, port in enumerate(ports, 1):
                print(f"  {i}. {port}")
            
            if args.device:
                if args.device in ports:
                    manager.save_printer_config(args.device)
                    manager.save_printer_type('serial')
                    print(f"Configured: {args.device}")
                else:
                    print("Invalid port. Available ports:")
                    for port in ports:
                        print(f"  {port}")
            else:
                print("\nSpecify port with --device COM3 (or /dev/ttyUSB0)")
    
    elif args.command == 'test':
        print("Printing test receipt...")
        success = printer.print_test_receipt()
        if success:
            print("Test receipt printed successfully")
        else:
            print("Failed to print test receipt")
    
    elif args.command == 'print':
        text = ' '.join(args.text)
        success = printer.print_receipt([text])
        if success:
            print("Text printed successfully")
        else:
            print("Failed to print text")
    
    else:
        parser.print_help()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example usage
    printer = Printer()
    
    # Quick test if no command line arguments
    import sys
    if len(sys.argv) == 1:
        # Show available devices
        manager = PrinterManager()
        
        print("Thermal Printer Utility")
        print("=" * 50)
        
        # Check USB devices
        usb_devices = manager.get_usb_devices()
        if usb_devices:
            print(f"Found {len(usb_devices)} USB device(s):")
            for dev in usb_devices:
                print(f"  {dev['description']}")
        else:
            print("No USB devices found")
        
        # Check serial ports
        serial_ports = manager.get_serial_ports()
        if serial_ports:
            print(f"\nFound {len(serial_ports)} serial port(s):")
            for port in serial_ports:
                print(f"  {port}")
        else:
            print("\nNo serial ports found")
        
        # Load current config
        current_config = manager.load_printer_config()
        current_type = manager.load_printer_type()
        
        if current_config:
            print(f"\nCurrent printer: {current_config} ({current_type})")
        else:
            print("\nNo printer configured. Use command line to configure:")
            print("  python printer_utility.py config --type usb --device '1. ...'")
            print("  python printer_utility.py config --type serial --device COM3")
        
        print("\nCommands:")
        print("  python printer_utility.py list --type all")
        print("  python printer_utility.py test")
        print("  python printer_utility.py print 'Hello World'")
    else:
        cli_interface()