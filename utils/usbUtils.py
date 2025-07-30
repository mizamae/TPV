import usb.core
import usb.util

'''
On Windows, install libusb-win32
'''
def list_usb_devices():
    # Find all connected USB devices
    devices = usb.core.find(find_all=True)

    # Iterate over each device and print information
    for device in devices:
        print(f"Device: {device}")
        print(f"  - idVendor: {hex(device.idVendor)}")
        print(f"  - idProduct: {hex(device.idProduct)}")
        print(f"  - Manufacturer: {usb.util.get_string(device, device.iManufacturer)}")
        print(f"  - Product: {usb.util.get_string(device, device.iProduct)}")
        print(f"  - Serial Number: {usb.util.get_string(device, device.iSerialNumber)}")
        print()

if __name__ == "__main__":
    list_usb_devices()