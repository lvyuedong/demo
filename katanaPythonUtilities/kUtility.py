# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import shutil
import re
import numpy as np
import StringIO

from Katana import NodegraphAPI
from Katana import UI4
from Katana import Nodes3DAPI

import kCommonFunc as kcf
reload(kcf)
import kMath as km
reload(km)

def getDistance(a, b):
    # a and b should be the location string
    xforms = kcf.getWorldXform([a,b])
    a_position = (xforms[0][-4], xforms[0][-3], xforms[0][-2])
    b_position = (xforms[1][-4], xforms[1][-3], xforms[1][-2])
    return math.sqrt(sum( (a_position - b_position)**2 for a_position, b_position in zip(a_position, b_position)))

def getDistanceOfSelected(location=True):
    '''
    return the distance between the first two items in the selection lists
    you have to select something in the scene graph or viewer
    returned data: [(16 doubles), ...]
    By default, we get the selected location in the scene graph,
    if location is False, then we look up the node in the node graph,
    then convert the node to the location if possible
    '''
    sel = []
    if location:
        sel = kcf.getSelectedLocations()
    else:
        sel = kcf.nodesToLocations(getSelectedNodes())

    if len(sel)<2:
        print 'Error: please select two locations'
        return
    return getDistance(sel[0], sel[1])

def getRenderCamera():
    '''
    this method traverse upstream from the current viewed node to find the renderSettings node,
    then retrive the cameraName location from the renderSettings.
    If multiple renderSettings exists, we only use the first encounter.
    '''
    view_node = NodegraphAPI.GetViewNode()
    render_setting = kcf.ng_traverseUp(view_node, 'RenderSettings')
    if not render_setting:
        return None
    # we get camera matrix only from the first renderSettings
    cam_location = render_setting[0].getParameter('args.renderSettings.cameraName.value').getValue(0)
    #cam_matrix = kcf.getWorldXform(cam_location)
    return cam_location

def getViewer():
    '''
    get the viewer object from the Viewer Tab
    '''
    return UI4.App.Tabs.FindTopTab('Viewer')._OSGViewerPanel__viewerManager.getViewer()

def viewer_getPositionAndNormalAndPathByRayIntersection(ray_start, ray_end, viewer_obj):
    # ray_start and ray_end should be the tuple in world space
    # intersection only is performed behind the ray_end
    return viewer_obj.getPositionAndNormalAndPathByRayIntersection(ray_org, ray_dir)

def viewer_getSelectedFaceSet():
    # return selected face id, and the object
    # the returned dict can be fed into getGeoInfoAtFaceId method to get the vertex position
    viewer = getViewer()
    face_list = viewer.queryFaceSelection()
    obj = viewer.getSelection()
    return {'faceid':face_list, 'object':obj}

def getGeoInfoAtFaceId(face_list, obj):
    '''
    returned dict:
    { faceid:{'vertex':[[3 float list],...],
              'vertexid':[int,...]
              'center:[3 float list]'},
      ... 
    }
    '''
    if obj and isinstance(obj, list):
        obj = obj[0]
    root_producer = kcf.getRootProducer()
    geo_p = kcf.getLocationProducer(obj, root_producer)
    # collect datas
    point_P = geo_p.getAttribute('geometry.point.P').getData()
    p_tuple_size = geo_p.getAttribute('geometry.point.P').getTupleSize()
    face_index = geo_p.getAttribute('geometry.poly.startIndex').getData()
    face_index_length = len(face_index)
    vertex_index = geo_p.getAttribute('geometry.poly.vertexList').getData()

    info = {}
    for f_id in face_list:
        f_id = int(f_id)
        if f_id >= face_index_length - 1:
            continue
        face_index_range = range(face_index[f_id], face_index[f_id+1])
        vertex_index_list = [vertex_index[i] for i in face_index_range]
        point_list = [point_P[i*p_tuple_size:i*p_tuple_size+3] for i in vertex_index_list]
        info.update({f_id:{'vertex':point_list, \
                    'vertexid':vertex_index_list, \
                    'center':calculateCenterOfFace(point_list)}})
    return info

def calculateCenterOfFace(vertex_list):
    if len(vertex_list)==1:
        return vertex_list[0]
    if len(vertex_list)<1:
        return []
    center = np.array([0.0,0.0,0.0])
    for i in range(len(vertex_list)):
        center += np.array(vertex_list[i])
    center /= float(len(vertex_list))
    return list(center)

def calculateFaceforwardNormal(geo_info, camera_location, obj_location):
    '''
    calculate the face normal forward to the camera
    returned data is [normal, face_center, cam_position] in world space
    '''
    if not geo_info:
        print 'Error, invalid geo_info'
        return []
    vertex_list_local = geo_info[geo_info.keys()[0]]['vertex']
    face_center_local = geo_info[geo_info.keys()[0]]['center']
    # get object matrix
    obj_matrix = kcf.getWorldXform(obj_location)
    if not obj_matrix:
        print 'Error, failed to get world matrix at location: '+obj_location
        return []
    # convert to world space
    vertex_list = []
    face_center = []
    obj_matrix = km.list_to_matrix(obj_matrix[0])
    if not km.is_same_matrix(obj_matrix, km.matrix_identity(4)):
        for v in vertex_list_local:
            vertex_list.append( list(km.matrix_mul(v+[1], obj_matrix)[0][:-1]) )
        face_center.extend( list(km.matrix_mul(face_center_local+[1], obj_matrix)[0][:-1]) )
    else:
        vertex_list = vertex_list_local
        face_center = face_center_local

    # get the normal
    if len(vertex_list)<3:
        print 'Error, need at least three vertices to calculate the face normal'
        return []
    v0 = km.subtract( vertex_list[0], vertex_list[1] )
    v1 = km.subtract( vertex_list[1], vertex_list[2] )
    normal = km.vector_unit( km.cross(v0, v1) )

    # get the camera matrix
    cam_matrix = kcf.getWorldXform(camera_location)
    if not cam_matrix or not cam_matrix[0]:
        print 'Error, failed to get camera matrix'
        return []
    cam_matrix = km.list_to_matrix(list(cam_matrix[0]))
    cam_position = [cam_matrix[3][0], cam_matrix[3][1], cam_matrix[3][2]]
    # get unit z from camera in world space
    cam_z = km.vector_unit( km.matrix_mul( km.list_to_matrix([0,0,1,0]), cam_matrix )[0][:-1] )
    # test face forward
    if km.dot(cam_z, normal)<0:
        normal = -normal
    return [list(normal), face_center, cam_position]

def getSelectedFaceNormal():
    # returned data is [normal, face center, camera position]
    # get geometry info
    tmp = viewer_getSelectedFaceSet()
    face_list = tmp['faceid']
    obj = tmp['object']
    if not face_list or not obj:
        print 'Error, please select one face on the geometry'
        return []
    geo_info = getGeoInfoAtFaceId(face_list, obj)
    # get render camera and calculate the normal
    cam_location = getRenderCamera()
    if not cam_location:
        print 'Error, failed to find renderSettings node, please view any node downstream the renderSettings'
        return []
    return calculateFaceforwardNormal(geo_info, cam_location, obj)

def setSelectedLightAtReflectedPosition(normal, face_center, cam_position, \
                                        invert_normal=False, time=0.0, print_log=False):
    '''
    the normal should be the returned data from getSelectedFaceNormal
    '''
    normal = np.array(normal)
    if invert_normal:
        normal = -normal
    face_center = np.array(face_center)
    cam_position = np.array(cam_position)
    cam_to_face_vector = face_center - cam_position
    reflect = km.vector_unit( km.vector_reflect(cam_to_face_vector, normal) )
    if print_log:
        print 'reflect vector'
        print reflect

    root_producer = kcf.getRootProducer()
    # get selected light
    light_locations = kcf.getSelectedLocations()
    for l in light_locations:
        # if the selected item is light?
        location_producer = root_producer.getProducerByPath(l)
        if location_producer.getType().lower() != 'light':
            continue
        light_Node = kcf.locationsToNodes(l)[l]
        # get light world matrix
        matrix_world_light = kcf.getWorldXform(l)
        if not matrix_world_light:
            print light_Node.getName()+": Failed to get light's world matrix, ignored."
            continue
        matrix_world_light = km.list_to_matrix( matrix_world_light[0] )
        if print_log:
            print 'light world matrix'
            print matrix_world_light
        # get light local matrix
        transform = kcf.getTransform(light_Node)
        if print_log:
            print 'light transform'
            print transform
        matrix_local_light = km.list_to_matrix( transform[light_Node]['matrix'] )
        if print_log:
            print 'light local matrix'
            print matrix_local_light
        # get the intermediate matrix: M_i = M_light_local_inverse * M_world
        matrix_intermediate = km.matrix_mul( km.matrix_inverse(matrix_local_light), matrix_world_light )
        if print_log:
            print 'intermediate matrix'
            print matrix_intermediate
        # compose the reflect world matrix
        distance_light_to_face = float( km.vector_norm(matrix_world_light[3][:-1] - face_center) )
        if print_log:
            print 'light to face distance'
            print distance_light_to_face
        position = reflect * distance_light_to_face + face_center
        rotation = km.vector_to_rotation(-reflect)
        if print_log:
            print 'light new position'
            print position
            print 'light new rotation'
            print rotation
            print km.rad_to_deg(rotation)
        matrix_reflect = km.matrix_compose(scale=np.array([1,1,1]), angles=rotation, translate=position)
        if print_log:
            print 'world reflect matrix'
            print matrix_reflect
        # compute the new light local matrix: M_light = M_reflect * M_intermediate_inverse
        new_matrix_light = km.matrix_mul(matrix_reflect, km.matrix_inverse(matrix_intermediate))
        if print_log:
            print 'new light local matrix'
            print new_matrix_light
        # then get the translate, rotation and scale components
        scale, shear, angles, translate, perspective = km.matrix_decompose(new_matrix_light)
        angles = km.rad_to_deg(angles)
        print (light_Node.getName()+', target transform: \ntranslate: [%f, %f, %f]\n'+\
            'rotate: [%f, %f, %f]\nscale: [%f, %f, %f]')%(translate[0], translate[1], translate[2],\
            angles[0], angles[1], angles[2], scale[0], scale[1], scale[2])
        # let's move the light!
        kcf.setTransform(light_Node, translate=list(translate), rotate=list(angles), \
                            scale=list(scale), rotation_order='XYZ')
        # change the center of interest at the face center
        kcf.setParameters({'centerOfInterest':distance_light_to_face}, light_Node)

def selectSceneGraphByBound(location=None, \
        max_height=999999, max_width=999999, max_depth=999999):
    ''' this function can be used to filter out the bounding boxes
        whose dimension is smaller than the given value '''
    root_producer = kcf.getRootRroducer()
    if not location:
        location = kcf.getSelectedLocations()
        if not location:
            print 'Please select a location in scene graph to proceed!'
            return False
    if not isinstance(location, list):
        location = [location]
    
    locations = []
    for l in location:
        location_producer = root_producer.getProducerByPath(l)
        for i in kcf.sg_iteratorByType(location_producer, type_='component', to_leaf=False):
            bounds = getBound(i)
            width = abs(bounds[1] - bounds[0])
            height = abs(bounds[3] - bounds[2])
            depth = abs(bounds[5] - bounds[4])
            if height < max_height and width < max_width and depth < max_depth:
                locations.append(i.getFullName())
    if locations:
        kcf.selectLocations(locations)
    return True
        
def getBound(sg_location):
    ''' if there is no bound info on the current location,
        it will find recursivly the bound in the children location '''
    if not sg_location:
        return []
    location_producer = None
    if isinstance(sg_location, str):
        root_producer = kcf.getRootRroducer()
        location_producer = root_producer.getProducerByPath(sg_location)
    else:
        location_producer = sg_location
    bound_attr = location_producer.getAttribute('bound')
    if not bound_attr:
        # find the child bounds
        bounds_collect = []
        bounds = []
        for c in location_producer.iterChildren():
            tmp = getBound(c)
            if tmp:
                bounds_collect.append(tmp)
        # calculate the combined bounds
        if bounds_collect:
            bounds = range(6)
            for i in range(0, 6, 2):
                bounds[i] = min([b[i] for b in bounds_collect])
            for i in range(1, 6, 2):
                bounds[i] = max([b[i] for b in bounds_collect])
        return bounds
    local_bound = location_producer.getAttribute('bound').getData()
    parent_matrix = kcf.getWorldXform(location_producer.getFullName())
    if not parent_matrix:
        return local_bound
    parent_matrix = km.list_to_matrix(parent_matrix[0])
    if km.is_same_matrix(parent_matrix, km.matrix_identity()):
        return local_bound
    # convert local bound to world space
    # caculate 8 corners of bounding box
    bmin = [local_bound[0], local_bound[2], local_bound[4]]
    bmax = [local_bound[1], local_bound[3], local_bound[5]]
    ftr = [bmax[0], bmax[1], bmax[2]]
    fbr = [bmax[0], bmin[1], bmax[2]]
    fbl = [bmin[0], bmin[1], bmax[2]]
    ftl = [bmin[0], bmax[1], bmax[2]]
    btr = [bmax[0], bmax[1], bmin[2]]
    bbr = [bmax[0], bmin[1], bmin[2]]
    bbl = [bmin[0], bmin[1], bmin[2]]
    btl = [bmin[0], bmax[1], bmin[2]]
    # convert to world space
    ftr = km.matrix_mul( km.list_to_matrix(ftr+[1]), parent_matrix )[0][:-1]
    fbr = km.matrix_mul( km.list_to_matrix(fbr+[1]), parent_matrix )[0][:-1]
    fbl = km.matrix_mul( km.list_to_matrix(fbl+[1]), parent_matrix )[0][:-1]
    ftl = km.matrix_mul( km.list_to_matrix(ftl+[1]), parent_matrix )[0][:-1]
    btr = km.matrix_mul( km.list_to_matrix(btr+[1]), parent_matrix )[0][:-1]
    bbr = km.matrix_mul( km.list_to_matrix(bbr+[1]), parent_matrix )[0][:-1]
    bbl = km.matrix_mul( km.list_to_matrix(bbl+[1]), parent_matrix )[0][:-1]
    btl = km.matrix_mul( km.list_to_matrix(btl+[1]), parent_matrix )[0][:-1]
    # recaculate bounding box
    bmin[0] = min(ftr[0], fbr[0], fbl[0], ftl[0], btr[0], bbr[0], bbl[0], btl[0])
    bmin[1] = min(ftr[1], fbr[1], fbl[1], ftl[1], btr[1], bbr[1], bbl[1], btl[1])
    bmin[2] = min(ftr[2], fbr[2], fbl[2], ftl[2], btr[2], bbr[2], bbl[2], btl[2])
    bmax[0] = max(ftr[0], fbr[0], fbl[0], ftl[0], btr[0], bbr[0], bbl[0], btl[0])
    bmax[1] = max(ftr[1], fbr[1], fbl[1], ftl[1], btr[1], bbr[1], bbl[1], btl[1])
    bmax[2] = max(ftr[2], fbr[2], fbl[2], ftl[2], btr[2], bbr[2], bbl[2], btl[2])
    return [bmin[0], bmax[0], bmin[1], bmax[1], bmin[2], bmax[2]]

def getBoundCenter(sg_location):
    bounds = getBound(sg_location)
    center_x = bounds[0] + (bounds[1] - bounds[0])/2.0
    center_y = bounds[2] + (bounds[3] - bounds[2])/2.0
    center_z = bounds[4] + (bounds[5] - bounds[4])/2.0
    return [center_x, center_y, center_z]

def getBounds(location_list=None):
    if not location_list:
        location_list = kcf.getSelectedLocations()
    bounds_list = []
    for l in location_list:
        bounds = getBound(l)
        width = abs(bounds[1] - bounds[0])
        height = abs(bounds[3] - bounds[2])
        depth = abs(bounds[5] - bounds[4])
        bounds_list.append((height, width, depth))
    return bounds_list

def sg_expandToComponent(location, sgv=None, root_location='/root', collapse_children=True):
    if not sgv:
        sgv = kcf.getSceneGraphView()
    parent_location = os.path.dirname(location)
    try:
        if not sgv.isLocationExpanded(root_location, parent_location):
            sgv.scrollToLocation(root_location, location)
        if collapse_children and sgv.isLocationExpanded(root_location, location):
            sg.setLocationCollapsed(root_location, location)
    except:
        print traceback.format_exc()
        
def sg_expandLocation(location, sgv=None, root_location='/root'):
    if location == '/' or location == '/root':
        return
    if not sgv:
        sgv = kcf.getSceneGraphView()
    if not sgv.isLocationExpanded(root_location, location):
        sgv.setLocationExpanded(root_location, location)
    parent_location = os.path.dirname(location)
    sg_expandLocation(parent_location, sgv, root_location)

def getCameraData(cam_location):
    data = {}
    root_producer = kcf.getRootProducer()
    data['producer'] = root_producer.getProducerByPath(cam_location)
    data['xform'] = data['producer'].getFlattenedGlobalXform()
    # in katana, fov is vertical angle of view
    data['fov_vertical'] = data['producer'].getAttribute('geometry.fov').getData()[-1]
    data['left'] = data['producer'].getAttribute('geometry.left').getData()[-1]
    data['right'] = data['producer'].getAttribute('geometry.right').getData()[-1]
    data['bottom'] = data['producer'].getAttribute('geometry.bottom').getData()[-1]
    data['top'] = data['producer'].getAttribute('geometry.top').getData()[-1]
    data['ratio'] = (abs(data['left']) + abs(data['right'])) / (abs(data['bottom']) + abs(data['top']))
    data['fov_horizontal'] = data['fov_vertical'] * data['ratio']
    data['position'] = [data['xform'][-4], data['xform'][-3], data['xform'][-2]]
    cam_matrix = km.list_to_matrix( list(data['xform']) )
    cam_y = km.vector_unit( km.matrix_mul( km.list_to_matrix([0,1,0,0]), cam_matrix )[0][:-1] )
    cam_z = km.vector_unit( km.matrix_mul( km.list_to_matrix([0,0,1,0]), cam_matrix )[0][:-1] )
    data['up'] = [cam_y[0], cam_y[1], cam_y[2]]
    data['forward'] = [-cam_z[0], -cam_z[1], -cam_z[2]]
    return data

def filterTypeMap(type_):
    if 'component' in type_.lower():
        return 'component'
    if 'light' in type_.lower():
        return 'light'
    if 'instance' in type_.lower():
        return 'instance'
    
def nodeTypeMap(type_):
    if 'prune' in type_.lower():
        return 'Prune'

def frustumSelectionIterator(location=None, filter_type='component', fov_extend_h=0, fov_extend_v=0, \
        cam_location='', inverse_selection=True, animation=False, step=5, \
        nearD=0.1, farD=99999999, debug=False):
    ''' return the list of location within the frustum of camera. The filter_type
        should be component if the component represents the bounding box.
        
        we make this function iterator(generator), so the pyqt progress bar can benefit
        from the yield statment in order to know the progress of the running function.
    '''
    root_producer = kcf.getRootProducer()
    sgv = kcf.getSceneGraphView()
    if not location:
        location = kcf.getSelectedLocations()
        if not location:
            yield 'Error: Please select a location in the scene graph to proceed!'
            return
    if not isinstance(location, list):
        location = [location]
        
    filter_type = filterTypeMap(filter_type)
    
    locations_inside_list = []
    locations_outside_list = []
    
    current_frame = NodegraphAPI.NodegraphGlobals.GetCurrentTime()
    start_frame = NodegraphAPI.NodegraphGlobals.GetInTime()
    end_frame = NodegraphAPI.NodegraphGlobals.GetOutTime()
    frames = range(start_frame, end_frame+1, step)
    if end_frame not in frames:
        frames.append(end_frame)
    if not animation:
        frames = [current_frame]
    
    progress = 0
    progress_step = 100.0 / len(frames)
    
    for f in frames:
        yield 'frame' + str(f) + '\nGet camera matrix datas...'
        NodegraphAPI.NodegraphGlobals.SetCurrentTime(f)
        cam_data = getCameraDatas(cam_location)
        if fov_extend_h != 0 or fov_extend_v != 0:
            cam_data['fov_horizontal'] += fov_extend_h
            cam_data['fov_vertical'] += fov_extend_v
            cam_data['ratio'] = cam_data['fov_horizontal'] / cam_data['fov_vertical']
        frustum = km.Frustum()
        frustum.nearD = nearD
        frustum.farD = farD
        frustum.setCamInternals(cam_data['fov_vertical'], cam_data['ratio'])
        frustum.setCamDef(cam_data['position'], cam_data['forward'], cam_data['up'])
        if debug:
            # put the sphere in the corner of frustum to visually see if we get
            # the correct frustum shape
            print(cam_data['ratio'], cam_data['fov_horizontal'], cam_data['fov_vertical'])
            nodes = kcf.getSelectedNodes()
            corners = [frustum.ntl, frustum.ntr, frustum.nbl, frustum.nbr, \
                      frustum.nc, frustum.fc]
            for i in range(6):
                if i > len(nodes) - 1:
                    break
                kcf.setTransform(nodes[i], translate=list(corners[i]), scale=[10,10,10])
            return
        sub_process = 0
        sub_process_step = progress_step / 100.0
        yield 'start to iterate scene graph locations...'
        for l in location:
            location_producer = root_producer.getProducerByPath(l)
            for i in kcf.sg_iteratorByType(location_producer, type_=filter_type, to_leaf=False):
                bounds = getBound(i)
                if type_ == 'light':
                    bounds = []
                    # if the type is mesh light without bbox, or one of the rect, sphere,
                    # disk light, we use center of point to decide the visibility in frustum
                    # instead of bbox
                    light_shader = i.getAttribute('material.prmanLightShader').getData()
                    if not light_shader:
                        # light without valid light shader, skip
                        continue
                    light_shader = light_shader[0].lower()
                    if 'mesh' not in light_shader and 'rect' not in light_shader \
                        and 'sphere' not in light_shader and 'disk' not in light_shader:
                        continue
                    if 'mesh' in light_shader:
                        # if it's mesh light, let's check the source geometry
                        src = i.getAttribute('geometry.areaLightGeometrySource').getData()
                        if src:
                            bounds = getBound(root_producer.getProducerByPath(src[0]))
                isOutside = False
                if not bounds:
                    # if bounding box info is invalid, we try to use xform instead
                    world_xform = kcf.getWorldXform(i.getFullName())
                    if not world_xform:
                        continue
                    world_xform = world_xform[0]
                    center = world_xform[-4:-1]
                    if frustum.pointInFrustum(center) == frustum.status['outside']:
                        isOutside = True
                else:
                    aabox = km.AABox( bbox_list=bounds )
                    if frustum.boxInFrustum(aabox) == frustum.status['outside']:
                        isOutside = True
                    
                if isOutside:
                    locations_outside_list.append(i.getFullName())
                else:
                    locations_inside_list.append(i.getFullName())

                if sub_process < progress_step:
                    sub_process += sub_process_step
                    yield math.floor(progress + sub_process)
                    
        progress += progress_step
        yield math.floor(progress)
    
    locations_inside_list = list(set(locations_inside_list))
    locations_outside_list = list(set(locations_outside_list))
    locations_outside_list = list(set(locations_outside_list).difference(locations_inside_list))
    
    yield 'Completed!'
    if inverse_selection:
        yield locations_outside_list
        return
    yield locations_inside_list
    
def frustumSelection(*args, **kargs):
    locations_list = []
    for i in frustumSelectionIterator(*args, **kargs):
        if isinstance(i, list):
            locations_list = i
            break
    return locations_list

def createFrustumNode(prune_list=None, *args, **kargs):
    if not prune_list:
        prune_list = frustumSelection(*args, **kargs)
    if not prune_list:
        print('There is nothing to be added to the prune list, make sure you select the correct scene graph location')
        return
    prune = kcf.createNode('Prune')
    # get the CEL parameter ( parameter is named 'cel' )
    cel_param = prune.getParameter('cel')
    # set the value
    cel_param.setValue('(' + ' '.join(prune_list) + ')', 0)
    # rename prune node
    prune.setName('Prune_outOfCameraView')
    return prune

def compareHierarchy(src_location='', dst_location='', type_=['subdmesh', 'polygon']):
    '''compare children of selected two locations. If any child location is identical,
    this function will return the two locations as source and destination.
    returned data: [(src1, dst1), (src2, dst2), ...]
    '''
    root_producer = kcf.getRootProducer()
    sgv = kcf.getSceneGraphView()
    if not src_location or not dst_location:
        locations = kcf.getSelectedLocations()
        if not location:
            print 'Please select source and destination location in scene graph to proceed!'
            return []
        if len(locations) < 2:
            print 'Please select both source and destination location'
            return []
        src_location = locations[0]
        dst_location = locations[1]
    src_producer = kcf.getLocationProducer(src_location, root_producer)
    dst_producer = kcf.getLocationProducer(dst_location, root_producer)
    # get full children hierarchy
    src_hierarchy = [i.getFullName().replace(src_location, '') for i in \
                     kcf.sg_iteratorByType(src_producer, type_=type_, to_leaf=False)]
    dst_hierarchy = [i.getFullName().replace(dst_location, '') for i in \
                     kcf.sg_iteratorByType(dst_producer, type_=type_, to_leaf=False)]
    # let's get the common items
    common_items = [(src_location+i, dst_location+i) for i in \
                   list(set(src_hierarchy).intersection(dst_hierarchy))]
    return common_items

def createHierarchyCopyNode(*args, **kargs):
    hierarchy_list = compareHierarchy(*args, **kargs)
    hierarchy_node = kcf.createNode('HierarchyCopy')
    parameter = hierarchy_node.getParameter('copies')
    for i in hierarchy_list:
        src_location = i[0]
        dst_location = i[1]
        hierarchy_node.AddGroup()
        index = parameter.getNumChildren() - 1
        name = parameter.getChildByIndex(index).getName()
        hierarchy_node.getParameter('copies.'+name+'.sourceLocation').setValue(src_location, 0)
        hierarchy_node.getParameter('copies.'+name+'.destinationLocations.i0').setValue(dst_location, 0)

def findChildLocation(locations='', type_='light', parameters=[], select=True):
    '''
    find any child under locations whose type is given type_, and
    has the given parameter and value pairs. if the value is *, then
    child will be return if the parameter name matches.
    
    attribute example:
    light or light material lightGroup -> 'material.prmanLightParams.lightGroup'
    light meshLightGeometry -> 'geometry.areaLightGeometrySource'
    '''
    if not locations:
        locations = kcf.getSelectedLocations()
        if not locations:
            print 'Error: Please select a location in scene graph to proceed!'
            return []
    if not isinstance(locations, list):
        locations = [locations]
        
    collection = []
    root_producer = kcf.getRootProducer()
    for l in locations:
        location_producer = root_producer.getProducerByPath(l)
        for c in kcf.sg_iteratorByType(location_producer, type_=type_, to_leaf=True):
            attr = c.getAttribute(parameters[0])
            if not attr:
                continue
            value = attr.getValue()
            if parameters[1] == '*' \
                    or (isinstance(value, str) and value.lower() == parameters[1].lower()) \
                    or value == parameters[1]:
                collection.append(c.getFullName))
        collection = list(set(collection))
        
    if select:
        for c in collection:
            sg_expandLocation(c)
        kcf.selectLocations(collection)
    return collection

def excludeLocationList(node=None, exclude_location_list=[]):
    '''exclude the given list from the selected node.
    for example, exclude the given location from the list of prune node'''
    if not node:
        node = kcf.getSelectedNodes()
        if not node:
            print 'Error: Please select a node in node graph to proceed!'
            return []
        node = node[0]
    if not exclude_location_list:
        return []
    cel = node.getParameter('cel')
    cel_string = cel.getValue(0)
    cel_string_subtract_difference = ''
    cel_string_only_difference = ''
    is_difference = False
    for i in cel_string:
        if i == '+' or i == '^':
            if_difference = False
            continue
        if i == '-':
            is_difference = True
            continue
        if is_difference:
            cel_string_only_difference += i
            continue
        cel_string_subtract_difference += i
        
    locations = cel_string_subtract_difference.replace('(', ' ').replace(')', ' ').replace('+', ' ').replace('^', ' ').replace('-', ' ').split()
    locations_exclude = []
    for l in locations:
        for e in exclude_location_list:
            if l in e:
                locations_exclude.append(l)
                break
    locations_exclude = list(set(locations_exclude))
    if not locations_exclude:
        return []
    cel_string += ' - (' + ' '.join(locations_exclude) + ')'
    cel.setValue('', 0)
    cel.setValue(cel_string, 0)
    return locations_exclude

def searchAndReplaceLocationList(node=None, search='', replace=''):
    '''search the specified keyword in the location list of any node with cel location.
    if replace is empty, then this method only find the list, otherwise, replace.
    user should be expected to select some node in nodegraph'''
    if not node:
        node = kcf.getSelectedNodes()
        if not node:
            print 'Error: Please select a node in node graph to proceed!'
            return []
        node = node[0]
    cel = node.getParameter('cel')
    cel_string = cel.getValue(0)
    locations = cel_string.replace('(', ' ').replace(')', ' ').replace('+', ' ').replace('^', ' ').replace('-', ' ').split()
    locations_filtered = []
    for l in locations:
        if search in l:
            locations_filtered.append(l)
            
    if replace:
        cel.setValue('', 0)
        cel_string = cel_string.replace(search, replace)
        cel.setValue(cel_string, 0)
    return locations_filtered

def getAbsolutePath(current_path, relative_path):
    tmp = relative_path.split('/')
    go_upper_count = tmp.count('..')
    return os.path.join( '/'.join(current_path.split('/')[:-go_upper_count]), \
                        '/'.join(tmp[go_upper_count:]) )

def findConstraintTargets(locations='', select=True):
    '''this function will try to iterate all of the children and find the constrain targets,
    then select those targets'''
    if not locations:
        locations = kcf.getSelectedLocations()
        if not locations:
            print 'Error: Please select a location in scene graph to proceed!'
            return []
    if not isinstance(locations, list):
        locations = [locations]
        
    targets = []
    root_producer = kcf.getRootProducer()
    for l in locations:
        location_producer = root_producer.getProducerByPath(l)
        for c in kcf.sg_iteratorByType(location_producer):
            xform = c.getAttribute('xform')
            if not xform:
                continue
            child_list = xform.childList()
            for attr_name, attr_obj in child_list:
                t = c.getAttribute('xform.'+attr_name+'.target')
                if t:
                    targets.append( getAbsolutePath(c.getFullName(), t.getValue()) )
    targets = list(set(targets))
    if select:
        for c in targets:
            sg_expandLocation(c)
        kcf.selectLocations(targets)
    return targets


    
