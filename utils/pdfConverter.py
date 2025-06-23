from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph,Image,Table, SimpleDocTemplate
from reportlab.platypus.tables import TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.legends import LineLegend
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.charts.axes import XValueAxis, YValueAxis, AdjYValueAxis, NormalDateXValueAxis

from django.conf import settings
from django.utils.translation import gettext as _


class PrintedBill(object):
    def __init__(self,billData,commerceData):
        self.buffer = BytesIO()
        self.billData=billData
        self.commerceData=commerceData

        self.fontName = "Helvetica-Bold"
        #Canvas nos permite hacer el reporte con coordenadas X y Y
        topMargin = 20*mm
        leftMargin = 20*mm
        rightMargin = 20*mm
        bottomMargin = 10*mm
        self.pdf = canvas.Canvas(self.buffer,pagesize=A4,
                                 topMargin=topMargin,
                                leftMargin=leftMargin,
                                rightMargin=rightMargin,
                                bottomMargin=bottomMargin)
        width, height = A4
        

        self.maxY = (height/mm-topMargin/mm)*mm
        self.minY = bottomMargin
        self.maxX = (width/mm-rightMargin/mm)*mm
        self.minX = leftMargin
        self.dy = 5*mm
        self.currentY = self.maxY

        self.createBill()

        self.pdf.showPage()
        self.pdf.save()
        self.pdf = self.buffer.getvalue()
        self.buffer.close()
    
    def nextRow(self,number=1):
        self.currentY -= number*self.dy
        if self.currentY < self.minY:
            self.nextPage()
    
    def nextPage(self):
        self.pdf.showPage()
        self.footer()
        self.header()
        self.currentY = self.maxY
        self.nextRow(5)

    def footer(self,):
        self.currentY = self.minY
        self.nextRow(-5*0.75)
        # Escribimos los datos del comercio
        fontSize=10
        self.pdf.setFont(self.fontName, fontSize)
        text = self.commerceData['name']
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)
        self.nextRow(0.75)
        text = self.commerceData['address1']
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)
        self.nextRow(0.75)
        if self.commerceData['address2']:
            text = self.commerceData['address2'] if self.commerceData['address2'] else '' 
            string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
            self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)
            self.nextRow(0.75)
            text = 'CIF: ' + self.commerceData['cif'] 
            string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
            self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)
        else:
            text = 'CIF: ' + self.commerceData['cif'] 
            string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
            self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)
        self.nextRow(0.75)
        text = 'Tel.: ' + self.commerceData['phone'] if self.commerceData['phone'] else 'Tel.: '
        text += " - " + self.commerceData['web'] if self.commerceData['web'] else ''
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.minX+0.5*(self.maxX-string_width-self.minX), self.currentY, text)

    def header(self,):
        self.currentY = self.maxY+10*mm
        
        #Utilizamos el archivo logo_django.png que está guardado en la carpeta media/imagenes
        try:
            archivo_imagen = settings.STATIC_ROOT+'\site\logos\CompanyLogoNavbar.jpg'
        except:
            archivo_imagen = 'C:/Users/mikel.zabaleta/Github/TPV/static/site/logos/CompanyLogoNavbar.jpg'

        
        #Establecemos el tamaño de letra en 16 y el tipo de letra Helvetica
        self.currentY = self.maxY+10*mm
        self.nextRow(1.5)
        self.pdf.setFont(self.fontName, 14)

        text = self.billData['code']
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=14)
        self.pdf.drawString(self.maxX-string_width, self.currentY, text)
        self.pdf.drawImage(archivo_imagen, self.minX, self.currentY-35, 110,preserveAspectRatio=True)
        self.currentY = self.maxY
        self.pdf.line(x1=self.minX,y1 = self.currentY,x2=self.maxX, y2 = self.currentY)
        self.nextRow(2)

    def createBill(self,):
        rowsPerPage = 25

        #Dibujamos una cadena en la ubicación X,Y especificada
        self.footer()
        self.header()

        self.nextRow(0.5) 
        # Escribimos los datos del cliente
        fontSize=10
        self.pdf.setFont(self.fontName, fontSize)
        text = _("Date: ") + self.billData['date'].strftime("%d/%m/%Y, %H:%M:%S")
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.minX, self.currentY, text)
        self.nextRow(1)
        if self.billData['customer']:
            text = _("Customer name: ") + self.billData['customer']['name'] + " " +self.billData['customer']['surname']
            string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
            self.pdf.drawString(self.minX, self.currentY, text)
            self.nextRow(1)
            text = _("Customer Tax number: ") + self.billData['customer']['cif']
            string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
            self.pdf.drawString(self.minX, self.currentY, text)
            self.nextRow(5)       
        
        fontSize=18
        self.pdf.setFont(self.fontName, fontSize)

        text = _("Bill summary")
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.minX+(self.maxX-self.minX-string_width)/2, self.currentY, text)
        
        self.nextRow(2)

        tableRows = [(row['quantity'],row['product'],str(round(row['subtotal']/row['quantity'],2))+'€',str(row['subtotal'])+'€') for row in self.billData['positions']]
        

        if len(self.billData['positions'])<=rowsPerPage:
            self.__table__(y=None,header=[_('Quant.'),_('Product'), _('Unit price'), _('Subtotal')],
                                    rows=tableRows)
        else:
            for i in range(0,len(self.billData['positions']),rowsPerPage):
                self.__table__(y=None,header=[_('Quant.'),_('Product'),_('Unit price'), _('Subtotal')],
                                    rows=tableRows[i:i+rowsPerPage])
                if i+rowsPerPage < len(self.billData['positions']):
                    self.nextPage()

        # Escribimos el resumen de la factura
        self.nextRow(1.5)
        fontSize=10
        self.pdf.setFont(self.fontName, fontSize)
        vat_amount=0
        for row in self.billData['positions']:
            vat_amount += row['vat_amount']
        text = _("VAT") +": ........................" + str(round(vat_amount,2))+"€"
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.maxX-string_width, self.currentY, text)
        self.nextRow(2)
        fontSize=12
        self.pdf.setFont(self.fontName, fontSize)
        text = _("TOTAL")+": ......................." + str(round(self.billData['total'],2))+"€"
        string_width = self.pdf.stringWidth(text=text, fontName=self.fontName, fontSize=fontSize)
        self.pdf.drawString(self.maxX-string_width, self.currentY, text)



    def __table__(self,header,rows,y=None):
        #Creamos una tupla de encabezados para neustra tabla
        encabezados = (col for col in header)
        #Establecemos el tamaño de cada una de las columnas de la tabla
        table = Table([encabezados] + rows, colWidths=  [(self.maxX-self.minX)*0.1]+ # column 1
                                                        [(self.maxX-self.minX)*0.5]+ # column 2
                                                        [0.4*(self.maxX-self.minX)/(len(header)-2) for _ in header[2:]])
        #Aplicamos estilos a las celdas de la tabla
        cellStyles = []
        # for i,row in enumerate(rows):
        #     if row[-1] == 'OK':
        #         cellStyles.append(('BACKGROUND',(-1,i+1),(-1,i+1),colors.green))
        #     else:
        #         cellStyles.append(('BACKGROUND',(-1,i+1),(-1,i+1),colors.red))


        table.setStyle(TableStyle(
            [
                ('BACKGROUND',(0,0),(len(header),0),colors.HexColor("#898A88")),
                ('FONT',(0,0),(len(header),0),self.fontName),
                #El tamaño de las letras de cada una de las celdas del encabezado sera 11
                ('FONTSIZE', (0, 0), (len(header),0), 11),

                # All cells aligned center
                ('ALIGN',(0,0),(0,-1),'CENTER'), # first column centered
                ('ALIGN',(1,0),(1,-1),'LEFT'), # second column left
                ('ALIGN',(2,0),(-1,-1),'CENTER'), # rest centered
                #Los bordes de todas las celdas serán de color negro y con un grosor de 1
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black), 
                
                #El tamaño de las letras de cada una de las celdas con datos será de 10
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ] + cellStyles
        ))
        #Establecemos el tamaño de la hoja que ocupará la tabla 
        table.wrapOn(self.pdf, 800, 600)
        w, h = table.wrap(0, 0)
        #Definimos la coordenada donde se dibujará la tabla
        if y:
            table.drawOn(self.pdf, 60,y)
            self.currentY = y
        else:
            # if self.currentY-h < self.minY:
            #     self.nextPage()
            table.drawOn(self.pdf, 60, self.currentY-h)
            self.currentY -=h
        pass


    

if __name__ == '__main__':
    import datetime
    report = PrintedBill(billData={'code':'23-2025',
                                   'customer':{'name':'Mikel','surname':"Zabaleta",'cif':"777789997"},
                                   'date':datetime.datetime.now(),
                                   'total':56.23,
                                   'vat':12.03,
                                   'positions':[
                                       {'quantity':2,'product':"Product "+str(i),'vat_amount':21,'subtotal':100,'reduce_concept':'none'} for i in range(26) 
                                   ]
                                   },
                        commerceData={'name':"Pattas S.L.",
                                      'address1':"Avda Gipuzkoa 4",
                                      'address2':'31187 Tolosa',
                                      'cif':"97245623",
                                      'phone':"944525656",
                                      'web':'www.pattas.es'},
                        )
    with open("kk.pdf", "wb") as binary_file:
        binary_file.write(report.pdf)