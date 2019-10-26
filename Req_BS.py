import requests
import bs4
import re
import time
import pandas as pd
import numpy as np

from pprint import pprint


class Scraper():
	def __init__(self):
		self.propiedades = list()
		self.cuenta = 0
		self.totalCasas = 0
		self.pagina = 1
		self.peticion = ""
		self.precio_dolar = 0

	def parametros_iniciales(self):
		url = "https://www.inmuebles24.com/departamentos-en-venta-en-zona-hotelera.html"
		peticion = requests.get(url)
		print(url)
		print(peticion)
		parsear = bs4.BeautifulSoup(peticion.text, "html.parser")
		self.totalCasas = int(parsear.find('h1', {'class':'list-result-title'}).b.text)
		print('TOTAL CASAS : ', self.totalCasas)

		url2 = "https://www.eldolar.info/es-MX/mexico/dia/hoy"
		peticion2 = requests.get(url2)
		parsear2 = bs4.BeautifulSoup(peticion2.text, "html.parser")
		precio = parsear2.find('p', {'title':'A la compra'}).span.text
		self.precio_dolar = round(float(precio),2)
		print()
		print('Precio del dolar el dia de hoy ${}'.format(self.precio_dolar))
		print()

	def limpia_texto(self, texto):
		texto = texto.replace("\n", "")
		texto = texto.replace("\t", "")
		texto = texto.replace("<b>", "")
		texto = texto.replace("</b>","")
		return texto

	def obtener_numero(self, numero):
		numero = numero.split('-')
		numero = int(numero[-1])
		return numero

	def precio2pesos(self, texto):
		texto = texto.replace(",","")
		apoyo = texto.split()
		pp = 0
		if apoyo[0] == 'USD':
			pp = float(apoyo[1]) * self.precio_dolar
		else:
			pp = float(apoyo[1])
		return pp

	def obtiene_caracteristicas(self, lista):
		salida = dict()
		salida['terreno'] = None
		salida['construidos'] = None
		salida['cuartos'] = None
		salida['banos'] = None
		salida['estacionamiento'] = None

		for elem in lista:
			temp = elem.split()
			if (temp[-1] in 'terreno'):
				salida['terreno'] = temp[0]
			elif (temp[-1] in 'construidos'):
				salida['construidos'] = temp[0]
			elif (temp[-1] in 'Recámaras'):
				salida['cuartos'] = temp[0]
			elif (temp[-1] in 'Estacionamientos'):
				salida['estacionamiento'] = temp[0]

		return salida


	def extrae_informacion(self):
		self.parametros_iniciales()
		while self.cuenta <= self.totalCasas:
			url = "https://www.inmuebles24.com/departamentos-en-venta-en-zona-hotelera-pagina-{}.html".format(self.pagina)			
			self.peticion = requests.get(url)
			parsear = bs4.BeautifulSoup(self.peticion.text, "html.parser")
			todas = parsear.findAll("div", {"class":"general-content"})

			for unaProp in todas:
				propiedad = dict()
				precio = unaProp.find("span", {"class":"first-price"})
				precio = precio['data-price']
				precio_pesos = self.precio2pesos(precio)
				
				cabeza = unaProp.find("a", {'class':'go-to-posting'})
				link = "https://www.inmuebles24.com" + cabeza['href']
				titulo = cabeza.text
				titulo = self.limpia_texto(titulo)

				localizacion = unaProp.find("span", {"class":"posting-location go-to-posting"})
				ubicacion = localizacion.text
				ubicacion = self.limpia_texto(ubicacion)
				zona = localizacion.span.text.strip()

				descripcion = unaProp.find("div", {"class":"posting-description go-to-posting"}).text
				descripcion = self.limpia_texto(descripcion)

				tablaCaract =  unaProp.find("ul", {"class":"main-features go-to-posting"})
				caracteristicas = list()
				if tablaCaract:
					for c in tablaCaract.findAll('b'):
						if c.text:
							caracteristicas.append( self.limpia_texto(c.text))

				caracts = self.obtiene_caracteristicas(caracteristicas)

				tablaOtra = unaProp.find('ul', {'class':'posting-features go-to-posting'})
				otraInfo = list()
				for info in tablaOtra.findAll('li'):
					otraInfo.append(info.text)

				contacto = unaProp.find('div', {'class':'posting-buttons'}).div['id']
				contacto = self.obtener_numero(contacto)
				
				propiedad['titulo'] = titulo
				propiedad['enlace'] = link
				propiedad['ubicacion'] = ubicacion
				propiedad['zona'] = zona
				propiedad['precio_publicado'] = precio
				propiedad['precio_pesos'] = precio_pesos
				propiedad['terreno_m2'] = caracts['terreno']
				propiedad['construidos_m2'] = caracts['construidos']
				propiedad['cuartos'] = caracts['cuartos']
				propiedad['banos'] = caracts['banos']
				propiedad['estacionamiento'] = caracts['estacionamiento']
				propiedad['contacto'] = contacto
				
				self.propiedades.append(propiedad)

				self.cuenta = self.cuenta + 1

			self.pagina = self.pagina + 1

			if (self.cuenta % 100 == 0):
				print("{} / {} ".format(self.cuenta, self.totalCasas))
				time.sleep(2)

		#self.genera_csv()

	def genera_csv(self):
		df = pd.DataFrame(self.propiedades, columns = ['titulo', 'enlace','ubicacion','zona',
											'precio_publicado', 'precio_pesos', 'terreno_m2', 'construidos_m2',
											'cuartos', 'banos', 'estacionamiento', 'contacto'])
		df.to_csv('propiedades.csv')

	def analisis_csv(self):
		try:
			df = pd.read_csv('propiedades.csv',  index_col=0)
			df = df[['construidos_m2', 'precio_pesos']]

			print()
			print(df.describe())
			print()

			low = .05
			high = .95
			quant_df = df.quantile([low, high])

			df2 = df.apply(lambda x: x[(x>quant_df.loc[low,x.name]) & 
                                    (x < quant_df.loc[high,x.name])], axis=0)

			df2['precio_m2'] = np.where(df2['construidos_m2'] > 0, 
												round(df2['precio_pesos']/df2['construidos_m2'], 2), 
												df2['construidos_m2'])
			print()
			print(df2.head())
			print()
			
			print()
			
			print('mediana precios : ${:20,.2f}'.format(round(df2['precio_pesos'].median(), 2)) )
			print('promedio precios : ${:20,.2f}'.format(round(df2['precio_pesos'].mean(),2)) )

			print()

			print('promedio precio/m2 : ${:20,.2f}'.format(round(df2['precio_m2'].median(), 2)) )
			print('promedio precio/m2 : ${:20,.2f}'.format(round(df2['precio_m2'].mean(), 2)) )
			print()

		except:
			print('Ocurrio un error al abrir el csv, posiblemente no existe')



scraper = Scraper()

# Extraer informacion de la pagina y generar el csv para guardar todos los registros
#scraper.extrae_informacion() 

scraper.analisis_csv()