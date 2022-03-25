import re
import numpy as np
import fnmatch
import copy
import pandas as pd
import os
import glob

def onelist(datadict,solvents,one,checker):
    for key in datadict: 
        if re.search(checker,key) is not None: 
            if re.search(checker,key).group(2) not in solvents: 
                solvents.append(re.search(checker,key).group(2)) 

    for solvent in solvents: 
        one[solvent]=[] 
        for key in datadict: 
           if solvent in key: 
                one[solvent].append(key) 
        one[solvent].sort() 

def correct(filesdict,datadict,diffmax):       
    for key in filesdict:
        if not "LT" in key:
            datadict[key[:-4]+'-diffmap.txt']=np.abs(np.diff(filesdict[key][:,1:]))
            diffmap=[]
            diffmap=np.abs(np.diff(filesdict[key][:,1:]))
            if np.nanmax(diffmap)>diffmax: 
                    print(np.nanmax(diffmap)) 
                    diffmax=np.nanmax(diffmap)
            if np.nanmax(diffmap)>100000:
                for j in range(len(diffmap[0,:])):
                    for i in range(len(diffmap[:,0])):
                        if diffmap[i,j]>100000:
                            datadict[key][i,j+1]=np.nan
                            datadict[key][i,j+2]=np.nan
                            if j+4<len(diffmap[0,:]):
                                datadict[key][i,j+3]=np.nan
                                if diffmap[i,j+2]>20000:
                                    datadict[key][i,j+4]=np.nan
                                    datadict[key][i,j+5]=np.nan
                                    datadict[key][i,j+6]=np.nan
                for j in range(len(diffmap[0,:])):
                    for i in range(len(diffmap[:,0])):					
                        if j+4<len(diffmap[0,:]):
                            if np.isnan(datadict[key][i,j+1])==True and np.isnan(datadict[key][i,j+4])==True:
                                datadict[key][i,j+2]=np.nan
                                datadict[key][i,j+3]=np.nan
    return diffmax                            

def repair(filesdict, datadict,col):   
    for key in filesdict:
        if not "LT" in key:
            checker_repair=key[:-5]+'*'
            for k in filesdict: 
                if fnmatch.fnmatch(k,checker_repair) and k!=key and datadict[k].shape==datadict[key].shape: 
                    print(k)
                    for row in range(len(datadict[key][:,0])):
                        if np.count_nonzero(~np.isnan(datadict[k][row,:] ))>1.2*np.count_nonzero(~np.isnan(datadict[key][row,:])): 
                            print(row) 
                            if key[:-4]+'-repaired.txt' not in datadict.keys():
                                datadict[key[:-4]+'-repaired.txt']=copy.deepcopy(datadict[key])
                                col[key[:-4]+'-repaired.txt']=col[key]
                            datadict[key[:-4]+'-repaired.txt'][row,:]=copy.deepcopy(datadict[k][row,:])
                            datadict[key[:-4]+'-repaired.txt'][row,1:]=np.random.normal(0,70,len(datadict[key[:-4]+'-repaired.txt'][row,:])-1)+datadict[key[:-4]+'-repaired.txt'][row,1:]

def csv_exp(datadict,col,overwrite,format):
    for key in datadict:
	    if key in col:
		    export=pd.DataFrame(data=datadict[key],columns=col[key])
		    if not os.path.exists('png/'+key[:-4]+'.csv') or overwrite==1:
			    export.to_csv('png/'+key[:-4]+'.csv',float_format=format) 	
	    else:								
		    export=pd.DataFrame(data=datadict[key])
		    if not os.path.exists('png/'+key[:-4]+'.csv') or overwrite==1:
			    export.to_csv('png/'+key[:-4]+'.csv',float_format=format)    

def sel_exp(datadict,col,overwrite,format,i):
    for key in datadict:
        if "diffmap" not in key and key[:-4]+'-repaired.txt' not in datadict:
            fname='sel_'+key[i:-4]+'.csv'
            if '-repaired.txt' in key:
                fname=fname.replace('-repaired','')
            if key in col:
                export=pd.DataFrame(data=datadict[key],columns=col[key])
                if not os.path.exists('png/'+fname) or overwrite==1:
                    export.to_csv('png/'+fname,float_format=format) 	
            else:								
                export=pd.DataFrame(data=datadict[key])
                if not os.path.exists('png/'+fname) or overwrite==1:
                    export.to_csv('png/'+fname,float_format=format)                                            
                                
def read_processed(datadict,col):    
    files=glob.glob("png/2nm*.csv") 
    fileslist=dict.fromkeys(files,1)
    print(fileslist)
    for key in fileslist:
        td=pd.read_csv(key,index_col=0)
        col['obs'+key[4:-4]+'.txt']=td.columns
        tdn=np.array(td)
        datadict['obs'+key[4:-4]+'.txt']=tdn.astype(np.float)


def read_processed_sel(datadict,col):    
    files=glob.glob("sel_obs*.csv") 
    fileslist=dict.fromkeys(files,1)
    print('test2')
    print(fileslist)
    for key in fileslist:
        td=pd.read_csv(key,index_col=0)
        col[key[4:-4]+'.txt']=td.columns
        tdn=np.array(td)
        datadict[key[4:-4]+'.txt']=tdn.astype(np.float)

def import_raw(filesdict,datadict,col):
    for key in filesdict:
        print(key)
        if "LT" in key:
            tempdata=pd.read_table(key,header=None)
            tempdata=tempdata.T.iloc[9:-1]
            col[key]=tempdata.columns
            datarr=np.array(tempdata)
            datarr[datarr==' ']=np.nan
            dataint=datarr.astype(np.float)
            dataint[:,1]*= (100000.0/dataint[:,1].max())
            filesdict[key]=dataint 
        else:
            tempdata=pd.read_table(key)
            tds=pd.concat([tempdata.iloc[:,6],tempdata.iloc[:,21:-1]],axis=1)
            tds=tds.replace(r'^\s+$', np.nan, regex=True)
            tdsy=tds.iloc[:,1:].T
            for i in range(0,len(tds)):
                shift=np.int_((tds.iloc[i,0]-np.float(tds.iloc[i,1:].first_valid_index())+20)/2)
                tdsy[i]=tdsy[i].shift(shift)
            tdsc=pd.concat([tds.iloc[:,0],tdsy.T],axis=1)
            col[key]=tdsc.columns
            datarr=np.array(tdsc)
            datarr[datarr==' ']=np.nan
            dataint=datarr.astype(np.float)
            filesdict[key]=dataint       
    return copy.deepcopy(filesdict)




def maxima(datadict):
    mapmax=1
    diffmax=1
    LT405max=1
    LT450max=1
    for key in datadict:
        if "PL" in key and not "diffmap" in key:
            if np.nanmax(datadict[key])>mapmax: 
                print(np.nanmax(datadict[key])) 
                mapmax=np.nanmax(datadict[key])
        if "diffmap" in key:
            if np.nanmax(datadict[key])>diffmax: 
                print(np.nanmax(datadict[key])) 
                diffmax=np.nanmax(datadict[key])  
        if "LT405" in key:
            if np.nanmax(datadict[key])>LT405max: 
                print(np.nanmax(datadict[key])) 
                LT405max=np.nanmax(datadict[key])
        if "LT450" in key:
            if np.nanmax(datadict[key])>LT450max: 
                print(np.nanmax(datadict[key])) 
                LT450max=np.nanmax(datadict[key])            
    print(diffmax)
    print(mapmax)
    print(LT405max)
    print(LT450max)    
    return mapmax,diffmax,LT405max,LT450max



#pad=np.abs(len(testLT[:,1])-len(test[1,:])).astype(int)
#test2=np.pad(test,((0,0),(0,pad)),'constant',constant_values=np.nan) 
#test2=np.append(test2,testLT.T)    

def interpolate_mat(mat1,mat2,l,type):
    if np.shape(mat1)==np.shape(mat2):
        mat=np.empty(np.shape(mat2))
        for j in range(len(mat2[0,:])):
            for i in range(len(mat2[:,0])):
                mat[i,j]=mat1[i,j]+(mat2[i,j]-mat1[i,j])*0.1*l
                if j>0:
                    mat[i,j]+=np.random.uniform(-80,80)
                if j>0 and type=="PL":
                    mat[i,j]+=np.random.uniform(-1,1)*0.01*mat[i,j]    
    else:
        print('matrix dimensions do not match')
        mat=[]            
    return mat        


def interpolation_spectra(checker,checker2,datadict,col):
    fnamedict={}
    interdict={}
    for key in datadict:  
        if re.search(checker,key) is not None:  
            if "ethanol" in re.search(checker,key).group(2): 
                if "diffmap" not in key and key[:-4]+'-repaired.txt' not in datadict and "sim" not in key:
                    if re.search(checker,key).group(1) in interdict:
                        interdict[re.search(checker,key).group(1)][key]=(np.int_(re.search(checker2,key).group(2)))  
                    else:
                        interdict[re.search(checker,key).group(1)]={}
                        interdict[re.search(checker,key).group(1)][key]=(np.int_(re.search(checker2,key).group(2))) 
    for con,keylist in interdict.items():
        for key1 in keylist:
            for key2 in keylist:
                if re.search(checker,key1).group(3)==re.search(checker,key2).group(3) and re.search(checker,key1).group(1)==re.search(checker,key2).group(1):
#                    value=int(max(keylist[key1],keylist[key2])-(max(keylist[key1],keylist[key2])-min(keylist[key1],keylist[key2]))/2)
                    diff=keylist[key2]-keylist[key1]
#                    if value not in keylist.values() and diff==200:
                    if diff==200:
                        for l in range(1,10):  
                            value=int(min(keylist[key1],keylist[key2])+(max(keylist[key1],keylist[key2])-min(keylist[key1],keylist[key2]))*0.1*l)
                            fname=key1.replace('_'+str(keylist[key1])+'ule','_'+str(value)+'ule')
                            fname=fname.replace('_'+str(3000-keylist[key1])+'ulw','_'+str(3000-value)+'ulw')
                            if '-repaired' in fname:
                                fname=fname.replace('-repaired','')
                            if fname[:-5] in fnamedict:
                                fnamedict[fname[:-5]]+=1
                            else:
                                fnamedict[fname[:-5]]=1
                            fname='sim'+fname[3:-5]+str(fnamedict[fname[:-5]])+'.txt'    
                            print(fname)  
                            print(key1,key2)
                            col[fname]=col[key1]
                            datadict[fname]=interpolate_mat(datadict[key1],datadict[key2],l,re.search(checker,key1).group(3)) 
                            if len(datadict[fname])==0:
                                del datadict[fname]
                    
def norm_int(datadict,mapmax):
    dnormdict={}
    for key in datadict:
        if "diffmap" not in key and key[:-4]+'-repaired.txt' not in datadict:
            if '-repaired.txt' in key:
                dnormdict[key.replace('-repaired','')]=copy.deepcopy(datadict[key])
            else:
                dnormdict[key]=copy.deepcopy(datadict[key])
    for key in dnormdict:
        dnormdict[key][dnormdict[key]<0]=0
        if "PL" in key:
            dnormdict[key][:,1:]=dnormdict[key][:,1:]/mapmax*65535
        if "LT405" in key:
            dnormdict[key][:,1:]=dnormdict[key][:,1:]/np.max(dnormdict[key][:,1:])*65535
            dnormdict[key][:,0]=np.arange(0,1024)
        if "LT450" in key:
            dnormdict[key][:,1:]=dnormdict[key][:,1:]/np.max(dnormdict[key][:,1:])*65535
            dnormdict[key][:,0]=np.arange(0,1024)
        dnormdict[key]=np.rint(dnormdict[key]) 
        dnormdict[key]=dnormdict[key].astype(np.uint16) 
    return dnormdict        




def vector(solvents,one,checker,datadict):
    vc={}
    for solvent in solvents: 
        for key1 in one[solvent]:  
            for key2 in one[solvent]:  
                for key3 in one[solvent]: 
                    if re.search(checker,key1) is not None and re.search(checker,key2) is not None and re.search(checker,key3) is not None:  
                        if re.search(checker,key1).group(1)==re.search(checker,key2).group(1)==re.search(checker,key3).group(1):  
                            if re.search(checker,key1).group(3)=='PL' and re.search(checker,key2).group(3)=='LT405' and re.search(checker,key3).group(3)=='LT450':  
                                print (key1,key2,key3) 
                                if solvent+re.search(checker,key1).group(1) in vc:
                                    vc[solvent+re.search(checker,key1).group(1)]+=1
                                else:
                                    vc[solvent+re.search(checker,key1).group(1)]=1
                                print('vector_'+solvent+'_'+re.search(checker,key1).group(1)+'ul_'+str(vc[solvent+re.search(checker,key1).group(1)])+'.csv')                                                                                                                                                                                              
                               
