# Uso de la API

## Pasos previos

Esta API utiliza los certificados digitales en formato PEM, por lo que es necesario convertir desde PFX a PEM antes de ingresarlos. Para esto se utiliza el modulo openssl incluido en la mayoria de sistemas.

### Convertir PFX a PEM
  + Ingresar a la carpeta donde se ubique el certificado pfx.
  + Abrir terminal e ingresar el siguiente comando `openssl pkcs12 -in in_file.pfx -out out_file.pem -nodes `  

## Pasos para instalacion

  + Desactivar seguridad para aceptar certificados de 1024 bit modificando openssl.cnf, cambiar a @seclevel=1 [ver aqui](https://askubuntu.com/questions/1233186/ubuntu-20-04-how-to-set-lower-ssl-security-level)
    + Para ubicar el archivo openssl.cnf a configurar se puede ejecutar el comando `openssl version -d` 
    + Abrir el archivo previamente ubicado e incluir lo siguiente:
      + En la parte superior incluir: 
          
            openssl_conf = default_conf 
      
      + En la parte final incluir :
        
            [ default_conf ] 
            ssl_conf = ssl_sect 
          
            [ssl_sect]
            system_default = system_default_sect 
            
            [system_default_sect]
            MinProtocol = TLSv1.2
            CipherString = DEFAULT:@SECLEVEL=1

  + Obtener los archivos desde respositorio git
  + Seguir las instruciones del manual de instalacion.


## Autenticacion

Antes de comenzar a utilizar los servicios de la API se debe autenticar el usuario, previamente creado en Django, y obtener un token de autenticacion. Para esto se debe enviar una peticion POST incluyendo el usario y contraseña en su body con el siguiente formato:
    
  + `request.post('http://ip_host:port/auth', data={'username': "user" , "password": "pass"}`
  
  + Esto devolvera un token de autenticacion a utilizar para tener acceso a la API, con el siguiente formato: `{"token":"80af2d944cbf55bfc2fec00b49f90dcd389626f2"}` como se ve en la imagen ![img autenticacion](instalacion/auth_ok.png)
  + En caso de error retornara una alerta de credenciales invalidas como se ve en la imagen ![img autenticacion error](instalacion/auth_error.png)
 
## Pedir Folios

Para obtener los folios se debe hacer una peticion GET a la direccion del servidor agregando '/api/solicitarFolios' con el siguiente formato:

  +  `request.get("http://ip_host:port/api/solicitarFolios", headers={"Authorization":"Token 80af2d944cbf55bfc2fec00b49f90dcd389626f2"}, data={"rut":"1234567-8","cant_folios":"1",'cod_doc':"33"} `

Donde:
  + rut (str): El rut de la empresa a consultar. Debe ser enviado sin puntos, con guion y digito verificador.

  + cod_doc (str): El codigo del documento a solicitar.

  + cant_folios (str): La cantidad de folios que quieren solicitar, esta cantidad esa sujeta a disponibilidad del SII. Solicitar mas del permitidado llevara a un error notificando la cantidad maxima a solicitar.

### Respuesta

  + Si la peticion se realizo correctamente la respuesta sera un json como se ve en la imagen ![imagen solicitar ok](instalacion/solicitarFolios_ok.png)
  
  + En caso contrario pueden ocurrir los siguientes escenarios:
    + Usuario ha sido deshabilitado en la pagina de administracion de Django. Retornara un json como se ve en la imagen ![imagen cliente sin acceso](instalacion/cliente_sin_acceso.png)
    
    + Usuario registra situaciones pendientes con el sii. Retornara un json como se ve en la imagen ![imagen error pendientes](instalacion/solicitarFolios_err1.png)
    
    + Usuario solicita mas de los folios permitidos. Retornara un json notificando el error junto a la cantidad maxima de folios permitidos.

    + Usuario solicita un documento no permitido. Retornara un json notificando el error y texto de la alerta.


## Consultar Folios
 Para consultar los folios emitidos se debe hacer una peticion GET a la direccion del servidor agregrando '/api/consultarFolios' con el siguiente formato:
    
  + `request.get("http://ip_host:port/api/consultarFolios", headers={"Authorization":"Token 80af2d944cbf55bfc2fec00b49f90dcd389626f2"}, data={"rut":"1234567-8",'cod_doc':"33"} `

Donde: 

  + rut (str): El rut de la empresa a consultar. Debe ser enviado sin puntos, con guion y digito verificador.
  + cod_doc (str): El codigo del documento a consultar. 

### Respuesta

  + Si la peticion se realizo correctamente la respuesta sera un json como se ve en la imagen ![imagen solicitar ok](instalacion/consultarFolios_ok.png)
  + En caso contrario pueden ocurrir los siguientes escenarios:
    + Usuario ha sido deshabilitado en la pagina de administracion de Django. Retornara un json como se ve en la imagen ![imagen cliente sin acceso](instalacion/cliente_sin_acceso.png)
    + Usuario no registra timbrajes del documento solicitado. Retornara un json como se ve en la imagen ![imagen error no info](instalacion/consultarFolios_noInfo.png)

    
## Anular Folios

Para anular folios se debe hacer una peticion GET a la direccion del servidor agregando '/api/deleteFolios' con el siguiente formato:
    
  + `request.get("http://ip_host:port/api/deleteFolios", headers={"Authorization":"Token 80af2d944cbf55bfc2fec00b49f90dcd389626f2"}, data={"rut":"1234567-8","id":"33-1-100", "motivo":"motivo_anulacion", "folio_inicio":"1", "folio_final":"100"} `

Donde:

  + rut (str): El rut de la empresa a consultar. Debe ser enviado sin puntos, con guion y digito verificador.

  + id (str): El id del folio a anular, este se obtiene al consultar los folios y sigue el formato:  `codigoDocumento_folioInicial_folioFinal`

  + motivo (str): El motivo de la cancelacion del folio.

  + folio_inicio(str): Numero del folio inicial a anular.

  + folio_final(str) : Numero del folio final a anular.

### Respuesta

  + Si la peticion se realizo correctamente la respuesta sera un json como se ve en la imagen ![imagen anular ok](instalacion/anular_ok.png)

  + En caso contrario pueden ocurrir los siguientes escenarios:
    + Usuario ha sido deshabilitado en la pagina de administracion de Django. Retornara un json como se ve en la imagen ![imagen cliente sin acceso](instalacion/cliente_sin_acceso.png)
    + El folio solicitado ya ha sido anulado. Retornara un json como se ve en la imagen ![imagen error anular](instalacion/anular_err1.png)
    + El folio solicitado no existe. Retornara un json como se en la imagen ![imagen error anular](instalacion/anular_err2.png)

## Funciones
  + login(rut): esta funcion permite el inicio de sesion del webdriver. El rut ingresado debe corresponder al rut de algun cliente registrado, se buscara el certificado digital asociado al rut y realiza una peticion POST al SII.
  
  + class PedirFolios: 
    + get(request): esta funcion permite solicitar folios. El request debe incluir en su body el rut de la compañia, codigo del documento y cantidad de folios. En caso de exito retornara el XML obtenido y en caso de error notificara del tipo de error.
  
  + class AnularFolios:

    + get(request): esta funcion permite anular folios. El request debe incluir en su body el rut de la compañia, el ID del folio, el motivo, el folio inicial y el final para anular. En caso de exito retornara la confirmacion de que se ha anulado el folio o la respuesta de ese folio ya ha sido anulado, en caso de error notificara el error.
  
  + class ConsultarFolios:

    + get(request): esta funcion permite consultar folios. El request debe incluir en su body el rut de la compañia y el codigo del documento a consultar. En caso de exito retornara los folios existentes o la respuesta de que no existen folios, en caso de error notifica el error.
  
