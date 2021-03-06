#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  2 13:42:34 2020

Earthquake phase pick generator

@author: amt
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from scipy.interpolate import RegularGridInterpolator
#import datetime

def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km
    dlat = np.radians(lat2-lat1)
    dlon = np.radians(lon2-lon1)
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
        * np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    d = radius * c
    return d

testing=0
if testing:
    # # SO WE CAN REPRODUCE
    np.random.seed(42)
    # WANT SOME PLOTS
    plots=1
else:
    plots=0

# LOAD STATION INFORMATION
stas=pd.read_csv('station_master_with_elev.dat',delimiter=' ', usecols=(0,1,2,7,8,9), names=["Network","Station","Channel","Latitude","Longitude","Elevation"])
stas=stas.drop_duplicates(subset ="Station")
# Horizontals: BHE,BHN,EHE,EHN,HHE,HHN,EH1,EH2,BH3,HH3
# Verticals:BHZ,EHZ,HHZ
# BOTH:BH1,BH2,HH1,HH2

# LOAD VELOCITY MODELS and CREATE INTERP FUNCTIONS
names=['c3', 'e3', 'j1', 'k3', 'n3', 'p4', 's4', 'O0', 'gil7'] 
for name in names:
    ttdists, ttdepths, ttelevs, ptt_all, stt_all = pickle.load( open(name+'.pkl', 'rb' ) )
    if name=='c3':
        c3p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        c3s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)
    elif name=='e3':
        e3p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        e3s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)    
    elif name=='j1':
        j1p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        j1s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None) 
    elif name=='k3':
        k3p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        k3s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)    
    elif name=='n3':
        n3p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        n3s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)   
    elif name=='p4':
        p4p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        p4s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)    
    elif name=='s4':
        s4p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        s4s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None)
    elif name=='O0':
        O0p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        O0s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None) 
    else:
        gil7p=RegularGridInterpolator((ttdepths, ttdists, ttelevs), ptt_all, bounds_error=False, fill_value=None)
        gil7s=RegularGridInterpolator((ttdepths, ttdists, ttelevs), stt_all, bounds_error=False, fill_value=None) 
        
# SYNTHETIC SOURCE LOCATIONS
lat=np.linspace(39,51.5,1000000)# want uniform geographic sampling
latp=np.sin(lat*np.pi/180)
latp=latp/np.sum(latp)

# # do the shifts and make batches
def my_data_generator(lat,latp,c3p,c3s,e3p,e3s,j1p,j1s,k3p,k3s,n3p,n3s,p4p,p4s,s4p,s4s,O0p,O0s,gil7p,gil7s,batch_length=10000,duration=7,ri=1800,phases=False):
    while True:
        #defines coefficients for gmm
        a1,a2,a3,a4,a5=-1.96494392,  0.89260686, -0.12470324, -1.43533434, -0.00561138
        outfile=np.zeros((0,12))
        count=0
        ps=np.zeros((len(stas)))
        ss=np.zeros((len(stas)))
        sourceepoch=0
        length_in_seconds=86400*duration # one day
        while sourceepoch < length_in_seconds: 
            #print(sourceepoch)
            sourcelon=np.random.uniform(-132.5,-116.5)
            sourcelat=np.random.choice(lat,p=latp)
            sourcedepth=np.random.uniform(0,100)
            sourcemag=np.random.uniform(1,6) # np.random.exponential(np.log(10)*1)
            dt=np.random.exponential(ri) #(11564)
            if len(outfile)>0:
                sourceepoch=dt+sourceepoch
            else:
                sourceepoch=dt    
            # print("Trying earthquake # "+str(len(np.unique(outfile[:,9]))+1))
            # print(str(sourceepoch))
            dists=distance([sourcelat,sourcelon], [stas['Latitude'].values,stas['Longitude'].values])
            rhyp=np.sqrt(dists**2+sourcedepth**2) # dist from rupture in km
            gm=np.exp(a1 + a2*sourcemag + a3*(8.5-sourcemag)**2. + a4*np.log(rhyp) + a5*rhyp)
            # if plots and np.max(gm)>1e-06: # make sure recorded at at least one station
            #     fig,ax=plt.subplots(nrows=1,ncols=3,figsize=(16,9))
            #     ax[0].plot(sourcelon,sourcelat,'ko',markersize=12)
            #     im0=ax[0].scatter(stas['Longitude'],stas['Latitude'],s=25,c=dists,marker='^')
            #     fig.colorbar(im0, ax=ax[0])
            #     ax[1].plot(sourcelon,sourcelat,'ko',markersize=12)
            #     im1=ax[1].scatter(stas['Longitude'],stas['Latitude'],s=25,c=rhyp,marker='^')
            #     fig.colorbar(im1, ax=ax[1])
            #     ax[2].plot(sourcelon,sourcelat,'ko',markersize=12)
            #     im2=ax[2].scatter(stas['Longitude'],stas['Latitude'],s=25,c=gm,marker='^')
            #     fig.colorbar(im2, ax=ax[2])
            if np.max(gm)>1e-05: # if ground motion is recordable
                for ii in range(len(stas)):       
                    if gm[ii]>=1e-05 and dists[ii]/300 < 0.375*np.random.uniform(): # if ground motion at station is recordable and adding a random drop term in here to account for missing/bad stations
                        dist=dists[ii]
                        elev=stas.iloc[ii]['Elevation']/1000
                        if sourcelon<=-125:
                            #mod='j1'
                            ps[ii]=np.float(j1p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(j1s((sourcedepth+elev,dist,elev)))
                        elif sourcelat<=42:
                            #mod='gil7'
                            ps[ii]=np.float(gil7p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(gil7s((sourcedepth+elev,dist,elev)))
                        elif sourcelat>42 and sourcelat<=43:
                            #mod='k3'
                            ps[ii]=np.float(k3p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(k3s((sourcedepth+elev,dist,elev)))
                        elif sourcelat>43 and sourcelat<=45.5:
                            #mod='O0'
                            ps[ii]=np.float(O0p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(O0s((sourcedepth+elev,dist,elev)))
                        elif sourcelat>45.5 and sourcelat<=47 and sourcelon>-120.5:  
                            #mod='e3'
                            ps[ii]=np.float(e3p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(e3s((sourcedepth+elev,dist,elev)))
                        elif sourcelat>47 and sourcelon>-120.5:  
                            #mod='n3'
                            ps[ii]=np.float(n3p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(n3s((sourcedepth+elev,dist,elev)))
                        elif sourcelon>-122.69 and sourcelon<=-121.69 and sourcelat>45.69 and sourcelat<=46.69:
                            #mod='s4'
                            ps[ii]=np.float(s4p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(s4s((sourcedepth+elev,dist,elev)))
                        elif sourcelon>-122.5:
                            #mod='c3'
                            ps[ii]=np.float(c3p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(c3s((sourcedepth+elev,dist,elev)))
                        else:
                            #mod='p4'
                            ps[ii]=np.float(p4p((sourcedepth+elev,dist,elev)))
                            ss[ii]=np.float(p4s((sourcedepth+elev,dist,elev)))
                        if ps[ii]>0:
                            # Pick Lon, Pick Lat, Pick Elev, Assigned P or S, Pick Time, Source Longitude, Source Latitude, Source Depth, Source Magnitude, Travel Time, True P or S, EQ or Noise])
                            evoutfile=np.zeros((2,12))
                            evoutfile[0,0]=stas.iloc[ii]['Longitude']
                            evoutfile[0,1]=stas.iloc[ii]['Latitude']
                            evoutfile[0,2]=stas.iloc[ii]['Elevation']
                            evoutfile[0,3]=1
                            evoutfile[0,4]=ps[ii]+sourceepoch #+np.random.normal(0, 0.05, 1000)
                            evoutfile[0,5]=sourcelon
                            evoutfile[0,6]=sourcelat
                            evoutfile[0,7]=sourcedepth
                            evoutfile[0,8]=sourcemag
                            evoutfile[0,9]=ps[ii]
                            evoutfile[0,10]=1
                            evoutfile[0,11]=1
                            evoutfile[1,0]=stas.iloc[ii]['Longitude']
                            evoutfile[1,1]=stas.iloc[ii]['Latitude']
                            evoutfile[1,2]=stas.iloc[ii]['Elevation']
                            evoutfile[1,3]=0
                            evoutfile[1,4]=ss[ii]+sourceepoch #+np.random.normal(0, 0.05, 1000)
                            evoutfile[1,5]=sourcelon
                            evoutfile[1,6]=sourcelat
                            evoutfile[1,7]=sourcedepth
                            evoutfile[1,8]=sourcemag
                            evoutfile[1,9]=ss[ii]
                            evoutfile[1,10]=0
                            evoutfile[1,11]=1
                            # print('Event picks ='+str(len(evoutfile)))
                            tmp=np.random.uniform() # make a random variable
                            if tmp < 0.1: # drop the P
                                outfile=np.append(outfile,evoutfile[1,:].reshape(1,-1),axis=0)
                            elif tmp >= 0.1 and tmp < 0.2: # drop the S
                                outfile=np.append(outfile,evoutfile[0,:].reshape(1,-1),axis=0)
                            elif tmp >= 0.2 and tmp < 0.3: # make the S a P
                                evoutfile[1,3]=1
                                outfile=np.append(outfile,evoutfile,axis=0)
                            elif tmp >= 0.3 and tmp < 0.4: # make the P a S
                                evoutfile[0,3]=0
                                outfile=np.append(outfile,evoutfile,axis=0)
                            else:
                                outfile=np.append(outfile,evoutfile,axis=0)

        # If too many picks, adjust
        if len(outfile)>batch_length:
            # print("before="+str(len(outfile)))
            deck = list(range(1, len(outfile)))
            np.random.shuffle(deck)
            deck=np.sort(deck[:np.random.randint(int(0.4*batch_length//2),int(0.65*batch_length//2))])
            outfile=outfile[deck,:]

        # this removes events that have less than 6 picks
        print("Pre cull length is:"+str(len(outfile)))
        depths=np.unique(outfile[:,7])
        depths=depths[depths!=0]
        indstoremove=[]
        for depth in depths:
            print(depth)
            inds=np.where(outfile[:,7]==depth)[0]
            print(indstoremove)
            if len(inds)<4:    
                indstoremove.extend(inds)
        print("Culling "+str(len(np.array(indstoremove))))
        if len(indstoremove)>0:
            outfile=np.delete(outfile,np.array(indstoremove),0)
        print("Post cull length is:"+str(len(outfile)))

        print("{:.2%} of picks are from events.".format(len(outfile)/batch_length))
        # ADD SYNTHETIC NOISE    
        outfilen=np.zeros((batch_length-len(outfile),12))
        count=0
        while count < len(outfilen):
            ii=np.random.choice(np.arange(len(stas)))
            outfilen[count,0]=stas.iloc[ii]['Longitude']
            outfilen[count,1]=stas.iloc[ii]['Latitude']
            outfilen[count,2]=stas.iloc[ii]['Elevation']
            outfilen[count,3]=np.random.choice([0,1])
            outfilen[count,4]=np.random.uniform(low=0,high=np.max([np.max(outfile[:,4]),length_in_seconds]))
            outfilen[count,5]=0
            outfilen[count,6]=0
            outfilen[count,7]=0
            outfilen[count,8]=0
            outfilen[count,9]=0
            outfilen[count,10]=0
            outfilen[count,11]=0
            count+=1
                 
        # COMBINE EQS AND NOISE
        allout=np.concatenate((outfile,outfilen))
        inds=np.argsort(allout[:,4])
        allout=allout[inds,:]  
        allout=allout[np.newaxis,:,:]
        # print(allout.shape)
        if allout.shape[1]>batch_length:
            allout=allout[:,:batch_length,:]
        #     print("clip")
        else:
            allout=np.append(allout,np.zeros((1,batch_length-allout.shape[1],12)),axis=1)
        #    print("add")
        
        # DROP TRUE PHASES IF THEY ARENT NEEDED
        if not phases:
            allout=np.delete(allout, 10, 2)
        else:
            allout=allout[:, :, np.r_[0:5,10:12]]
            
        if plots:
            # PLOT RESULTS
            pind=np.where(allout[0,:,3]==0)
            sind=np.where(allout[0,:,3]==1)
            # Pick Lon, Pick Lat, Pick Elev, P or S, Pick Time, Source Longitude, Source Latitude, Source Depth, Source Magnitude, Source Time, noise or sig])
            plt.figure()
            plt.scatter(allout[0,pind,4],allout[0,pind,1],s=25,c=allout[0,pind,-2],marker='+')
            plt.scatter(allout[0,sind,4],allout[0,sind,1],s=25,c=allout[0,sind,-2],marker='x')
            plt.plot(allout[0,np.where(allout[0,:,-1]!=0),4]-allout[0,np.where(allout[0,:,-1]!=0),9],allout[0,np.where(allout[0,:,-1]!=0),-5],'ko')
            plt.ylim((39,51.5))
            
            sourceepoch=outfile[:,4]-outfile[:,9]
            unisou=np.unique(sourceepoch)
            bc=np.loadtxt('bc.outline')
            ca=np.loadtxt('ca.outline')
            ore=np.loadtxt('or.outline')
            wa=np.loadtxt('wa.outline')
            ida=np.loadtxt('id.outline')
            nv=np.loadtxt('nv.outline')
            for ind in range(10): #len(unisou)):
                inds=np.where(sourceepoch==unisou[ind])
                tmpsource=outfile[inds,:][0,:,:]
                plt.figure(figsize=(7,9))
                # Pick Lon, Pick Lat, Pick Elev, P or S, Pick Time, Source Longitude, Source Latitude, Source Depth, Source Magnitude, Source Time])
                plt.plot(tmpsource[0,5],tmpsource[0,6],'ko',markersize=5)
                plt.scatter(tmpsource[:,0],tmpsource[:,1],s=25,c=tmpsource[:,9],marker='^',vmin=0,vmax=50)
                plt.plot(wa[:,1],wa[:,0])
                plt.plot(bc[:,1],bc[:,0])
                plt.plot(ore[:,1],ore[:,0])
                plt.plot(ca[:,1],ca[:,0])
                plt.plot(ida[:,1],ida[:,0])
                plt.plot(nv[:,1],nv[:,0])
                plt.title('D'+str(np.round(10*tmpsource[0,7])/10)+'-M'+str(np.round(10*tmpsource[0,8])/10))
                plt.colorbar()

        yield(allout)                

# generate batch data
def get_generator():
    return my_data_generator(lat,latp,c3p,c3s,e3p,e3s,j1p,j1s,k3p,k3s,n3p,n3s,p4p,p4s,s4p,s4s,O0p,O0s,gil7p,gil7s,batch_length=10000)

# generate batch data
def get_small_generator():
    return my_data_generator(lat,latp,c3p,c3s,e3p,e3s,j1p,j1s,k3p,k3s,n3p,n3s,p4p,p4s,s4p,s4s,O0p,O0s,gil7p,gil7s,batch_length=500, duration=1, ri=5000)

# generate batch data
def get_phases_generator():
    return my_data_generator(lat,latp,c3p,c3s,e3p,e3s,j1p,j1s,k3p,k3s,n3p,n3s,p4p,p4s,s4p,s4s,O0p,O0s,gil7p,gil7s,batch_length=500, duration=1, ri=5000, phases=True)

if __name__=="__main__":
    my_data=get_small_generator()
    x=next(my_data)
    depths=np.unique(x[0,:,7])
    depths=depths[depths!=0]
    for depth in depths:
        inds=np.where(x[0,:,7]==depth)[0]
        print(len(inds))
