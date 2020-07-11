#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 15:42:35 2020

@author: sahyadri
"""


from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
import numpy as np
from astropy.table import Table, vstack
from astropy.io import ascii
from astropy import units as u
from astropy.coordinates import SkyCoord, get_constellation
import pandas as pd 
import glob, os


print('Downloading constellation_borders.csv...')
catalogue_list = Vizier.find_catalogs("Constellation")#This loads all the catalogs by the keyword "constellation"
Vizier.ROW_LIMIT = -1
catalog = Vizier.get_catalogs("VI/49")[1]#This selects the 2nd of three tables that were found by the key-word search. This table contains relevant data
catalog.remove_columns(['cst','type'])
coords = SkyCoord(catalog['RAJ2000'],catalog['DEJ2000'],unit="deg")
const = coords.get_constellation()
const = ['Bootes' if x=='Boötes' else x for x in const]#fixing for the unicode problem
catalog.add_column(const,name="Constellation", index = 2)
catalog.write("constellation_borders.csv",format="csv",overwrite="True")
print('\n')
print('Done')
print('\n')
print('Downloading Messier Catalogue...')

#the next three lines are to simplify the output table
Simbad.reset_votable_fields()
Simbad.remove_votable_fields('coordinates')
Simbad.add_votable_fields('otype(3)', 'ra(d;A;ICRS;J2000;2000)', 'dec(d;D;ICRS;J2000;2000)','flux(B)','flux(V)')#These are all the columns added to the table

result_table = Simbad.query_catalog("Messier")#This asks the SIMBAD database to list all objects from the messier catalog
result_table['FLUX_V'].name = 'V'
result_table['OTYPE_3']=np.array([x.decode('utf8') for x in result_table['OTYPE_3']])
result_table['MAIN_ID']=np.array([x.decode('utf8') for x in result_table['MAIN_ID']])
result_table['RA_d_A_ICRS_J2000_2000'].name = "RAJ2000"
result_table['DEC_d_D_ICRS_J2000_2000'].name = "DEJ2000"
result_table['B-V'] = result_table['FLUX_B'] - result_table['V']
result_table.remove_column('FLUX_B')

coords = SkyCoord(result_table['RAJ2000'],result_table['DEJ2000'],unit="deg")
const = coords.get_constellation()
const = ['Bootes' if x=='Boötes' else x for x in const]#fixing for the unicode problem
const_abr = coords.get_constellation(short_name = "True")
result_table.add_column(const,name="Constellation", index = 2)

otype = result_table['OTYPE_3']
internal_id = ['{}_{}_M{}'.format(otype[i],const_abr[i],str(i+1)) for i in range(len(const))]
result_table.add_column(internal_id, name = "Internal ID Number", index = 0)

result_table.write("messier_objects.csv",format="csv",overwrite="True")#creates a csv file


Simbad.reset_votable_fields()#renders the prev changes to simbad class temporary.
print('\n')
print('Done')
print('\n')
print('Downloading NGC catalogue...')

v = Vizier(columns = ['Name','Type','mag','RA (deg)','Dec (deg)'])#Columns added to table
v.ROW_LIMIT = -1
result_table = v.get_catalogs("VII/118/ngc2000")[0]

#Changing the type and name - making more uniform.
result_table['Name'] = np.array(['IC '+x[1:] if x[0]=='I' else 'NGC '+x for x in result_table['Name']])
result_table['Type'] = np.array(['Gal' if x=='Gx' else 'OpC' if x=='OC' else 'GlC' if x=='Gb' else 'PN' if x=='Pl' else 'Str' if x=='*' or x=='D*' or x=='***' else '-' if x == '' or x=='-' or x=='?' else x for x in result_table['Type']])

#adding constellation names
coords = SkyCoord(result_table['_RAJ2000'],result_table['_DEJ2000'],unit="deg")
const = coords.get_constellation()
const = ['Bootes' if x=='Boötes' else x for x in const]#fixing for the unicode problem
const_abr = coords.get_constellation(short_name = "True")
result_table.add_column(const,name="Constellation", index = 2)

#Adding an internal id number
otype = result_table['Type']
internal_id = ['{}_{}_{}'.format(otype[i],const_abr[i],result_table['Name'][i]) if otype[i]!='-' else 'notype_{}_{}'.format(const_abr[i],result_table['Name'][i]) for i in range(len(const))]
result_table.add_column(internal_id, name = "Internal ID Number", index = 0)
result_table.write("NGC.csv",format="csv",overwrite="True")

#cross-reference catalogue for NGC
v = Vizier(columns = ['Object','Name'])
v.ROW_LIMIT = -1
v.TIMEOUT = 1000
cross_catalog = v.get_catalogs('VII/118/names')[0]

cross_catalog['Name'] =  ['IC {}'.format(x.split()[1]) if len(x.split())==2 and x.split()[0]=="I" else 'IC {}'.format(x.split()[0][1:]) if len(x.split())==1 and x[0]=="I" else 'NGC {}'.format(x) for x in cross_catalog['Name']]
name = np.array([len(x.split()) for x in cross_catalog['Name']])
index = np.array(np.where(name==1)[0])
cross_catalog['Name'][index] = ['NGC 6603','NGC 7092','NGC 1432','NGC 5866']#manual editing
cross_catalog.write("DsCrossCatalog.csv",format='csv',overwrite="True")

#Adding common names of some NGC objects
ccat = pd.read_csv('DsCrossCatalog.csv')
ccat = pd.DataFrame(ccat)
ccat = ccat.groupby('Name')['Object'].apply(lambda x: ', '.join(x)).reset_index()
ntable= pd.read_csv('NGC.csv')
ntable = pd.DataFrame(ntable)
ntable.insert(2,"Common Name",np.zeros(len(ntable['_RAJ2000'])))
ntable['Common Name'] = ntable.Name.map(ccat.set_index('Name').Object,na_action="ignore")
ntable.to_csv('NGC.csv')
ntable = Table.read('NGC.csv')
ntable.remove_columns(['col0'])
ntable.write('NGC.csv',format='csv',overwrite="True")

print('\n')
print('Done')
print('\n')

#Download the star name file
#kaggle.api.authenticate()
#kaggle.api.dataset_download_files('ecotner/named-stars/IAU-CSN.csv', path='/home/sahyadri/Desktop/Star-Hopping', unzip=True)

#CROSS CATALOG
v = Vizier(columns = ['HD','TYC','HIP','Vmag','Fl','Bayer','Cst'])
v.ROW_LIMIT = -1
v.TIMEOUT = 1000
cross_catalog = v.get_catalogs('IV/27A/catalog')[0]
bayer_const = ['{} {}'.format(x['Bayer'],x['Cst']) for x in cross_catalog]
cross_catalog.remove_columns("Bayer")
cross_catalog['BayerConst'] = bayer_const
cross_catalog.write("CrossCatalog.csv",format='csv',overwrite="True")


ccat = pd.read_csv('CrossCatalog.csv')
ccat = pd.DataFrame(ccat)
ccat["HIP"].fillna("0", inplace = True)
miss_index = np.where(ccat['HIP']=='0')[0]
hd_missing = np.array(ccat['HD'][miss_index])
hip=[]#will containt all missing values
for items in hd_missing:
    ident_table = np.array(Simbad.query_objectids("HD "+str(items)))
    ident_table = np.array([x[0].decode('utf8') for x in ident_table])
    if any(['HIP' in x.split()[0] for x in ident_table]):
        ind = np.where(['HIP' in x.split()[0] for x in ident_table])[0]
        hip.append(ident_table[ind][0].split()[1])
    else:
        hip.append('0')
        
cross_catalog['HIP'][miss_index] = hip
cross_catalog.write("CrossCatalog.csv",format='csv',overwrite="True")

print('Tycho-1 Catalogue')

run_count = 0
run = True
last_id = 0
while run:
    
    MinVmag = input('(INT ONLY) Input minimum value of Vmag (skippable) ',)
    MaxVmag = float(input('(INT ONLY) Input maximum value of Vmag (MAX 10.5)',))

    if type(MaxVmag)!=float:
        print("invalid entry")
        continue
    elif MaxVmag>10.5:
        print("Input a number less than 10.5 for tycho-1")
        continue
    if MinVmag!='':
        MinVmag = int(MinVmag) 
    
    run_count = run_count +1
    if MinVmag=='':
        filter_input = "<{}".format(MaxVmag)
    else:
        filter_input = "{}..{}".format(MinVmag, MaxVmag)
    
    #Query
    v = Vizier(columns = ['HIP','TYC','HD','_RAJ2000','DECJ2000','+Vmag','B-V'], column_filters = {"Vmag":"{}".format(filter_input)})
    v.ROW_LIMIT = 1000000000
    v.TIMEOUT = 1000
    catalog_stars = v.get_catalogs("I/239/tyc_main")[0]
    catalog_stars['Vmag'].name = "V"

    #Adding constellation names
    coords = SkyCoord(catalog_stars['_RAJ2000'],catalog_stars['_DEJ2000'],unit="deg")
    const = coords.get_constellation()
    const = ['Bootes' if x=='Boötes' else x for x in const]#fixing for the unicode problem
    const_abr = coords.get_constellation(short_name = "True")
    
    catalog_stars.add_column(const,name="Constellation", index = 0)
    
    #adding internal id
    internal_id = ["Str_{}_{:08d}".format(const_abr[i],i+last_id+1) for i in range(len(catalog_stars['_RAJ2000']))]
    catalog_stars.add_column(internal_id, name="Internal ID Number", index = 0)
    
    catalog_stars.write("tycho_{}.csv".format(run_count),format="csv",overwrite = "True")
    last_id = last_id + len(catalog_stars['_RAJ2000'])


    #Adding common names to the stars
    names_table = pd.read_csv('IAU-CSN.csv')
    names_table = pd.DataFrame(names_table)
    ttable = pd.read_csv('tycho_{}.csv'.format(run_count),dtype = {"Name":"string"})
    ttable = pd.DataFrame(ttable)
    names_table["HIP"] = np.array([x if x!='-' else 0 for x in names_table["HIP"]])
    ttable.insert(1,"Name",np.zeros(len(ttable['TYC'])))
    names_table["HIP"] = pd.to_numeric(names_table['HIP'],errors='coerce')
    ttable['Name'] = ttable.HIP.map(names_table.set_index('HIP').Name)
    ttable.to_csv('tycho_{}.csv'.format(run_count))
  

    #The cross cataloguing part
    ccat = pd.read_csv('CrossCatalog.csv')
    ccat = pd.DataFrame(ccat)
    ccat["HIP"].fillna("0", inplace = True)
    ttable = pd.read_csv('tycho_{}.csv'.format(run_count),dtype = {"Name":"string"})
    ttable = pd.DataFrame(ttable) 
    ccat = ccat.loc[~ccat.HIP.duplicated(keep='first')]
    ttable.insert(4,"Bayer",np.zeros(len(ttable['_RAJ2000'])))    
    ttable['Bayer'] = ttable.HIP.map(ccat.set_index('HIP').BayerConst,na_action="ignore")
    if run_count == 1:    
        ttable.to_csv('tycho.csv',index=False) 
    else:
        ttable.to_csv('tycho.csv',mode='a', header=False,index=False)
      
    while True:
        status = input("Another run of Tycho database download? (y/n)",)
        if status == "n":
            run = False
            break
        elif status == "y":
            run = True
            break
        else:
            print("invalid answer")
  
for file in glob.glob("tycho_*.csv"):
    os.remove(file)
            
print('Tycho-2 Catalogue - from Vmag 10.5 to 12')
print('\n')
print('NOTE: Large file, may take some time.')
print('\n')
print('Downloading...')

#The catalogue download
v = Vizier(columns = ['HIP','_RAJ2000','DECJ2000','BTmag','+VTmag'], column_filters = {"VTmag":"10.2..12.3"})
v.ROW_LIMIT = -1
v.TIMEOUT = 1000
catalog_stars = v.get_catalogs("I/259/tyc2")[0]
vmag = catalog_stars['VTmag'] - 0.09*(catalog_stars['BTmag']-catalog_stars['VTmag'])
catalog_stars.add_column(vmag,name = 'Vmag',index=5)
catalog_stars['Vmag'].name = "V"
catalog_stars['V'].sort()

#Filtering
v= np.array([x if x!='--' else 0 for x in catalog_stars['V']])
ind1 = np.where(v>12)[0]
ind2 = np.where(v<10.5)[0]
ind = np.concatenate((ind1,ind2))
catalog_stars.remove_rows(ind)

#adding constellation names
coords = SkyCoord(catalog_stars['_RAJ2000'],catalog_stars['_DEJ2000'],unit="deg")
const = coords.get_constellation()
const = ['Bootes' if x=='Boötes' else x for x in const]#fixing for the unicode problem
const_abr = coords.get_constellation(short_name = "True")
bv = np.array(catalog_stars['BTmag'])-np.array(catalog_stars['VTmag'])
catalog_stars.add_column(bv,name='BT-VT',index=6)
catalog_stars.remove_columns(['BTmag','VTmag'])
#adding internal id and saving
internal_id = ["Str_{}_{:08d}".format(const_abr[i],i+last_id+1) for i in range(len(catalog_stars['_RAJ2000']))]
catalog_stars.add_column(internal_id, name="Internal ID Number", index = 0)
catalog_stars.add_column(const,name="Constellation", index = 0)
catalog_stars.write("tycho-2.csv",format="csv",overwrite = "True",fast_writer=True)

print('Done')