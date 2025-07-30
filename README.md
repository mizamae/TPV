<!-- This file is part of Tiny TPV.

Tiny TPV is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Tiny TPV is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Tiny TPV. If not, see <https://www.gnu.org/licenses/>. -->

# Tiny TPV
[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README.es.md)

Tiny TPV is a fully featured application that can be used in physical commerces as a payment terminal.
Among its current available features are:
- Organizes the products on product families.
- Consumables are defined with cost and selling price (defining the desired gross margin); and from them, sellable products are created.
- Sellable products can be created directly from one consumable or from a combination of several ones (in different proportions).
- The selling process of the products are automatically calculated based on desired margins. Besides, it can be overriden manually.
- Discounts can be applied to products impacting on its selling price.
- Control of the stock levels and raises warnings if lower than minimum.
- Generates and sends invoices automatically to customers adhered to e-invoicing
- Several reports can be generated to obtain information about the sales. 

## Installation

### Cloning the repository
Use Git tools to clone the repository into your local machine.

### Creation of Python virtuel env
Create a virtual environment based on Python 3.11 or newer.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Tiny TPV.

```
pip install -r requirements.txt
```

### Configuration of the thermal printer

Depending on your thermal printer, a slightly different procedure should be followed. In my case, to make a TM-P80 type thermal printer on a Windows 10 machine, the following steps should be followed:

- Download [Zadig](https://zadig.akeo.ie/) to install the proper driver
- Setup the libusbK driver for the USB printer compatibility profile
- Try if configuration is correct by executing python ./utils/usbUtils.py

## Usage

Once up and running the first thing that appears is the login page.
![login page](/assets/images/login.png)
The login in this project has been established by an identifier (no username and password). The user identifier is a code (up to 20 characters long) that is assigned to each user
when created. The login process has been conceived so that identifiers can be printed in a personal card as a barcode and easily read with a barcode scanner.

Create a superuser by issuing the following command
```
python ./manage.py createsuperuser
```
Login by introducing the generated identifier in the login field.
Once logged in, the base page is shown where different actions can be executed by clicking in the corresponding buttons.

- NEW BILL: starts a new bill and products can be asociated to it
- NEW CUSTOMER: new customer profile can be created
- STOCK: the units in stock (and the cost and selling price) of the different consumables can be edited here
- PRICES: the prices and active discounts of the different products is edited here.
- REPORTS: Different type of reports can be generated with the bills already created.
- HISTORIC: Any past bill can be gathered and revised.
![Empty home page](/assets/images/home_0.png)

### First steps

The first thing to do might be to create the product families that will organize the stock. This should be done through the typical Django admin interface
by clicking the Product families add button. Simply introduce a unique name for the family and create it. 
Afterwards, the consumables and products to be sold should be created. This should be done through the typical Django admin interface
specifically in the ProductsAPP section.
![admin page](/assets/images/admin_0.png)

#### Consumables

To create a consumable, click on the create button next to Consumables label and fill-in the information with the following fields:
- Barcode: the bar code associated to this consumable.
- Comments: free-text field to introduced relevant comments.
- Family: the family that the consumable is associated to.
- Manufacturer: the manufacturer of the consumer.
- Unitary cost: the cost of one unit of the consumable. This is the price that you pay to your supplier.
- Selling price: the price you would like to sell one unit of consumable. Selling price minus Unitary cost would yield the gross margin you expect.
- Minimum order quantity: the minimum units of consumable that your supplier accept in an order.
- Current stock: curent number of units in your stock.
- Minimum stock: minimum number of units in stock you would like to have. Below that, a warning notification is sent encouraging to issue an order 
to acquire more.
- Can be directly sold: checking this flag, automatically creates a product (eligible to be sold) that consists of one unit of consumable.
- Infinite consumable: checking this flag discards the consumable from the stock control. This can be used to count for other type of costs such as
man-hours, electricity, water, etc.

![admin page](/assets/images/consumable_0.png)

#### Products

The products require the following fields:
- Image: The image that will be shown in the card of the product
- Barcode: the barcode associated to the product. 
- Name: The name that will be shown in the tickets and bills.
- Details: Additional details of the product
- Family: The family that represents the product
- Override selling price: If different to null, it is the actual price of the product. This value overrides the automatically calculated from its consumable.
- Discount: The discount currently applied to the product.
- Combinations of consumables: If the product consists of any combination of several consumables, its constitutents should be defined here.
The selling price and the stock level are automatically calculated according to the proportions of the different consumables.

#### Stock levels

The stock levels can be modified from the STOCK page. Here the cost or the desired selling price for every consumable can be edited as well as its 
current stock level. The consumables whose stock level is below its minimum defined will be highlighted in yellow.

![stocks page](/assets/images/stock_0.png)

#### Prices

The selling prices of any product can be overriden from this page. Additionally, discounts can be applied to the products.

![prices page](/assets/images/prices_0.png)

#### Let's start billing

Once the products are created in the database, it is time to start selling them. Clicking the NEW BILL button opens a new billing where products can 
be appended by simply clicking on its image or by scanning a barcode (inside the barcode textbox)
The appended product will appear in the right side panel and the bill's total cost will be updated accordingly. When a product is appended, a numeric keyboard appears 
that allows to set a defined number of units to that product (instead of scanning them all).

![admin page](/assets/images/bill_1.png)

Once all the products have been scanned, the bill should be closed by hitting the green button on the right side panel. 

![admin page](/assets/images/bill_2.png)

This leads to the bill resume page where a summary of the bill is shown and the payment method should be indicated.

![admin page](/assets/images/bill_resume_0.png)

Once the bill is confirmed, the home page is again shown. Now all the bills executed today will be shown as a table.

![Full home page](/assets/images/home_1.png)

#### Reporting

When several bills have been introduced, or better of, several days have passed while introducing bills; some rich information can be extracted
from the database in a visual form.

For example, information about the number of bills (operations) or the total income can be gathered in a per day basis,

![sales report 1](/assets/images/per_day.png)

or on a per week-day basis,

![sales report 2](/assets/images/per_weekday.png)

or even on a per-hour

![sales report 3](/assets/images/per_hour.png)|

This information can be helpful in defining the shop's more active days or hours. 

Additionally, information on a per product's base can also be yielded such as the number of items sold of each product or the total benefit from 
each of the product.

![product report 1](/assets/images/per_product_units_sold.png)
![product report 2](/assets/images/per_product_revenue.png)|

This information can be helpful in determining minimum stock levels, real money-making products or those not very profitable.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

Tiny TPV is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Tiny TPV is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Tiny TPV (see [license](gpl-3.txt)).
