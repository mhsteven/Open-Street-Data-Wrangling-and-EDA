
# coding: utf-8

# In[ ]:


import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "map (San Jose).xml"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE) #Steven: \b matches word boundary. \S matches non-white space. 
# +one or more occruance. \. this . is preceding by \ an escape, so mean purely an ".".  ? match 0 or 1 occurance
# $ matches end of line => so it must be the last word of the string ! So it only matches "Ave."  
# what is this matching up ?  for example.  "asdfa." => something start with Non-white space, and end with either . or non-white space
# ave. Street    Note: space doesn't seem like a whitespace


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Highway", "Hill", "Circle", "Way", "Expressway","Alley"]


mapping = { "St": "Street",
            "St.": "Street", "Ave": "Avenue", "Ave.": "Avenue", "Rd":"Road", "Rd.":"Road","Dr":"Drive", "Dr.":"Drive",
            "Blvd":"Boulevard", "Blvd.":"Boulevard", "Hwy":"Highway", "Ct":"Court", "court":"Court", "Ln":"Lane"
            }


def audit_street_type(street_types, street_name): # this street_name argument pass in the full address.. but street_types start with empty dictionary, and gradually added if no match to the street type etc. Ave.
    m = street_type_re.search(street_name)  # the stree_types passsed in is the defaultdictionary object in Set
    if m:
        street_type = m.group()  #Steven: This seems just return a string. Returns one or more subgroups of the match. Without arguments, group1 defaults to zero (the whole match is returned).
        if street_type not in expected: # expected is list of street type, so street_type must only contain street_type string
            street_types[street_type].add(street_name) #Steven: street_name is the whole attribute v value ="North Lincoln Ave"
        
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile): # Powerhouse function holding 2 functions above, to pass in the XML file, and return a defaultDict Object (Set) containing the street name that has street type not in "expected" list
    osm_file = open(osmfile, "r", encoding='utf8') # Steven: for windows user, I need to add encoding = 'utf8' to avoid error
    street_types = defaultdict(set)  # Steven" it creates a empty set whenever enter a new key as the key of the empty set, and enter the value into the new Set => In short, it save our effort to specify what type of value to create in the dictionary, it's setting a baseline default value to begin with
    for event, elem in ET.iterparse(osm_file, events=("start",)): 

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"): # Steven: it iterate through all tag named "tag" to allow us check its attribute
                if is_street_name(tag): # Steven: if this tag's k value is "addr:street" then trigger below code
                    audit_street_type(street_types, tag.attrib['v']) # this link to audit_street_type function and return a dictionary containing any street name with ending that wasn't in "expected" list
                    
    osm_file.close()
    return street_types   # this return the defaultdict type that containing non-matching street type and its current name in dataset. 


def update_name(name, mapping): # name is a string object, mapping is a Dictionary object

    # Steven: mapping is the St. to Street etc. a dictionary object, so you can call with dictionary key

    better_name = ''
    for item in name.split():
        if item.capitalize() in mapping:  # if the name component is contain in mapping's dictionary "key"
            better_name = ' '.join([better_name, mapping[item.capitalize()]]) # Steven: I add capitalize so in the mapping I only need to provide one possible spelling
        else:
            better_name = ' '.join([better_name, item.capitalize()]) # if name not in mapping, then just keep the original spelling while capitalize first character
    return better_name.strip()



def test():
    st_types = audit(OSMFILE)  # Steven: from above code, it looks like it only return the dict that has no matches street type as in "expected" list
    pprint.pprint(len(st_types)) # Steven: so from this file, there are only 3 street name with street type that are non-standard, so need to be corrected using update_name function
    pprint.pprint(dict(st_types))  # st_types here is an DefaultDict object (with Set)

    for st_type, ways in st_types.items(): # changed this method from .iteritems() from 2.7 to 3.6's .items()   # Steven: return tuple (key,value) pairs
        for name in ways: # ways is an Set object containing full street name that is not contain in "expected" list
            better_name = update_name(name, mapping) # name is an string object, mapping is a dictionary object
            print (name, "=>", better_name) # cleaned up this print statement 

if __name__ == '__main__':
    test()  

