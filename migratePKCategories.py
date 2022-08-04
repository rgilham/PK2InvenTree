import partkeepr
from inventree.api import InvenTreeAPI
from inventree.part import PartCategory,Part,PartAttachment
from inventree.stock import StockItem, StockLocation
import tempfile
import requests
import os
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
SERVER_ADDRESS = config.get('inventree', 'server_address')
MY_USERNAME = config.get('inventree', 'user')
MY_PASSWORD = config.get('inventree', 'password')

api = InvenTreeAPI(SERVER_ADDRESS, username=MY_USERNAME, password=MY_PASSWORD)

#delete all the exisiting parts

itparts = Part.list(api)
for p in itparts:
    print("delete p ",p.name)
    p.__setitem__('active', False)
    p.__setitem__('image', None)
    p.save()
    p.delete()

#delete all of the exisitng categories

cat = PartCategory.list(api)


for c in cat:
    print("delete c ",c.name)
    c.delete()



def checkAndCreatePartCat(partnodeCat,parent):
    partnodeCat = partnodeCat.replace('/','-')
    try:
        parent = parent.replace('/', '-')
    except:
        pass
    #print("checkAndCreatePartCat %s %s" % (partnodeCat,parent))
    cats = PartCategory.list(api,search=partnodeCat)
    for c in cats:
        if (c.name==partnodeCat):
            #print ("found ",partnodeCat)
            #print(c.name)
            if (c.parent==None) and (parent==None):
                return c
            if not(c.parent==None):
                parentCat = PartCategory(api,c.parent)
                #print("parentCat ",parentCat)
                #print("parentCat ", parentCat.name)
                if (parentCat.name == parent):
                    return c




    if (parent==None):
        cat = PartCategory.create(api,{
            'name' : partnodeCat,
            'description' : ''
        })
        #print("created ",cat," ",cat.pk)
        return cat
    else:
        parentCat = PartCategory.list(api, search=parent)
        #print("got parent ",parentCat)
        if (len(parentCat)>0):
            parentpk=None
            for pc in parentCat:
                if (pc.name==parent):
                    parentpk = pc
                    break

            #print(parentpk.name)
            #print(parentpk.pk)
            cat = PartCategory.create(api, {
                'name': partnodeCat,
                'description': '',
                'parent' : parentpk.pk
            })
            print("created ",cat," ",cat.pk)
            return cat
        else:
            print("checkAndCreatePartCat %s %s" % (partnodeCat, parent))
            print("Error parent given but not created previously")
            return None

def getorCreateLocation(part):
    print(part.name, " loca ",part.storageLocation)
    if (len(part.storageLocation)>0):
        itloca = StockLocation.list(api,search=part.storageLocation)
        for loc in itloca:
            if (loc.name == part.storageLocation):
                return loc
        return StockLocation.create(api, {
            'name': part.storageLocation,
            'parent': ""
        })

    else:
        #create or return unknownloadtion
        itloca = StockLocation.list(api, search='UNKNOWN')
        if (len(itloc)>0):
            return itloca[0]
        return 0

class DownloadedAttachment:
    "Context manager for a downloaded attachment with the correct file name"

    def __init__(self, attachment_data):
        self.path = os.path.join(tempfile.gettempdir(), attachment_data.filename)
        self.url = attachment_data.url

    def __enter__(self):
        with requests.get(self.url, auth=partkeepr.auth) as r:
            open(self.path, 'wb').write(r.content)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.unlink(self.path)

def createITPart(part,ITCat):
    print("create part %s cat %s" % (part,ITCat.name))
    if len(part.description)==0:
        part.description=part.name
    np = Part.create(api, {
        'name' : part.name,
        'description' : part.description,
        'notes' : part.comment,
        'category' : ITCat.pk,
        'active' : True,
        'virtual' : False,
        'IPN' : part.IPN
    })
    if part.image:
        with DownloadedAttachment(part.image) as file:
            np.uploadImage(file.path)
    for attachment in part.attachments:
        with DownloadedAttachment(attachment) as file:
            np.uploadAttachment(attachment=file.path)
    return np

allPKparts=partkeepr.getallParts()

print(allPKparts)
for pkpart in allPKparts:
    catpath = pkpart.categoryPath[1:]
    root = None
    for p in catpath:

        catforPart = checkAndCreatePartCat(p,root)
        root = p
    newPart = createITPart(pkpart, catforPart)
    print(newPart._data)
    itloc = getorCreateLocation(pkpart)
    stockit = StockItem.create(api,{
        'part' : newPart.pk,
        'quantity' : pkpart.stock,
        'location' : itloc.pk
    })

