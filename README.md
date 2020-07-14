# Sistemas Distribuidos: Descarga de ficheros mediante ZeroC Ice

## Arquitectura del proyecto
El sistema estará formado por cinco tipos de componentes: *senders*, encargados del envío de ficheros; *transfers*, para la gestión de la transferencia de cada archivo; *receivers*, empleados para la recepción de ficheros; *clientes*, que solicitarán los ficheros; y canales de eventos para la comunicación de estados entre componentes.

## Objetivo del proyecto
El sistema estará compuesto por un cliente llamado *FileDownloader* con una factoría de *receivers*,
un servidor con una factoría de *transfers* y otro servidor con una factoría de *senders*. El *cliente*, que
recibirá como argumentos el nombre de los ficheros, solicitará una transferencia de N ficheros al
servidor donde están ubicados los *transfers*. Este creará un *transfer* para controlar la transferencia,
que a su vez creará una pareja *receiver-sender* para cada uno de los ficheros. Cuando todas las
parejas estén listas el cliente iniciará la transferencia, es decir, el envío entre las parejas. Los
*receivers* notificarán al *transfer* cuando hayan terminado, y este destruirá al *receiver* que envía la
notificación y a su *sender* compañero. Si todas las parejas han terminado, el *tranfer* informará al
cliente (estará a la espera), que destruirá el *transfer* (en caso de que sea el suyo) y terminará su
ejecución.

También será importante el control de fallos, al menos de los que pueden tener lugar por acciones
del cliente, para garantizar el correcto funcionamiento del lado del servidor. Por ejemplo, en el caso
de que se hagan solicitudes de ficheros que no existen la transferencia se daría por fallida, incluso
cuando solamente uno de los ficheros solicitados no existiese, destruyendo todos los componentes
relacionados con la transferencia e informando al cliente de lo sucedido.

## Cómo ejecutar
Todos los script se ejecutarán desde el directorio */src*

### Servidor
Ejecutaremos el servidor con el script 
```shell 
./run_server.sh
```

### Cliente
Ejecutaremos el cliente solicitando por linea de comandos los archivos que queramos transferir. Se pueden solicitar tantos ficheros como el cliente quiera, escribiendo delante de cada nombre del fichero la opción *-f*
```shell 
./run_client.sh -f <nombre_archivo>
```

Los ficheros que se soliciten deben de existir en la carpeta *files*, en caso de que no existan la transferencia se dará por fallida informando al cliente de lo sucedido. 
