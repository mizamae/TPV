<!-- This file is part of Tiny TPV.

Tiny TPV is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Tiny TPV is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Tiny TPV. If not, see <https://www.gnu.org/licenses/>. -->


# Tiny TPV
[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README.es.md)

Tiny TPV es una aplicación completamente funcional que puede ser utilizada en comercios físicos como terminal de punto de venta.
Entre sus funcionalidades actuales se encuentran:

- Organiza los productos en familias de productos.
- Los consumibles se definen con un coste y un precio de venta (definiendo el margen bruto deseado); a partir de ellos, se crean productos vendibles.
- Los productos vendibles pueden crearse directamente desde un consumible o a partir de una combinación de varios (en diferentes proporciones).
- El proceso de venta de los productos se calcula automáticamente en base a los márgenes deseados. Además, puede sobrescribirse manualmente.
- Se pueden aplicar descuentos a los productos, lo que impacta en su precio de venta.
- Control de niveles de stock con alertas si bajan del mínimo establecido.
- Genera y envia facturas de forma automatica a los clientes adheridos a la factura electronica
- Se pueden generar varios informes para obtener información sobre las ventas.

## Instalación

Crea un entorno virtual basado en Python 3.11 o superior.  
Utiliza el gestor de paquetes [pip](https://pip.pypa.io/en/stable/) para instalar Tiny TPV.

```
pip install -r requirements.txt
```

## Uso

Una vez en funcionamiento, lo primero que aparece es la página de inicio de sesión.  
![login page](/assets/images/login.png)  
El inicio de sesión en este proyecto se realiza mediante un identificador (sin nombre de usuario ni contraseña). El identificador de usuario es un código (de hasta 20 caracteres) que se asigna a cada usuario cuando se crea. El proceso ha sido diseñado para que los identificadores puedan imprimirse en una tarjeta personal como un código de barras y leerse fácilmente con un escáner. 

Crea un superusuario ejecutando el siguiente comando:

```
python ./manage.py createsuperuser
```

Inicia sesión introduciendo el identificador generado en el campo de inicio de sesión.  
Una vez iniciada la sesión, se muestra la página principal donde se pueden ejecutar distintas acciones haciendo clic en los botones correspondientes:

- NUEVA FACTURA: inicia una nueva factura y se pueden asociar productos.
- NUEVO CLIENTE: se puede crear un nuevo perfil de cliente.
- STOCK: se pueden editar las unidades en stock (y el coste y precio de venta) de los distintos consumibles.
- PRECIOS: se editan los precios y descuentos activos de los distintos productos.
- INFORMES: se pueden generar distintos tipos de informes con las facturas ya creadas.
- HISTÓRICO: se pueden recuperar y revisar facturas pasadas.  
![Empty home page](/assets/images/home_0.png)

### Primeros pasos

Lo primero podría ser crear las familias de productos que organizarán el stock. Esto debe hacerse a través de la interfaz de administración típica de Django, haciendo clic en el botón de añadir familias de productos. Simplemente introduce un nombre único para la familia y créala.  
Después, se deben crear los consumibles y productos que se van a vender. Esto también se hace desde la interfaz de administración típica de Django, específicamente en la sección *ProductsAPP*.  
![admin page](/assets/images/admin_0.png)

#### Consumibles

Para crear un consumible, haz clic en el botón de crear junto a la etiqueta *Consumables* y rellena la información con los siguientes campos:

- Código de barras: el código de barras asociado al consumible.
- Comentarios: campo de texto libre para introducir comentarios relevantes.
- Familia: la familia a la que pertenece el consumible.
- Fabricante: el fabricante del consumible.
- Coste unitario: el coste de una unidad del consumible. Es el precio que se paga al proveedor.
- Precio de venta: el precio al que deseas vender una unidad del consumible. Precio de venta menos coste unitario da el margen bruto esperado.
- Cantidad mínima de pedido: mínimo de unidades que acepta tu proveedor por pedido.
- Stock actual: número actual de unidades en stock.
- Stock mínimo: número mínimo de unidades que deseas mantener. Por debajo de esto, se enviará una alerta recomendando realizar un pedido.
- Puede venderse directamente: al marcar esta opción, se crea automáticamente un producto (vendible) que consiste en una unidad del consumible.
- Consumible infinito: al marcar esta opción, se excluye al consumible del control de stock. Puede usarse para otros costes como horas hombre, electricidad, agua, etc.

![admin page](/assets/images/consumable_0.png)

#### Productos

Los productos requieren los siguientes campos:

- Imagen: imagen que se mostrará en la tarjeta del producto.
- Código de barras: código de barras asociado al producto.
- Nombre: nombre que se mostrará en los tickets y facturas.
- Detalles: detalles adicionales del producto.
- Familia: la familia que representa el producto.
- Precio de venta sobrescrito: si no es nulo, es el precio real del producto. Este valor sobrescribe el calculado automáticamente desde su consumible.
- Descuento: descuento actualmente aplicado al producto.
- Combinaciones de consumibles: si el producto consiste en una combinación de varios consumibles, sus componentes deben definirse aquí.  
  El precio de venta y el nivel de stock se calculan automáticamente según las proporciones de los diferentes consumibles.

#### Niveles de stock

Los niveles de stock pueden modificarse desde la página STOCK. Aquí se pueden editar tanto el coste como el precio de venta deseado para cada consumible, así como su stock actual.  
Los consumibles cuyo stock esté por debajo del mínimo definido se destacarán en amarillo.  
![stocks page](/assets/images/stock_0.png)

#### Precios

Los precios de venta de cualquier producto pueden sobrescribirse desde esta página. Además, pueden aplicarse descuentos a los productos.  
![prices page](/assets/images/prices_0.png)

#### Empecemos a facturar

Una vez creados los productos en la base de datos, es hora de empezar a venderlos. Al hacer clic en el botón NUEVA FACTURA, se abre una nueva factura donde los productos se pueden añadir haciendo clic en su imagen o escaneando su código de barras (en el campo de texto correspondiente).  
El producto añadido aparecerá en el panel derecho y el coste total de la factura se actualizará. Al añadir un producto, aparecerá un teclado numérico que permite definir el número de unidades del producto (en lugar de escanearlas todas una a una).  

![admin page](/assets/images/bill_1.png)

Una vez escaneados todos los productos, la factura debe cerrarse pulsando el botón verde del panel derecho.  
![admin page](/assets/images/bill_2.png)

Esto lleva a la página de resumen de la factura donde se muestra un resumen y se debe indicar el método de pago.  
![admin page](/assets/images/bill_resume_0.png)

Una vez confirmada la factura, se vuelve a mostrar la página principal. Ahora se mostrarán en tabla todas las facturas realizadas durante el día.  
![Full home page](/assets/images/home_1.png)

#### Informes

Cuando se han introducido varias facturas —o mejor aún, han pasado varios días introduciendo facturas— se puede extraer información útil de la base de datos en forma visual.

Por ejemplo, se puede obtener información sobre el número de facturas (operaciones) o los ingresos totales por día:  
![sales report 1](/assets/images/per_day.png)

O según el día de la semana:  
![sales report 2](/assets/images/per_weekday.png)

O incluso por hora:  
![sales report 3](/assets/images/per_hour.png)

Esta información puede ser útil para determinar cuáles son los días u horas de mayor actividad en la tienda.

Además, se puede obtener información por producto, como el número de unidades vendidas o el beneficio total por producto:  
![product report 1](/assets/images/per_product_units_sold.png)  
![product report 2](/assets/images/per_product_revenue.png)

Esta información puede ayudar a definir niveles mínimos de stock, identificar productos rentables o aquellos que no lo son tanto.

## Contribuciones

Los *pull requests* son bienvenidos. Para cambios importantes, abre primero un *issue* para discutir lo que te gustaría modificar.

Por favor, asegúrate de actualizar los tests según corresponda.

## Licencia

Tiny TPV es software libre: puedes redistribuirlo y/o modificarlo bajo los términos de la Licencia Pública General GNU publicada por la Free Software Foundation, ya sea en su versión 3 o (según tu elección) cualquier versión posterior.

Tiny TPV se distribuye con la esperanza de que sea útil, pero **SIN NINGUNA GARANTÍA**; ni siquiera la garantía implícita de COMERCIALIZACIÓN o ADECUACIÓN PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública General GNU para más detalles.

Debes haber recibido una copia de dicha licencia junto con Tiny TPV (ver [license](gpl-3.txt)).