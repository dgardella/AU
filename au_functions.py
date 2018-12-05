# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import datetime
import resource
import logging
import pymysql


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')


def get_open_orders():
	db = pymysql.connect("bot.zapto.org","cryptodb","M3xico.860#f3","crypto" )
	mycursor = db.cursor()
	sql_select_query="select count(*) from automatic_orders where status='open'"
	mycursor.execute(sql_select_query)
	data = mycursor.fetchone() #get the data in data variable
	open_orders = float(data[0])
	return open_orders
	#print (open_orders)
	#if open_orders >= 10:
		#print ("Demasiadas ordenes abiertas - Saliendo")
		#sys.exit()

#get_open_orders()
