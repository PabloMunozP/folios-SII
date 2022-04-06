#!/usr/bin/env bash

function usage {
  echo "Error: no certificate filename or name supplied."
  echo "Usage: $ ./installcerts.sh <certname>.pem <Cert-DB-Name>"
  exit 1

}

if [ -z "$1" ] || [ -z "$2" ]
  then
    usage
fi

certificate_file="$1"
certificate_name="$2"
# Cambiar ruta para buscar cert9.db
ruta="$(pwd)/api_sii/data/profile"
echo ${ruta}
for certDB in $(find ${ruta} -name "cert9.db")
do
  cert_dir=$(dirname ${certDB});
  echo ${cert_dir};
  echo "Mozilla Firefox certificate" "install '${certificate_name}' in ${cert_dir}"
  certutil -A -n "${certificate_name}" -t "TCu,Cu,Tu" -i ${certificate_file} -d sql:"${cert_dir}"
done
