import partkeepr
from inventree.api import InvenTreeAPI
from inventree.part import PartCategory,Part
from inventree.stock import StockItem, StockLocation

SERVER_ADDRESS = 'http://127.0.0.1:8000'
MY_USERNAME = 'username'
MY_PASSWORD = 'password'

api = InvenTreeAPI(SERVER_ADDRESS, username=MY_USERNAME, password=MY_PASSWORD)

itparts = Part.list(api)
for p in itparts:
    print("delete p ",p.name)
    p.delete()



# cat = PartCategory.list(api)
# print(len(cat))
#
# for c in cat:
#     print("delete c ",c.name)
#     c.delete()



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
        return 0

    else:
        #create or return unknownloadtion
        itloca = StockLocation.list(api, search='UNKNOWN')
        if (len(itloc)>0):
            return itloca[0]
        return 0

def createITPart(part,ITCat):
    print("create part %s cat %s" % (part,ITCat.name))
    if len(part.description)==0:
        part.description=part.name
    np = Part.create(api, {
        'name' : part.name,
        'description' : part.description,
        'category' : ITCat.pk,
        'active' : True,
        'virtual' : False,
        'IPN' : part.IPN
    })
    return np

allPKparts=partkeepr.getallParts()

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

