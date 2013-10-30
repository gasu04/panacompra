panacompra
==========

tool para recolectar data de panacompra

usado en http://www.panacompra.net


Dependencies
-------------
* BeautifulSoup
* sqlalchemy 
* pyyaml
* requests 
* urllib3
* python3


usage
------
```bash
usage: panacompra.py [-h] [--update] [--reparse] [--revisit] [--visit]
                     [--pending]

Dataminer for Panacompra

optional arguments:
  -h, --help  show this help message and exit
  --update    only scrape first page of every category
  --reparse   set parsed to False and parse
  --revisit   set visited to False and visit
  --visit     get html for compras where visited is False
  --pending   process compras where visited is True and Parsed is False
```


legal stuff
------------
Copyright (C) 2013  Ivan Barria

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
