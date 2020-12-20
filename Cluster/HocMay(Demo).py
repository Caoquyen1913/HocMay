# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 09:21:06 2020

@author: HQ
"""

import flask
from flask import jsonify
import pandas as pd
import numpy as np
#from scipy.cluster.hierarchy import linkage
from sklearn.cluster import AgglomerativeClustering
from datetime import datetime
import requests 
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


now = datetime.now() # current date and time
date=now
timestartdefault=datetime.now()
timerun=datetime.now()
timeafter=datetime.now()
plustime=0
TempA=""
datatemp=""
A=0
y_hc=0
cluster_number=1
size=1000
soluongdon=0
timesloop=5
scheduler = BackgroundScheduler()
finaljson=[]
ulrpage="http://servertlcn.herokuapp.com"
tstart="19:00"
tend="20:00"
global statusServer
statusServer=False
#phan cluster dua theo so cluster
def Cluster(A):
    if(len(A)>1):
        hc=AgglomerativeClustering(n_clusters=cluster_number,affinity='euclidean', linkage='ward')
        return hc.fit_predict(A)

def getSizeSanPhamByIdDonHang(id):
    url=ulrpage+"/dssanpham/"+str(id)+"/donhang"
    r=requests.get(url)
    data=r.json()
    soluong=0
    index=data['data']
    for i in range(0,len(index)):   
        soluong+=float(index[i]['SanPham']['KichCo'])
    return soluong

def createjson():
    a='{"data": ['
    for n in range(0,cluster_number):
        if(n<cluster_number-1):
            a+='[],'
        else: a+='[]'
    a+=']}'
    return json.loads(a)

#xuat cluster thanh json 
def outputdatatojson():
    data=createjson()
    outputdata=data['data']
    cluster=0
    while(cluster<cluster_number):
        for j in range(0,len(A[y_hc==cluster])):
                for i in range(0,len(TempA)):
                    if(A[y_hc==cluster][j][0]==TempA[i][0] and A[y_hc==cluster][j][1]==TempA[i][1]):
                        outputdata[cluster].append(datatemp[i])
        cluster+=1
    return outputdata
def getjsontoarray():
    X = np.array([[106,10]])
    url = ulrpage+"/diachi/search"
    r = requests.post(url, json={
        "id":1,
        "timerange":{
                "timeStart":"12/10/2020 "+tstart,
                "timeEnd":"12/10/2020 "+tend  
                }
        })
    data=r.json()
    for i in range(0,len(data['data'])):
        X=np.concatenate([X,[[float(data['data'][i]['KinhDo']),float(data['data'][i]['ViDo'])]]])
    X=np.delete(X,0,axis = 0)
    return X

def getalldata():
    url = ulrpage+"/diachi/search"
    r = requests.post(url, json={
        "id":1,
        "timerange":{
                "timeStart":"12/10/2020 "+tstart,
                "timeEnd":"12/10/2020 "+tend   
                }
})
    return r.json()

def checkSizeOrder(json):
    clusternumber=cluster_number
    for i in range(0,cluster_number):
        soluong=0
        for j in range(0,len(json[i])):
            soluong+=getSizeSanPhamByIdDonHang(json[i][j]['DonhangId'])
            
        if soluong>size:
            clusternumber+=1
    if(soluongdon<clusternumber): return True
    if(clusternumber==cluster_number): return True
    else: return False 
def fplustime(timerun, plustime):
    return timerun.replace(day=timerun.day, 
                           hour=timerun.hour+plustime, 
                           minute=timerun.minute, 
                           second=timerun.second, 
                           microsecond=timerun.microsecond)


def setjsontime(timerun, timeafter):
    return {
            "id":1,
            "timerange":{
                    "timeStart":str(timerun.strftime("%m/%d/%Y %H:%M")),
                    "timeEnd":str(timeafter.strftime("%m/%d/%Y %H:%M")) 
                    }
            }
            
def gettime(timestart,pltime,plday,timesloops):
    global timestartdefault
    timestartdefault=datetime.strptime(str(date.strftime("%m/%d/%Y")+" " +timestart),'%m/%d/%Y %H:%M')
    global plustime
    plustime=int(pltime)
    global plusday
    plusday=int(plday)
    global timesloop
    timesloop=int(timesloops)

def checkresult(data):
    if(data['result']=='ok'):
        return True
    return False

def fplusday(date,plusday):
    date=date.replace(day=date.day+plusday)
    return date.strftime("%m/%d/%Y")
plustime=2
plusday=0

#khoảng thời gian giao hàng

#timerun=timeafter
def runcluster():
    data=getalldata()
    if(checkresult(data)==False):
        json=createjson()
        outputdata=json['data']
        del outputdata[1]
        del outputdata[0]
        return outputdata,0
    else:
        global A
        A=getjsontoarray()
        global soluongdon
        soluongdon=len(A)
        global TempA
        TempA=getjsontoarray()
        if(len(A)<2):
            json=createjson()
            outputdata=json['data']
            outputdata[0].append(data['data'][0])
            del outputdata[1]
            return outputdata,0
        else:
            global y_hc
            y_hc=Cluster(A)
            global datatemp
            datatemp=data['data']
            j=outputdatatojson()
            return j,1

def getlapchuoidonhang(j):
    url =ulrpage+"/lapchuoidonhang/donhang" 
    r = requests.post(url, json={'timeStart':tstart,
                                 'data':j})
    data=r.json()
    return data['result']
    #return data
def Motnhanh():
    b='{"data": []}'
    b=json.loads(b)
    alldata=getalldata()
    global soluongdon
    soluongdon=len(alldata['data'])
    b=b['data']
    b.append(alldata['data'])
    return b
def runall():
    b=Motnhanh()
    global cluster_number
    if(checkSizeOrder(b) == True):
        return b
    else:
        cluster_number=2
        j,status=runcluster()
        if(status==0): return j
        else:
            while checkSizeOrder(j) == False:
                cluster_number+=1
                j,status=runcluster()
        global finaljson
        finaljson=j
        return j

#timestartdefault=datetime.strptime("11/03/2020"+" 8:00",'%m/%d/%Y %H:%M')
    
  
def loopHourInDay():
    timerun=timestartdefault
    timeafter = fplustime(timerun,plustime)
    solan=0
    while solan < timesloop:
        j=runall()
        """
        check=getlapchuoidonhang(j)
        #print(timerun.strftime("%m/%d/%Y %H:%M"))
        #print(timeafter.strftime("%m/%d/%Y %H:%M"))
        if(check=="ok" or check=="fail"):
            timerun=timeafter
            timeafter = fplustime(timerun,plustime)
            solan+=1
        """

"""
data=getalldata()
A=getjsontoarray()
soluongdon=len(A)
TempA=getjsontoarray()
y_hc=Cluster(A)
datatemp=data['data']
dataa=createjson()
j=outputdatatojson()
soluong=getSizeSanPhamByIdDonHang(j[0][1]['DonhangId'])
check=checkSizeOrder(j)
print(soluong)

print(A)
print(A[y_hc==0,0],A[y_hc==0,1])
print(A[y_hc==1,0],A[y_hc==1,1])

print(json[i][j]['DonhangId'])
"""
    #j,status=runcluster()
# print(getalldata())
j=runall()
print("so nhanh: " + str(cluster_number))
# print(j)
# # app = flask.Flask(__name__)
check=getlapchuoidonhang(j)
print(check)