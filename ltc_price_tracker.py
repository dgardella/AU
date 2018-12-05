# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import datetime
import resource
import logging
import pymysql
import re
import smtplib
import email.utils
from email.mime.text import MIMEText
from au_functions import get_open_orders


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt  #

##track_symbol= [ sys.argv[1] ] # Obtengo Valor 1 - Par a seguir 
##track_exchange= [ sys.argv[2] ] # Obtengo Valor 2 - Exchange
track_symbol='LTC/EUR'
buy_exchange='Kraken'
#track_exchange='exmo'
track_exchange_list=['dsx','kraken','bitstamp','coinbasepro']
volumen_inicial = 10
fecha=time.strftime("%Y-%m-%d %H:%M:%S")
sleep_time=30
recomendacion_compra = 3
recomendacion_compra_2 = 5
#valor_anterior=0
spread=0.5
sube_count=0
baja_count=0


def enviar_mail(mailbody):
        msg = MIMEText(mailbody)
        msg['To'] = email.utils.formataddr(('Diego', 'notificaciones.crypto@gmail.com '))
        msg['From'] = email.utils.formataddr(('BotKraken', 'dgardella@gmail.com'))
        msg['Subject'] = 'Recomendacion Compra LTC/EUR'
        server = smtplib.SMTP()
        server.connect ('localhost', 25)
        try:
                server.sendmail('dgardella@gmail.com', ['dgardella@gmail.com'], msg.as_string())
        finally:
                server.quit()

## LEG 1 ##
def f_get_price():
	global sube_count
	global baja_count
	global fecha
	global buy_exchange
	global buy_exchange
	global precio_compra_kraken
	global precio_venta_kraken
	global precio_venta_minimo_kraken
	valor_anterior = 0
	fecha=time.strftime("%Y-%m-%d %H:%M:%S")
	precio_compra_kraken = 0
	precio_venta_kraken = 0
	# Modificacion multiples exchanges
	# define tup for row
	tup_row = []
	tup_row.append(fecha)
	for track_exchange in track_exchange_list:
		print ('Loading exchange :' , track_exchange, track_symbol,fecha)
		exchanger = getattr(ccxt, track_exchange)()
		try:
			markets = exchanger.load_markets()
		except Exception:
			pass
		else:
			try :
				ticker = exchanger.fetch_ticker(track_symbol) # ticker for BTC/USD
			except Exception:
				#print (symbol, "Not found in :" , exch)
				pass
			else:
				#print (" !!! " , symbol, "Encontrado en :" , exch)
				json_str = json.dumps(ticker)
				resp = json.loads(json_str)
				if resp is None:
					pass
				else:
					last_price = resp['last']
					ask_price = resp['ask']
					print (fecha,";",last_price)
					# Registro las operacion en la base de datos
					db = pymysql.connect("bot.zapto.org","cryptodb","M3xico.860#f3","crypto" )
					# get last value
					mycursor = db.cursor()
					sql_select_query="""select last from crypto_track where symbol='LTC/EUR' and exchange=%s order by id desc limit 1"""
					mycursor.execute(sql_select_query, track_exchange)
					data = mycursor.fetchone() #get the data in data variable
					#print(data)
					# me quedo con los datos de kraken
					print (track_exchange,track_symbol,last_price)
					if track_exchange == 'kraken':
						precio_compra_kraken = ask_price
						precio_venta_kraken = ask_price + spread
						precio_venta_minimo_kraken = ask_price - (spread/2)
					
					if data is None:
						tendencia = 'COMIENZO'
						precio_anterior = 10000
					else:
						precio_anterior = float(data[0]) # load the data into value with conversion of its type
						print ("Precio Anterior:" , precio_anterior)
					if precio_anterior < last_price:
						tendencia = 'SUBE'
						sube_count += 1
					if precio_anterior == last_price:
						tendencia = 'IGUAL'
					if precio_anterior > last_price:
						tendencia = 'BAJA'
						baja_count += 1
					##
					print (tendencia)
					# Actualizo tup
					tup_row.append(last_price)
					print("Sube count" , sube_count)
					print("Baja count" , baja_count)
					
				

					#Insert new data
					cursor = db.cursor()
					query = "INSERT INTO crypto_track (exchange,symbol,fecha,last,tendencia) " \
					"VALUES(%s,%s,%s,%s,%s)"
					args = (track_exchange,track_symbol,fecha,last_price,tendencia)
					try:
						cursor.execute(query, args)
						db.commit()
					except:
					#except my.Error as e:
						print(e)
						d.rollback()
						db.close()
	# imprimo tup
	print (tup_row)
	print ("SUBE ::" , sube_count)

# Termino funcion 
#Comienzo ejecution
get_open_orders()
f_get_price()

if get_open_orders() >= 20:
	print ("Demasiadas ordenes abiertas")
	sys.exit()
else:
	print ("Ok para poner ordenes")
	db = pymysql.connect("bot.zapto.org","cryptodb","M3xico.860#f3","crypto" )
	if sube_count >= recomendacion_compra:
		acumulado = sube_count
		print ("Acumulado : ", acumulado)
		print ("Sube_COunt : ", sube_count)
		# Primera señal de compra - Buscar la segunda
		print ("encontre 1ra señal espero 30 segundos y vuelvo a buscar")
		print ("Pongo sube count en 0")
		sube_count = 0
		time.sleep(sleep_time)
		f_get_price()
		print ("Acumulado : ", acumulado)
		print ("Sube_COunt : ", sube_count)
		if sube_count + acumulado >= recomendacion_compra_2:
			baja_count = 0
			time.sleep(sleep_time)
			f_get_price()
			if baja_count < 1:
				print("encontre segunda señal - genero orden")
				mailm = "Recomendacion Compra Kraken :: " +  str(fecha) + ":: comprar a :: " + str(precio_compra_kraken) + " :: vender a :: " + str(precio_venta_kraken)
				print ("Señal compra - enviando mail")
				enviar_mail(mailm)
		# registro las operaciones en la db
				cursor = db.cursor()
				query = "INSERT INTO automatic_orders (fecha,exchange,symbol,precio_compra,precio_venta,precio_minimo,status) " \
					"VALUES(%s,%s,%s,%s,%s,%s,%s)"
				args = (fecha,buy_exchange,track_symbol,precio_compra_kraken,precio_venta_kraken,precio_venta_minimo_kraken,'open')
				try:
					cursor.execute(query, args)
					db.commit()
				except:
					#except my.Error as e:
					print(e)
					d.rollback()
					db.close()
			else:
				sube_count = 0
				baja_count = 0
		else:
			sube_count = 0
			baja_count = 0
