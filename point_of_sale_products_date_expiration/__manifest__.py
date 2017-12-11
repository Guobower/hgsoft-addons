# -*- coding: utf-8 -*-
##############################################################################
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Point of sale products date expiration',
    'description': 'Point of sale products date expiration',
    'summary': 'Point of sale products date expiration',
    'category': 'Point Of Sale',
    'version': '1.0',
    'website': '',
    'author': 'Wilder,Bitodoo',
    'depends': ['point_of_sale'],
    'data': [
        'views/product_date_expiration_view.xml',
    ],
    'images':['static/description/gif.gif'],
    # 'price': 9.90,
    'currency': 'EUR',
    'application': True,
}