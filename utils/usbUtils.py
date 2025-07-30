import usb.core
import usb.util
from os.path import join,exists
from escpos.printer import Usb

from django.conf import settings
try:
    settings.STATIC_ROOT
except:
    from box import Box
    settings = Box({"STATIC_ROOT":".."})
'''
On Windows, use zadig to install the proer driver
'''

class ThermalPrinter():
    def __init__(self,idVendor=0x1fc9, idProduct=0x2016,profile="TM-P80"):
        self.printer = Usb(idVendor=idVendor, idProduct=idProduct,timeout=0,profile=profile)

    def printReceipt(self,data):
        if exists(join(settings.STATIC_ROOT,"site","logos","CompanyLogoNavbar.jpg")):
            self.printer.image(join(settings.STATIC_ROOT,"site","logos","CompanyLogoNavbar.jpg"))
        for row in data:
            self.printer.textln(row)
        self.printer.cut()

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
    
    printer = ThermalPrinter()
    printer.printReceipt(data=['Hola mundo',"Esto es muy duro","Pero entre todos lo superaremos sin ninguna duda"])
    # p = Usb(idVendor=0x1fc9, idProduct=0x2016,timeout=0,profile="TM-P80")
    # p.text("Hello World\n")
    # p.image(join("..","static","site","logos","CompanyLogoNavbar.jpg"))
    # p.barcode('4006381333931', 'EAN13', 64, 2, '', '')
    # p.cut()