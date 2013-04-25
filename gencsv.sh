#!/bin/bash

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 OUTFILE"
  exit 1
fi

mongoexport --db panacompras --collection compras --csv --fields data.entidad,data.precio,data.proponente,data.descripcion,category,data.fecha,data.acto,url, --out $1
