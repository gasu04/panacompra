panacompra
==========

herramienta para recolectar data de panacompra


Dependencies
-------------
* mongodb
* python 2.7


To-Do
-------
* include category in compra data (pass it from scraper to worker)
* collect more data (more regex)
* add a class for processing stats and outputting reports




usage
------
    python panacompra.py
    mongoexport --db panacompras --collection compras --csv --fields data.entidad,data.precio,data.proponente,data.acto --out compras.csv
