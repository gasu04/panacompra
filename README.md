panacompra
==========

tool para recolectar data de panacompra


Dependencies
-------------
* BeautifulSoup
* sqlalchemy 
* pyyaml
* requests 
* python 2.7

Database Setup
--------------
1. configurar db_url en panacompra.py para usar un db existente que sea [compatible con sqlalchemy]('http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html#database-urls', 'SqlAlchemy')

To-Do
-------
* collect more data (more regex)
* get new via pgsql
* handle updates


usage
------
```bash
python panacompra.py --help

usage: panacompra.py [-h] [--send] [--update] [--sync] [--revisit] [--reparse]
                     [--pending] [--url URL]

Dataminer for Panacompra

optional arguments:
  -h, --help  show this help message and exit
  --send      send bulk compras to rails
  --update    only scrape first page of every category
  --sync      sync db to rails app
  --revisit   revisit db
  --reparse   reparse db
  --pending   process pending compras in db
  --url URL
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
