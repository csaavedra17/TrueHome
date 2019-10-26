Para ejecutar "pruebaTecnica.py" el archivo hay dos opciones:

Una para realizar nuevamente la extracción de los datos.
La otra solo para realizar el análisis de la información.

Si se quiere realizar nuevamente la extracción, de tiene que descomentar la siguiente linea:
#scraper.extrae_informacion() 

Si se requiere realizar el analis, se tiene que dejar como está, la siguiente línea, siempre y cuando 
el archivo csv ya se encuentre creado en la misma ruta.
scraper.analisis_csv()

Para poder correr el archivo se deben tener instaladas los siguientes paquetes
- requests
- beautifulsoup
- pandas
- numpy
Saludos!
