#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This file is automatically generated by AION for AION_ver_260_1 usecase.
File generation time: 2023-01-16 12:20:42
'''

from http.server import BaseHTTPRequestHandler,HTTPServer        
from socketserver import ThreadingMixIn        
import os        
from os.path import expanduser        
import platform        
import threading        
import subprocess        
import argparse        
import re        
import cgi        
import json        
import shutil
import logging
import sys        
import time
import seaborn as sns
from pathlib import Path        
from predict import deploy
from groundtruth import groundtruth       
import pandas as pd
import scipy.stats as st
import numpy as np
import warnings
from utility import *
from data_reader import dataReader

warnings.filterwarnings("ignore")
config_input = None   
     
IOFiles = {
	"inputData": "rawData.dat",
	"metaData": "modelMetaData.json",
	"production": "production.json",  
	"log": "aion.log",
	"monitoring":"monitoring.json",
	"prodData": "prodData",
	"prodDataGT":"prodDataGT"
}

def DistributionFinder(data):
    try:
        distributionName = ""
        sse = 0.0
        KStestStatic = 0.0
        dataType = ""
        if (data.dtype == "float64" or data.dtype == "float32"):
            dataType = "Continuous"
        elif (data.dtype == "int"):
            dataType = "Discrete"
        elif (data.dtype == "int64"):
            dataType = "Discrete"
        if (dataType == "Discrete"):
            distributions = [st.bernoulli, st.binom, st.geom, st.nbinom, st.poisson]
            index, counts = np.unique(data.astype(int), return_counts=True)

            if (len(index) >= 2):
                best_sse = np.inf
                y1 = []
                total = sum(counts)
                mean = float(sum(index * counts)) / total
                variance = float((sum(index ** 2 * counts) - total * mean ** 2)) / (total - 1)
                dispersion = mean / float(variance)
                theta = 1 / float(dispersion)
                r = mean * (float(theta) / 1 - theta)

                for j in counts:
                    y1.append(float(j) / total)

                pmf1 = st.bernoulli.pmf(index, mean)
                pmf2 = st.binom.pmf(index, len(index), p=mean / len(index))
                pmf3 = st.geom.pmf(index, 1 / float(1 + mean))
                pmf4 = st.nbinom.pmf(index, mean, r)
                pmf5 = st.poisson.pmf(index, mean)

                sse1 = np.sum(np.power(y1 - pmf1, 2.0))
                sse2 = np.sum(np.power(y1 - pmf2, 2.0))
                sse3 = np.sum(np.power(y1 - pmf3, 2.0))
                sse4 = np.sum(np.power(y1 - pmf4, 2.0))
                sse5 = np.sum(np.power(y1 - pmf5, 2.0))

                sselist = [sse1, sse2, sse3, sse4, sse5]
                best_distribution = 'NA'
                for i in range(0, len(sselist)):
                    if best_sse > sselist[i] > 0:
                        best_distribution = distributions[i].name
                        best_sse = sselist[i]

            elif (len(index) == 1):
                best_distribution = "Constant Data-No Distribution"
                best_sse = 0.0

            distributionName = best_distribution
            sse = best_sse

        elif (dataType == "Continuous"):

            distributions = [st.uniform, st.expon, st.weibull_max, st.weibull_min, st.chi, st.norm, st.lognorm, st.t,
                             st.gamma, st.beta]
            best_distribution = st.norm.name
            best_sse = np.inf
            datamin = data.min()
            datamax = data.max()
            nrange = datamax - datamin

            y, x = np.histogram(data.astype(float), bins='auto', density=True)
            x = (x + np.roll(x, -1))[:-1] / 2.0

            for distribution in distributions:
                params = distribution.fit(data.astype(float))
                arg = params[:-2]
                loc = params[-2]
                scale = params[-1]
                pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                sse = np.sum(np.power(y - pdf, 2.0))
                if (best_sse > sse > 0):
                    best_distribution = distribution.name
                    best_sse = sse
            distributionName = best_distribution
            sse = best_sse
    except:
        response = str(sys.exc_info()[0])
        message = 'Job has Failed' + response
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)
        print(str(exc_type) + ' ' + str(fname) + ' ' + str(exc_tb.tb_lineno))
        print(message)
    return distributionName, sse
    
def getDriftDistribution(feature, dataframe, newdataframe=pd.DataFrame()):
    import matplotlib.pyplot as plt
    import math
    import io, base64, urllib
    np.seterr(divide='ignore', invalid='ignore')
    try:	
        plt.clf()
    except:
        pass
    plt.rcParams.update({'figure.max_open_warning': 0})
    sns.set(color_codes=True)
    pandasNumericDtypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    if len(feature) > 4:
        numneroffeatures = len(feature)
        plt.figure(figsize=(10, numneroffeatures*2))
    else:
        plt.figure(figsize=(10,5))
    
    for i in enumerate(feature):
        
        dataType = dataframe[i[1]].dtypes
        if dataType not in pandasNumericDtypes:
            dataframe[i[1]] = pd.Categorical(dataframe[i[1]])
            dataframe[i[1]] = dataframe[i[1]].cat.codes
            dataframe[i[1]] = dataframe[i[1]].astype(int)
            dataframe[i[1]] = dataframe[i[1]].fillna(dataframe[i[1]].mode()[0])
        else:
            dataframe[i[1]] = dataframe[i[1]].fillna(dataframe[i[1]].mean())
        
        plt.subplots_adjust(hspace=0.5, wspace=0.7, top=1)
        plt.subplot(math.ceil((len(feature) / 2)), 2, i[0] + 1)
        distname, sse = DistributionFinder(dataframe[i[1]])        
        print(distname)        
        ax = sns.distplot(dataframe[i[1]], label=distname)
        ax.legend(loc='best')
        if newdataframe.empty == False:
            dataType = newdataframe[i[1]].dtypes
            if dataType not in pandasNumericDtypes:
                newdataframe[i[1]] = pd.Categorical(newdataframe[i[1]])
                newdataframe[i[1]] = newdataframe[i[1]].cat.codes
                newdataframe[i[1]] = newdataframe[i[1]].astype(int)
                newdataframe[i[1]] = newdataframe[i[1]].fillna(newdataframe[i[1]].mode()[0])
            else:
                newdataframe[i[1]] = newdataframe[i[1]].fillna(newdataframe[i[1]].mean())
            distname, sse = DistributionFinder(newdataframe[i[1]])                
            print(distname)
            ax = sns.distplot(newdataframe[i[1]],label=distname)
            ax.legend(loc='best')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri
	
def read_json(file_path):        
    data = None        
    with open(file_path,'r') as f:        
        data = json.load(f)        
    return data        
        
class HTTPRequestHandler(BaseHTTPRequestHandler):        
        
	def do_POST(self):        
		print('PYTHON ######## REQUEST ####### STARTED')        
		if None != re.search('/AION/', self.path) or None != re.search('/aion/', self.path):
			ctype, pdict = cgi.parse_header(self.headers.get('content-type'))        
			if ctype == 'application/json':        
				length = int(self.headers.get('content-length'))        
				data = self.rfile.read(length)        
				usecase = self.path.split('/')[-2]
				if usecase.lower() == config_input['targetPath'].lower():					
					operation = self.path.split('/')[-1]        
					data = json.loads(data)        
					dataStr = json.dumps(data)        
					if operation.lower() == 'predict':        
						output=deployobj.predict(dataStr)        
						resp = output        
					elif operation.lower() == 'groundtruth':
						gtObj = groundtruth(config_input)				
						output = gtObj.actual(dataStr)
						resp = output        
					elif operation.lower() == 'delete':
						targetPath = Path('aion')/config_input['targetPath']                    
						for file in data:
							x = targetPath/file                           
							if x.exists():
								os.remove(x)                        
						resp = json.dumps({'Status':'Success'})
					else:        
						outputStr = json.dumps({'Status':'Error','Msg':'Operation not supported'})        
						resp = outputStr        
				else:
					outputStr = json.dumps({'Status':'Error','Msg':'Wrong URL'})        
					resp = outputStr
        
			else:        
				outputStr = json.dumps({'Status':'ERROR','Msg':'Content-Type Not Present'})        
				resp = outputStr        
			resp=resp+'\n'        
			resp=resp.encode()        
			self.send_response(200)        
			self.send_header('Content-Type', 'application/json')        
			self.end_headers()        
			self.wfile.write(resp)        
		else:        
			print('python ==> else1')        
			self.send_response(403)        
			self.send_header('Content-Type', 'application/json')        
			self.end_headers()        
			print('PYTHON ######## REQUEST ####### ENDED')        
		return        
        
	def do_GET(self):        
		print('PYTHON ######## REQUEST ####### STARTED')        
		if None != re.search('/AION/', self.path) or None != re.search('/aion/', self.path):        
			usecase = self.path.split('/')[-2]        
			self.send_response(200)        
			self.targetPath = Path('aion')/config_input['targetPath']			
			meta_data_file = self.targetPath/IOFiles['metaData']        
			if meta_data_file.exists():        
				meta_data = read_json(meta_data_file)        
			else:        
				raise ValueError(f'Configuration file not found: {meta_data_file}')
			production_file = self.targetPath/IOFiles['production']            
			if production_file.exists():        
				production_data = read_json(production_file)        
			else:        
				raise ValueError(f'Production Details not found: {production_file}')           
			operation = self.path.split('/')[-1]                
			if (usecase.lower() == config_input['targetPath'].lower()) and (operation.lower() == 'metrices'):
				self.send_header('Content-Type', 'text/html')        
				self.end_headers()            
				ModelString = production_data['Model']
				ModelPerformance = ModelString+'_performance.json'                
				performance_file = self.targetPath/ModelPerformance                
				if performance_file.exists():        
					performance_data = read_json(performance_file)        
				else:        
					raise ValueError(f'Production Details not found: {performance_data}')
				Scoring_Creteria =  performance_data['scoring_criteria']                   
				train_score =  round(performance_data['metrices']['train_score'],2)                
				test_score =  round(performance_data['metrices']['test_score'],2)  
				current_score = 'NA'                        
				monitoring = read_json(self.targetPath/IOFiles['monitoring'])
				reader = dataReader(reader_type=monitoring['prod_db_type'],target_path=self.targetPath, config=monitoring['db_config'])
				inputDatafile = self.targetPath/IOFiles['inputData']                
				NoOfPrediction = 0
				NoOfGroundTruth = 0 
				inputdistribution = ''                
				if reader.file_exists(IOFiles['prodData']):        
					dfPredict = reader.read(IOFiles['prodData'])
					dfinput = pd.read_csv(inputDatafile)
					features = meta_data['training']['features']
					inputdistribution = getDriftDistribution(features,dfinput,dfPredict)                    
					NoOfPrediction = len(dfPredict)				
					if reader.file_exists(IOFiles['prodDataGT']):        
						dfGroundTruth = reader.read(IOFiles['prodDataGT'])
						NoOfGroundTruth = len(dfGroundTruth)                    
						common_col = [k for k in dfPredict.columns.tolist() if k in dfGroundTruth.columns.tolist()]				
						proddataDF = pd.merge(dfPredict, dfGroundTruth, on =common_col,how = 'inner')
						if Scoring_Creteria.lower() == 'accuracy':    
							from sklearn.metrics import accuracy_score                        
							current_score = accuracy_score(proddataDF[config_input['target_feature']], proddataDF['prediction'])
							current_score = round((current_score*100),2)                            
						elif Scoring_Creteria.lower() == 'recall':    
							from sklearn.metrics import accuracy_score                        
							current_score = recall_score(proddataDF[config_input['target_feature']], proddataDF['prediction'],average='macro')
							current_score = round((current_score*100),2)                           
				msg = """<html>
<head>
<title>Performance Details</title>
</head>
<style>
table, th, td {border}
</style>
<body>
<h2><b>Deployed Model:</b>{ModelString}</h2>
<br/>
<table style="width:50%">
<tr>
<td>No of Prediction</td>
<td>{NoOfPrediction}</td>
</tr>
<tr>
<td>No of GroundTruth</td>
<td>{NoOfGroundTruth}</td>
</tr>
</table>
<br/>
<table style="width:100%">
<tr>
<th>Score Type</th>
<th>Train Score</th>
<th>Test Score</th>
<th>Production Score</th>
</tr>
<tr>
<td>{Scoring_Creteria}</td>
<td>{train_score}</td>
<td>{test_score}</td>
<td>{current_score}</td>
</tr>
</table>
<br/>
<br/>
<img src="data:image/png;base64,{newDataDrift}" alt="" >
</body>
</html>
""".format(border='{border: 1px solid black;}',ModelString=ModelString,Scoring_Creteria=Scoring_Creteria,NoOfPrediction=NoOfPrediction,NoOfGroundTruth=NoOfGroundTruth,train_score=train_score,test_score=test_score,current_score=current_score,newDataDrift=inputdistribution)
			elif (usecase.lower() == config_input['targetPath'].lower()) and (operation.lower() == 'logs'):    
				self.send_header('Content-Type', 'text/plain')        
				self.end_headers()                           
				log_file = self.targetPath/IOFiles['log']                
				if log_file.exists():
					with open(log_file) as f:
						msg = f.read()                
					f.close()
				else:        
					raise ValueError(f'Log Details not found: {log_file}')            
			else:
				self.send_header('Content-Type', 'application/json')        
				self.end_headers()            
				features = meta_data['load_data']['selected_features']
				bodydes='['
				for x in features:
					if bodydes != '[':
						bodydes = bodydes+','
					bodydes = bodydes+'{"'+x+'":"value"}'	
				bodydes+=']'
				urltext = '/AION/'+config_input['targetPath']+'/predict'
				urltextgth='/AION/'+config_input['targetPath']+'/groundtruth'
				urltextproduction='/AION/'+config_input['targetPath']+'/metrices'
				msg="""
Version:{modelversion}
RunNo: {runNo}
URL for Prediction
==================
URL:{url}
RequestType: POST
Content-Type=application/json
Body: {displaymsg}
Output: prediction,probability(if Applicable),remarks corresponding to each row.

URL for GroundTruth
===================
URL:{urltextgth}
RequestType: POST
Content-Type=application/json
Note: Make Sure that one feature (ID) should be unique in both predict and groundtruth. Otherwise outputdrift will not work  

URL for Model In Production Analysis
====================================
URL:{urltextproduction}
RequestType: GET
Content-Type=application/json

""".format(modelversion=config_input['modelVersion'],runNo=config_input['deployedRunNo'],url=urltext,urltextgth=urltextgth,urltextproduction=urltextproduction,displaymsg=bodydes)        
			self.wfile.write(msg.encode())        
		else:        
			self.send_response(403)        
			self.send_header('Content-Type', 'application/json')        
			self.end_headers()        
		return        
        
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):        
	allow_reuse_address = True        
        
	def shutdown(self):        
		self.socket.close()        
		HTTPServer.shutdown(self)        
        
class file_status():
	
	def __init__(self, reload_function, params, file, logger):
		self.files_status = {}
		self.initializeFileStatus(file)
		self.reload_function = reload_function
		self.params = params
		self.logger = logger
		
	def initializeFileStatus(self, file):
		self.files_status = {'path': file, 'time':file.stat().st_mtime}

	def is_file_changed(self):
		if self.files_status['path'].stat().st_mtime > self.files_status['time']:
			self.files_status['time'] = self.files_status['path'].stat().st_mtime
			return True
		return False
		
	def run(self):
		global config_input    
		while( True):
			time.sleep(30)
			if self.is_file_changed():
				production_details = targetPath/IOFiles['production']
				if not production_details.exists():        
					raise ValueError(f'Model in production details does not exist')
				productionmodel = read_json(production_details)
				config_file = Path(__file__).parent/'config.json'        
				if not Path(config_file).exists():        
					raise ValueError(f'Config file is missing: {config_file}')        
				config_input = read_json(config_file)				
				config_input['deployedModel'] =  productionmodel['Model']
				config_input['deployedRunNo'] =  productionmodel['runNo']
				self.logger.info('Model changed Reloading.....')
				self.logger.info(f'Model: {config_input["deployedModel"]}')				
				self.logger.info(f'Version: {str(config_input["modelVersion"])}')
				self.logger.info(f'runNo: {str(config_input["deployedRunNo"])}')
				self.reload_function(config_input)
			
class SimpleHttpServer():        
	def __init__(self, ip, port, model_file_path,reload_function,params, logger):        
		self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)        
		self.status_checker = file_status( reload_function, params, model_file_path, logger)
		
	def start(self):        
		self.server_thread = threading.Thread(target=self.server.serve_forever)        
		self.server_thread.daemon = True        
		self.server_thread.start()        
		self.status_thread = threading.Thread(target=self.status_checker.run)        
		self.status_thread.start()        
		
	def waitForThread(self):        
		self.server_thread.join()        
		self.status_thread.join()        
		
	def stop(self):        
		self.server.shutdown()        
		self.waitForThread()        
        
if __name__=='__main__':        
	parser = argparse.ArgumentParser(description='HTTP Server')        
	parser.add_argument('-ip','--ipAddress', help='HTTP Server IP')        
	parser.add_argument('-pn','--portNo', type=int, help='Listening port for HTTP Server')        
	args = parser.parse_args()        
	config_file = Path(__file__).parent/'config.json'        
	if not Path(config_file).exists():        
		raise ValueError(f'Config file is missing: {config_file}')        
	config = read_json(config_file)        
	if args.ipAddress:        
		config['ipAddress'] = args.ipAddress        
	if args.portNo:        
		config['portNo'] = args.portNo        
	targetPath = Path('aion')/config['targetPath']        
	if not targetPath.exists():        
		raise ValueError(f'targetPath does not exist')
	production_details = targetPath/IOFiles['production']
	if not production_details.exists():        
		raise ValueError(f'Model in production details does not exist')
	productionmodel = read_json(production_details)
	config['deployedModel'] =  productionmodel['Model']
	config['deployedRunNo'] =  productionmodel['runNo']	
	#server = SimpleHttpServer(config['ipAddress'],int(config['portNo']))        
	config_input = config        
	logging.basicConfig(filename= Path(targetPath)/IOFiles['log'], filemode='a', format='%(asctime)s %(name)s- %(message)s', level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')                    
	logger = logging.getLogger(Path(__file__).parent.name)                    
	deployobj = deploy(config_input, logger)
	server = SimpleHttpServer(config['ipAddress'],int(config['portNo']),targetPath/IOFiles['production'],deployobj.initialize,config_input, logger)
	logger.info('HTTP Server Running...........')
	logger.info(f"IP Address: {config['ipAddress']}")
	logger.info(f"Port No.: {config['portNo']}")
	print('HTTP Server Running...........')  
	print('For Prediction')
	print('================')
	print('Request Type: Post')
	print('Content-Type: application/json')	
	print('URL: /AION/'+config['targetPath']+'/predict')	
	print('\nFor GroundTruth')
	print('================')
	print('Request Type: Post')
	print('Content-Type: application/json')	
	print('URL: /AION/'+config['targetPath']+'/groundtruth')	
	print('\nFor Help')
	print('================')
	print('Request Type: Get')
	print('Content-Type: application/json')	
	print('URL: /AION/'+config['targetPath']+'/help')	
	print('\nFor Model In Production Analysis')
	print('================')
	print('Request Type: Get')
	print('Content-Type: application/json')	
	print('URL: /AION/'+config['targetPath']+'/metrices')    
	server.start()        
	server.waitForThread()
