
# coding: utf-8

# In[ ]:


import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

OSM_FILE = "map (San Jose).xml"  # Replace this with your osm file
SAMPLE_FILE = "sample.xml"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n') # Steven: this keep throwing error TypeError: a bytes-like object is required, not 'str'
    # => work around is to add a 'b' in front of the string => https://github.com/mitsuhiko/phpserialize/issues/15
    output.write(b'<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write(b'</osm>')

