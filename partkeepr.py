# coding: utf-8
import requests
import json
import pprint
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
server = config.get('partkeepr', 'server_address')
auth = (config.get('partkeepr', 'user'), config.get('partkeepr', 'password'))

api = "/api/parts"
searchfilter = '?filter={"property":"name","operator":"LIKE","value":"%s%%"}'


class attachment(object):
    def __init__(self, data):
        self.url = server + data['@id'] + '/getFile'
        self.filename = data['originalFilename']
        self.isImage = data['isImage']

class part(object):
    def __init__(self,req):
        #print(req)
        #print (req["name"])
        self.name = req["name"]
        self.description = req["description"]
        self.comment = req["comment"]
        self.id = req["@id"][req["@id"].rfind("/")+1:]
        try:
            self.footprint = req["footprint"]["name"]
        except TypeError:
            self.footprint = ""
        try:
            self.category =  req["category"]["name"]
        except TypeError:
            self.category = ""
        try:
            self.categoryPath = req["category"]["categoryPath"].split(u' ➤ ')
        except TypeError:
            self.categoryPath =""
        try:
            self.storageLocation = req["storageLocation"]["name"]
        except TypeError:
            self.storageLocation=""
        try:
            self.MFR = req["manufacturers"][0]["manufacturer"]["name"]
        except (TypeError,IndexError):
            self.MFR = "-"
        try:
            self.MPN = req["manufacturers"][0]["partNumber"]
        except (TypeError , IndexError):
            self.MPN = "-"
        try:
            self.IPN = req['internalPartNumber']
        except (TypeError, IndexError):
            self.IPN =self.MPN
        try:
            self.stock = req['stockLevel']
        except (TypeError, IndexError):
            self.stock = 1
        try:
            self.price = req['averagePrice']
        except (TypeError, IndexError):
            self.price = 0

        self.attachments = []
        self.image = None
        for d in req['attachments']:
            a = attachment(d)
            if not self.image and a.isImage:
                self.image = a
            else:
                self.attachments.append(a)

    def getValues(self):
        return [self.category,self.name,self.description,self.footprint]

    def __str__(self):
        return '%s %s %s %s ' % (self.name,self.description,self.footprint,self.category)

def getPartsValues(listparts):
    pvales = []
    for p in listparts:
        pvales.append(p.getValues())
    return pvales

def searchComponent(value):
    url = server+api+searchfilter

    r = requests.get( url % value,auth=auth)

    if (r.status_code == 200):
        listofparts = []
        for p in r.json()["hydra:member"]:
            listofparts.append(part(p))

        return listofparts

    else:
        return None

def getDefaultHdr():
    return ["   Category   ","Value","        Description            ","Footprint"]


def getProjectList():
    url = server + "/api/projects"
    r = requests.get(url, auth=auth)
    if (r.status_code == 200):
        listofprojects = []
        for p in r.json()["hydra:member"]:
            listofprojects.append(p["name"])
        return listofprojects
    else:
        return []

def createProject(projectName,projectDescript,parts):
    projectDict = dict(name=projectName,description=projectDescript)
    #{"quantity":1,"remarks":"R1","overageType":"","overage":0,"lotNumber":"","part":"/api/parts/4"}
    partList = []
    for partid,partv in parts.items():
        partList.append({"quantity": len(partv['remark']), "remarks": "%s" % (",".join(partv['remark'])), "overageType": "", "overage": 0, "lotNumber": "", "part": "/api/parts/%s" % partid})

    projectDict['parts']=partList

    url = server + "/api/projects"
    r = requests.post(url, data=json.dumps(projectDict),auth=auth)
    if r.status_code == 201:
        return True
    return False


def buildPartCategoriesa(pcat):
    #print(pcat)
    #cat = []
    #print(len(pcat))
    #return
    #print(pcat[5]['name'])
    cat = {}
    for p in pcat:
        #print(p['name']+" "+p['@id'])
        #cat[p] = p['children']
        #children = {}
        children=[]
        for c in p['children']:
            children.append(c['name'])
            #print("children ", c['name'])
            #buildPartCategories(c['children'])
        #print(pcat['name'])
        cat[p['name']]=children
    print(cat)
    return cat
    for p in pcat["name"]:
        #print (p)
        l = [p["name"]]
        for c in p["children"]:
            l.append(buildPartCategories(c))
        cat.append(l)
    return cat

def getPartCategories():
    url = server + "/api/part_categories"
    r = requests.get(url, auth=auth)

    if (r.status_code == 200):

        #print(pprint.pprint(r.json()))
        #print(r.json()["hydra:member"])
        listofcategories = buildPartCategories(r.json()["hydra:member"])
        #print(listofcategories)
        print(listofcategories.keys())
        pass
        #return listofprojects
    else:
        return []


def getallParts():
    allfilter ="?itemsPerPage=9999999999"
    url = server + api + allfilter

    r = requests.get(url, auth=auth)

    if (r.status_code == 200):
        listofparts = []
        for p in r.json()["hydra:member"]:
            pkpart = part(p)
            #print(pkpart)
            listofparts.append(pkpart)



        #print(listofparts)
        #print(len(listofparts))
        return listofparts

    else:
        return None

def recursiveCat(pathlist,catdict):
    print(pathlist, catdict)
    if (len(pathlist) >= 1):
        node = recursiveCat(pathlist[1:], pathlist[0])
        print (node)
        print (catdict)
        return [catdict,node]
    return catdict



    print(pathlist)
    print(catdict)
    if (len(pathlist)>1):
        if pathlist[0] in catdict:
            twig = catdict[pathlist[0]]['children']
        else:
            twig = {'childrenlist':[],'children':{}}
        leaf = recursiveCat(pathlist[1:],twig)
        print("leaf %s" % leaf)
        print("pathlist %s" % pathlist)
        print("twig %s" % twig)
        twig['childrenlist'].extend(leaf.keys())
        twig['children'].update(leaf)
        print("twig %s" % twig)
        set(twig['childrenlist'])
        print("twig %s" % twig)

        print("catdict %s" % catdict)

        catdict['childrenlist'].extend(twig.keys())
        #print(catdict['childrenlist'])
        #set(catdict['childrenlist'])
        #print(catdict['childrenlist'])
        catdict['children'].update(twig)


    node = {pathlist[0]: {'childrenlist':[],"children":{}}}
    return node

def getPartCategories(allparts):
    #given the list of parts build up a dictionary of dictionaries

    for part in allparts:
        print(part.name)
        partcat = part.category
        print(partcat)
        partcatpath = part.categoryPath
        print(partcatpath)
        partparts = partcatpath.split(u' ➤ ')
        print(part.name)
        print(partparts)
        catdict=[]
        print("recursiveCat")
        cat = recursiveCat(partparts,catdict)
        print (cat)
        print (catdict)
        break