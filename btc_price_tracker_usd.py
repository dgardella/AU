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


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt  #

##track_symbol= [ sys.argv[1] ] # Obtengo Valor 1 - Par a seguir 
##track_exchange= [ sys.argv[2] ] # Obtengo Valor 2 - Exchange
track_symbol='BTC/USD'
buy_exchange='Kraken'
#track_exchange='exmo'
track_exchange_list=['dsx','kraken','bitstamp','coinbasepro']
volumen_inicial = 10
fecha=time.strftime("%Y-%m-%d %H:%M:%S")
sleep_time=30
recomendacion_compra = 3
#valor_anterior=0


MYSQL_IP = "195.201.32.212"

def enviar_mail(mailbody):
        msg = MIMEText(mailbody)
        msg['To'] = email.utils.formataddr(('Diego', 'notificaciones.crypto@gmail.com '))
        msg['From'] = email.utils.formataddr(('BotKraken', 'dgardella@gmail.com'))
        msg['Subject'] = 'Recomendacion Compra'
        server = smtplib.SMTP()
        server.connect ('localhost', 25)
        try:
                server.sendmail('dgardella@gmail.com', ['dgardella@gmail.com'], msg.as_string())
        finally:
                server.quit()

## LEG 1 ##
def f_get_price():
	sube_count=0
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
					sql_select_query="""select last from crypto_track where symbol='BTC/EUR' and exchange=%s order by id desc limit 1"""
					mycursor.execute(sql_select_query, track_exchange)
					data = mycursor.fetchone() #get the data in data variable
					#print(data)
					# me quedo con los datos de kraken
					print (track_exchange,track_symbol,last_price)
					if track_exchange == 'kraken':
						precio_compra_kraken = ask_price
						precio_venta_kraken = ask_price + 10
					
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
					##
					print (tendencia)
					# Actualizo tup
					tup_row.append(last_price)
					
				

	print (tup_row)
	print ("SUBE ::" , sube_count)

while True:
	f_get_price()
	print ("sleeping ..")
	time.sleep(sleep_time)
