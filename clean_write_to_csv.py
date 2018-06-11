
# coding: utf-8

# In[ ]:



import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema # note: refers to the schema.py file attached in this directory  


OSM_PATH = "map (San Jose).xml"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')  # Steven: this find string start with lower case with 1 colon(:) follow with lower case
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]') # Steven: this find any unusual character and whitespaces etc. line break

SCHEMA = schema.schema  # Steven: this pass in the SQL table structure from Python code (dictionary)

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp'] 
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type'] 
WAY_NODES_FIELDS = ['id', 'node_id', 'position'] 


def update_name(name, mapping): # name is a string object, mapping is a Dictionary object
    # this is to update street type abbreviation to full spelling
    # Steven: mapping is the St. to Street etc. a dictionary object, so you can call with dictionary key

    better_name = ''
    for item in name.split():
        if item.capitalize() in mapping:  # if the name component is contain in mapping's dictionary "key"
            better_name = ' '.join([better_name, mapping[item.capitalize()]]) # Steven: I add capitalize so in the mapping I only need to provide one possible spelling
        else:
            better_name = ' '.join([better_name, item.capitalize()]) # if name not in mapping, then just keep the original spelling while capitalize first character
    return better_name.strip()


def update_zipcode(zipcode):
    """
        Update the dict_tag['value'] (string) to the 5-digit format
        Args:
                zipcode (string): to pass in the dict_tag['value'], giving a string type of zip code
        
        Returns:
                string: return a string of 5-digit zip code
    """
    zip = re.compile(r'9\d{4}')  # to search for 5 digit start with number 9
    match = zip.search(zipcode)
    if match: # if find the correct pattern then use the correct 5-digit pattern
        return match.group(0)
    else: # if not finding 5-digit pattern, then keep as is, so I can capture it in my next round of checking using SQL
        return zipcode

    
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""


    
    node_attribs = {}
    way_attribs = {}
    way_nodes = []  # Steven: I notice they like to use List if the tag is repetitive under 1 ID. But use Dictionary to contain 1 tag with 1 unique ID.
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node': # this to handle the node tag.
        for field in node_attr_fields: # node_attribs dictionary contain NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
            node_attribs[field] = element.get(field) # add attribute to the dictionary. (this way I mandate the creation of each field, and in the case no such attribute existm, it store nothing in the value of the key field). I decide not to ignore any field since the schema to pass to SQL required all fields
        
        for tag in element.iter('tag'): # tags to pass to node_tags with NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
            # I think this iter() will iterate though all direct child level tag of element (actually also include the element's own tag), I need this to retrieve all tag under node, so .iter('tag)
            # Good that if the iter('tag') couldn't find tag, it won't throw error, but just pass this for loop to do nothing, so I can keep the tag =[] empty list as instructed
            dict_tag = {}
            
            if problem_chars.search(tag.get('k')): # if key contain problem character, then the tag should be ignore (I believe it mean to not create a dictionary for this tag?)
                continue # to skip current loop, and continue to next loop

            if LOWER_COLON.search(tag.get('k')): # if key contain colon, then split it to assign first part to type, and last part to key.
                split_key = tag.get('k').split(':',1)
                dict_tag['key'] = split_key[-1]
                dict_tag['type'] = split_key[0]
            else: # if not contain colon, then assign "regular" to type, and whole key to key
                dict_tag['key'] = tag.get('k')
                dict_tag['type'] = default_tag_type
                
            dict_tag['id'] = element.attrib['id'] # assign the id using parent element's 'id' attribute
            dict_tag['value'] = tag.get('v')# assign v attribute as value
            
            if dict_tag['key'] == 'street': # Steven: This is to modify the address value (v) to make sure it is in "expected" street type format (utilize function written from prior cell => update_name), and from my observation, only the key match exactly "street" needs attention to fix.
                dict_tag['value'] = update_name(dict_tag['value'],mapping) # Utilize update_name function created above
            
            if dict_tag['key'] == 'postcode': # Steven: this is to make sure all zip codde are in 5 digit format in 'value' field
                dict_tag['value'] = update_zipcode(dict_tag['value']) # Utilize update_zipcode function created above
            
            tags.append(dict_tag) # this is the key code to append each tag dictionary to the master tag list !
            
    if element.tag == 'way':  # this to handle the way tag.
        for field in way_attr_fields:
            way_attribs[field] = element.get(field)            
        
        for tag in element.iter('tag'): # this to handle the child element with 'tag' tag, handle the same way as in node tag
            dict_tag = {}
            
            if problem_chars.search(tag.get('k')): # if key contain problem character, then the tag should be ignore (I believe it mean to not create a dictionary for this tag?)
                continue
                
            if LOWER_COLON.search(tag.get('k')): # if key contain colon, then split it to assign first part to type, and last part to key.
                split_key = tag.get('k').split(':',1)
                dict_tag['key'] = split_key[-1]
                dict_tag['type'] = split_key[0]
            else: # if not contain colon, then assign "regular" to type, and whole key to key
                dict_tag['key'] = tag.get('k')
                dict_tag['type'] = default_tag_type
                
            dict_tag['id'] = element.attrib['id'] # assign the id using parent element's 'id' attribute
            dict_tag['value'] = tag.get('v')# assign v attribute as value
            
            if dict_tag['key'] == 'street': # Steven: This is to modify the address value (v) to make sure it is in "expected" street type format (utilize function written from prior cell => update_name), and from my observation, only the key match exactly "street" needs attention to fix.
                dict_tag['value'] = update_name(dict_tag['value'],mapping) # Utilize update_name function created above
            
            if dict_tag['key'] == 'postcode': # Steven: this is to make sure all zip codde are in 5 digit format in 'value' field
                dict_tag['value'] = update_zipcode(dict_tag['value']) # Utilize update_zipcode function created above
                    
            tags.append(dict_tag) # this is the key code to append each tag dictionary to the master tag list !            
        
        n = 0 # to assign for way_nodes's position of each nd tag
        for nd in element.iter('nd'): # this to handle the child element with 'nd' tag.
            dict_node = {}
            dict_node['id'] = element.get('id') #way_nodes id to store parent element's id
            dict_node['node_id'] = nd.get('ref')
            dict_node['position'] = n
            way_nodes.append(dict_node) # add the dictionary to way_nodes list
            n = n + 1    

    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

    # Steven: Finally, it return a dictionary of either node, or way

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end')) # Steven: from my understand, this iterate each line under top tag. 
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
    #Steven: this provide 

def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string)) 


class UnicodeDictWriter(csv.DictWriter, object):
    # note: this was necessary and done strictly for python 2 since it doesn't automatically read unicode
    # commented out writerow since it's overriding an existing method which should work fine in python 3 
    # if using windows and data doesn't write as unicode, you can find a way on your own or use original 
    # python 2 code
    """Extend csv.DictWriter to handle Unicode input"""

    """ def writerow(self, row):
        # change .iteritems() method to .items() (python 3 uses .items()) and figure out how to enforce unicode
        # note: the following is dictionary comprehension, similar to list comprehension but for dicts
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        }) 
    """
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate): #Steven: file_in is the file. validate is boolean variable, and test we enter True
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w',encoding='utf8') as nodes_file,             codecs.open(NODE_TAGS_PATH, 'w',encoding='utf8') as nodes_tags_file,             codecs.open(WAYS_PATH, 'w',encoding='utf8') as ways_file,             codecs.open(WAY_NODES_PATH, 'w',encoding='utf8') as way_nodes_file,             codecs.open(WAY_TAGS_PATH, 'w',encoding='utf8') as way_tags_file:
    
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS) #nodes_file pass in the csv to be created 
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader() 
        node_tags_writer.writeheader() 
        ways_writer.writeheader() 
        way_nodes_writer.writeheader() 
        way_tags_writer.writeheader() 

        validator = cerberus.Validator() 
        
        
        #added this
        count = 0
        for element in get_element(file_in, tags=('node', 'way')): #get_element function from XML file selected only Way, Node, Relation tag (nested function #1)
            
            el = shape_element(element) # element is from get_element function which from the     (nested function #2)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags']) 


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True) 

