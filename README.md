panacompra
==========

herramienta para recolectar data de panacompra


Dependencies
-------------
* mongodb
* python 2.7


To-Do
-------
* better handling of HAR file (hardcode array)
* add a class for processing stats and outputting reports


usage
------
    python panacompra.py
    mongoexport --db panacompras --collection compras --csv --fields data.entidad,data.precio,data.proponente,data.acto --out compras.csv
