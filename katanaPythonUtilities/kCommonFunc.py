# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import shutil
import re
import StringIO

from Katana import NodegraphAPI
from Katana import UI4
from Katana import Nodes3DAPI

import kMath as km
reload(km)

def getSceneGraphView():
    return UI4.App.Tabs.FindTopTab('Scene Graph').getSceneGraphView()

def getNodeGraphView():
    return UI4.App.Tabs.FindTopTab('Node Graph')._NodegraphPanel__nodegraphWidget

def getCurrentFocuseNode():
    '''return the current viewed group node'''
    return getNodeGraphView()._NodegraphWidget__currentFocusNode

def getSelectedLocations():
    # returned data: [('root', 'location'), ...]
    try:
        location = getSceneGraphView().getSelectedLocations()
    except:
        print 'You should select location in the scene graph.'
        return ''
    if location:
        return [i[1] for i in location]
    return []

def selectLocations(locations_list):
    if not isinstance(locations_list, list):
        locations_list = [locations_list]
    getSceneGraphView().selectLocations(locations_list)
    
def selectNode(node):
    NodegraphAPI.SetNodeSelected(node, True)

def createNode(node_type_string, auto_position=True):
    ''' create a type of node, and put that node in the center of the current focused group'''
    # get node graph widget
    ngw = getNodeGraphView()
    root = NodegraphAPI.GetRootNode()
    focused_node = getCurrentFocuseNode()
    if not focused_node:
        focused_node = root
    new_node = NodegraphAPI.CreateNode(node_type_string, focused_node)
    if auto_position:
        # view port center position in root node space
        # returned value lik ((815.5, -279.0, 10000.0), (1.0, 1.0, 1.0))
        center = NodegraphAPI.GetViewPortPosition(root)
        # convert to group position
        pos = ngw.getPointAdjustedToGroupNodeSpace(focused_node, (center[0][0], center[0][1]))
        # put the node at the position
        NodegraphAPI.SetNodePosition(new_node, pos)
        # select this node
        NodegraphAPI.SetNodeSelected(new_node, True)
    else:
        placeNode(new_node)
    return new_node

def placeNode(node):
    ''' interactivly place the node in the node graph '''
    getNodeGraphView().placeNode(node, shouldFloat=True, autoPlaceAllowed=True)

def getSelectedNodes():
    return NodegraphAPI.GetAllSelectedNodes()

def getLocationNodeMaps():
    # The method should be used to get maps from the location type to node type if possible
    # for example, the light filter type has 'LightFilterCreate' node name, the location can be retrived
    # by adding user.lightParent and user.name parameters, only if the user.makeSharedLightFilter is False
    return {'light filter':{'LightFilterCreate':{'parameters':['user.lightParent','user.name'], 
                                                'others':[('user.makeSharedLightFilter',False)]} \
                            }, \
            'light':{'LightCreate':{'parameters':['name'], 'others':[]}} \
            }

def nodesToLocations(nodes=[]):
    ''' convert node to scene graph location
    note: not every kind of node can be converted. AttributeSet, for instance, can not be converted
    '''
    location = []
    if not isinstance(nodes, list):
        nodes = [nodes]
    for n in nodes:
        if hasattr(n, 'getScenegraphLocation'):
            location.append(n.getScenegraphLocation())
            continue
    return location

def locationsToNodes(locations=[], time=0.0, return_top_node=False):
    if not isinstance(locations, list):
        locations = [locations]
    nodes = {}
    root_producer = getRootProducer()
    type_node_map = getLocationNodeMaps()
    for l in locations:
        location_producer = root_producer.getProducerByPath(l)
        location_type = location_producer.getType()
        if location_type not in type_node_map.keys():
            nodes.update({l:None})
            continue
        
        # find all the node types correspond to the location type
        node_types = type_node_map[location_type].keys()
        for nt in node_types:
            if nodes.has_key(l):
                break
            # get all nodes with specific type
            tmp = NodegraphAPI.GetAllNodesByType(nt)
            for n in tmp:
                isTarget = True
                # first check the conditions on the specific node
                conditions = type_node_map[location_type][nt]['others']
                for c in conditions:
                    if n.getParameter(c[0]).getValue(time) != c[1]:
                        isTarget = False
                        break
                if not isTarget:
                    continue
                # get the location path
                path = '/'
                params = type_node_map[location_type][nt]['parameters']
                for p in params:
                    value = n.getParameter(p).getValue(time)
                    if value.startswith('/'):
                        value = value[1:]
                    path = os.path.join(path, value)
                if path.strip() != l.strip():
                    isTarget = False

                if isTarget:
                    # this is the node we find
                    if return_top_node:
                        n = ng_traverseGroupUp(n)
                    nodes.update({l:n})
                    break
        if not nodes.has_key(l):
            nodes.update({l:None})

    return nodes

def getRootProducer(t='geometry'):
    # type='geometry' or 'render'
    if t=='geometry':
        return Nodes3DAPI.GetGeometryProducer()
    return Nodes3DAPI.GetRenderProducer()

def getLocationProducer(location_path, root_producer):
    return root_producer.getProducerByPath(location_path)

def getRootNode():
    return NodegraphAPI.GetRootNode()

def getWorldXform(locations=[]):
    # returned data: [(16 doubles), ...]
    if not isinstance(locations, list):
        locations = [locations]
    root_producer = getRootProducer()
    xform = []
    for l in locations:
        data = None
        location_producer = root_producer.getProducerByPath(l)
        if location_producer:
            data = location_producer.getFlattenedGlobalXform()
        xform.append(data)
    return xform

def findMethods(inst, include=''):
    # to be continue
    output = []
    inst_name = inst.__name__
    methods = [inst_name+'.'+m for m in eval('dir('+inst_name+')') if not m.startswith('__')]
    for i in methods:
        if include:
            if include.lower() in i.lower():
                output.append(i)
                output.extend( findMethods(i, include) )
        else:
            output.append(i)
    return output

def dir(dir_list, include=''):
    if include:
        return [m for m in dir_list if include.lower() in m.lower()]
    else:
        return dir_list

def findChildren(node, include='', search_for_name=True):
    # if search_for_name is False, then we try to match the type name
    output = []
    children = []
    try:
        children = node.getChildren()
    except:
        pass
    for i in children:
        if i.getType()=='Group':
            output.extend( findChildren(i, include) )
        if include:
            name = ''
            if search_for_name:
                name = i.getName().lower()
            else:
                name = i.getType().lower()
            if include.lower() in name:
                output.append(i)
        else:
            output.append(i)
    print output
    return output

def findList(l, target=''):
    output = []
    for i in l:
        try:
            if not isinstance(l, str):
                i = i.getName()
            if target.lower() in i.lower():
                output.append(i)
        except:
            pass
    print output

def sg_iteratorByType(parent_producer, type_='component', toLeaf=False):
    if parent_producer.getType() == type_:
        yield parent_producer
        if not toLeaf:
            return
    children_iter = parent_producer.iterChildren()
    for c in children_iter:
        for i in sg_iteratorByType(c, type_=type_, toLeaf=toLeaf):
            yield i

def sg_getChildLocations(parent_location, type_='component'):
    ''' this function return all children under the given location
        only if the expanded scene graph location is cached '''
    sgv = getSceneGraphView()
    root_producer = getRootProducer()
    children = sgv.getChildLocations(locationPath=parent_location, \
                    topLevelLocationPath=None, visibleOnly=False, \
                    allDescendants=True)
    locations_producers = []
    for c in children:
        producer = getLocationProducer(c, root_producer)
        if producer.getType() == type_:
            locations_producers.append(producer)
    return locations_producers

def ng_traverseUp(node, n_type, level=-1):
    '''
    this method only traverse the nodes in the same layer with the input node
    it will not go into the group node, or come out from the group node
    '''
    if not node or not n_type:
        return []
    result = []
    if level==0:
        return result
    input_ports = node.getInputPorts()
    # only consider logical inputs
    tmp = []
    for i in input_ports:
        try:
            tmp.append(node.getLogicalInputPort(i, 0)[0])
        except:
            pass
    input_ports = list(set(tmp))

    for i in input_ports:
        connected_ports = i.getConnectedPorts()
        for c in connected_ports:
            try:
                n = c.getNode()
                if n.getType().lower() != n_type.lower():
                    result.extend( ng_traverseUp(n, n_type, level-1) )
                else:
                    result.append(n)
            except:
                pass
    return result

def ng_traverseGroupDown(nodes=[]):
    '''
    recursively retrive the nodes in the node graph when meet the Group node
    '''
    if not isinstance(nodes, list):
        nodes = [nodes]
    output = nodes
    for n in nodes:
        if n.getType() == 'Group':
            tmp = n.getChildren()
            output.extend( ng_traverseGroupDown(tmp) )
    output = list(set(output))
    return output

def ng_traverseGroupUp(node):
    '''
    recursively traverse upward in the group node until hit the top layer
    '''
    parent = node.getParent()
    if not parent:
        return node
    if parent.getType()=='RootNode':
        return node
    return ng_traverseGroupUp(parent)

def traverseParameterGroup(params=[]):
    '''
    recursively retrieve the parameter objects when meet the group parameter
    '''
    if not isinstance(params, list):
        params = [params]
    output = params
    for p in params:
        if p.getType() == 'group':
            tmp = p.getChildren()
            output.extend( traverseParameterGroup(tmp) )
    output = list(set(output))
    return output

def setParameters(parameter_name_value_pair, node=[], time=0.0):
    '''
    set the given parameter and value on the selected(or given) node
    input parameter name and value should be a dict: {parameter_name:[value, time]}
    return parameters list
    '''
    if not node:
        sel = NodegraphAPI.GetAllSelectedNodes()
    else:
        sel = node
        if not isinstance(sel, list):
            sel = [sel]
    collections = []
    for s in sel:
        #get the parameter objects
        params = traverseParameterGroup(s.getParameters())
        for p in params:
            for (n,v) in parameter_name_value_pair.iteritems():
                if p.getFullName().lower().endswith(n.lower()):
                    if p.getType()=='group':
                        continue
                    p.setUseNodeDefault(False)
                    if type(v) in [float, long, int, str, tuple]:
                        p.setValue(v, time)
                        print p.getFullName()+': '+str(v)+' at time '+str(time)
                    else:
                        p.setValue(v[0], v[1])
                        print p.getFullName()+': '+str(v[0])+' at time '+str(v[1])
                    collections.append(p)
    collections = list(set(collections))
    return collections

def getParameters(parameter_name='', node=[], param_type='any', matchMode='tail'):
    '''
    set the given parameter and value on the selected(or given) node
    input parameter name should be a list or string
    the returned type is a dict if given the parameter_name: 
        {parameter_name:[parameter_object, ...]}
    or a list if the parameter_name is invalid, in this case, we simply list all parameters:
        [parameter_name, ...]
    '''
    if not node:
        sel = NodegraphAPI.GetAllSelectedNodes()
    else:
        sel = node
        if not isinstance(sel, list):
            sel = [sel]
    if not isinstance(parameter_name, list):
        parameter_name = [parameter_name]
    if parameter_name and parameter_name[0]:
        collections = {}
    else:
        collections = []

    for s in sel:
        #get the parameters
        params = traverseParameterGroup(s.getParameters())
        for p in params:
            if param_type!='any' and p.getType()!=param_type:
                continue
            if parameter_name and parameter_name[0]:
                for n in parameter_name:
                    if ( matchMode=='tail' and p.getFullName().lower().endswith(n.lower()) ) or \
                        ( matchMode=='include' and n.lower() in p.getFullName().lower() ):
                        if collections.has_key(n):
                            collections[n].append(p)
                        else:
                            collections.update({n:[p]})
                        print p.getFullName()
            else:
                collections.append(p)
                print p.getFullName()
    return collections
                    

def setParameterNodeGraph(parameter_name, value, time=1.0, t='', selected=False, recursive=False):
    '''
    this method set the given paramter to the given value on all the nodes in the node graph,
    if selected is True, then only selected nodes will be affected,
    if recursive is True, then the group nodes will be expanded recursivly if any,
    
    By default, we set the value at time 1.0, this can be changed by specifying the time, and
    node with any type will be targeted. If you want to shrink the nodes down to the type of 'Alembic_In' 
    for instance, then you can specify t='Alembic_In'

    obsoleted:
    if strictly is True, then we use strict name matching rule to look up the given parameters,
    otherwise it will be true if the lower case of the given parameter name is included in the lower 
    case of the parameter name on the nodes.
    '''
    if t and isinstance(t, str):
        nodes = NodegraphAPI.GetAllNodesByType(t)
    else:
        nodes = NodegraphAPI.GetAllNodes()
    if selected:
        sel_nodes = NodegraphAPI.GetAllSelectedNodes()
        if recursive:
            sel_nodes = ng_traverseGroupDown(sel_nodes)
        nodes = list(set(nodes).intersection(sel_nodes))
    # set attribute
    log = ''
    for n in nodes:
        # lets try to access the parameter directly
        param = n.getParameter(parameter_name)
        if param:
            param.setUseNodeDefault(False)
            param.setValue(value, time)
            log += ('%s: %s at time %s\n')%(param.getFullName(), str(value), str(time))
            continue
        # get the parameters' objects
        params = setParameters({parameter_name:[value, time]}, n)
        if params:
            log += ('%s: %s at time %s\n')%(params[0].getFullName(), str(value), str(time))
    if log:
        print log


def gafferThree_getLights(gaffer_node, light_location):
    if not gaffer_node.getType()=='GafferThree':
        return []
    root_package = gaffer_node.getRootPackage()
    root_location = gaffer_node.getRootLocation()
    light_location_relative = light_location.replace(root_location, '')
    # try to find the light by location name
    light_package = root_package.getChildPackage(light_location_relative)
    light_node = light_package.getPackageNode()
    return light_node

def getTransform(node, time=0.0):
    transform = {}
    transform_order = node.getParameter('transform.transformOrder')
    rotation_order = node.getParameter('transform.rotationOrder')
    translate = node.getParameter('transform.translate')
    rotate = node.getParameter('transform.rotate')
    scale = node.getParameter('transform.scale')
    if not transform_order or not rotation_order or not translate or not rotate or not scale:
        return transform
    transform_order = transform_order.getValue(time)
    rotation_order = rotation_order.getValue(time)
    tx = node.getParameter('transform.translate.x').getValue(time)
    ty = node.getParameter('transform.translate.y').getValue(time)
    tz = node.getParameter('transform.translate.z').getValue(time)
    rx = node.getParameter('transform.rotate.x').getValue(time)
    ry = node.getParameter('transform.rotate.y').getValue(time)
    rz = node.getParameter('transform.rotate.z').getValue(time)
    sx = node.getParameter('transform.scale.x').getValue(time)
    sy = node.getParameter('transform.scale.y').getValue(time)
    sz = node.getParameter('transform.scale.z').getValue(time)
    transform = {node:{}}
    transform[node].update({'transform_order':transform_order, 'rotation_order':rotation_order})
    transform[node].update({'translate':[tx,ty,tz], 'rotation':[rx,ry,rz], 'scale':[sx,sy,sz]})
    # compose local matrix
    matrix = km.matrix_mirror( km.matrix_compose(scale=[sx,sy,sz], angles=km.deg_to_rad( [rx,ry,rz]), \
                translate=[tx,ty,tz], axes=rotation_order) )
    transform[node].update({'matrix':list(matrix.reshape(1, matrix.size)[0])})
    return transform

def setTransform(node, translate=None, rotate=None, scale=None, transform_order=None, \
                    rotation_order=None, time=0.0):
    param_obj = None
    if transform_order:
        param_obj = node.getParameter('transform.transformOrder')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(transform_order, time)
    if rotation_order:
        param_obj = node.getParameter('transform.rotationOrder')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(rotation_order, time)
    if scale:
        param_obj = node.getParameter('transform.scale.x')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(scale[0], time)
        param_obj = node.getParameter('transform.scale.y')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(scale[1], time)
        param_obj = node.getParameter('transform.scale.z')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(scale[2], time)
    if rotate:
        param_obj = node.getParameter('transform.rotate.x')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(rotate[0], time)
        param_obj = node.getParameter('transform.rotate.y')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(rotate[1], time)
        param_obj = node.getParameter('transform.rotate.z')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(rotate[2], time)
    if translate:
        param_obj = node.getParameter('transform.translate.x')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(translate[0], time)
        param_obj = node.getParameter('transform.translate.y')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(translate[1], time)
        param_obj = node.getParameter('transform.translate.z')
        param_obj.setUseNodeDefault(False)
        param_obj.setValue(translate[2], time)
