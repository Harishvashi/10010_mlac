#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This file is automatically generated by AION for AION_ver_260_1 usecase.
File generation time: 2023-01-16 12:20:42
'''
import sys
import math
import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import platform
from utility import *
from data_reader import dataReader

IOFiles = {
        "monitoring":"monitoring.json", 
        "prodDataGT":"prodDataGT"
    }

class groundtruth():
    
    def __init__(self, base_config):        
        self.targetPath = Path('aion')/base_config['targetPath']  
        data = read_json(self.targetPath/IOFiles['monitoring'])
        self.prod_db_type = data['prod_db_type']
        self.db_config = data['db_config']
	
    def actual(self, data=None):
        df = pd.DataFrame()
        jsonData = json.loads(data)
        df = pd.json_normalize(jsonData)
        if len(df) == 0:
            raise ValueError('No data record found')
        self.write_to_db(df)
        status = {'Status':'Success','Message':'uploaded'}
        return json.dumps(status)
		
    def write_to_db(self, data):
        prod_file = IOFiles['prodDataGT']
        writer = dataReader(reader_type=self.prod_db_type, target_path=self.targetPath, config=self.db_config )
        writer.write(data, prod_file)
        writer.close()
			
