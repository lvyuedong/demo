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

    
    




