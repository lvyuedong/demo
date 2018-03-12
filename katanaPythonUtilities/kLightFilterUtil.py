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

import kCommonFunc as kcf
reload(kcf)
import transformations as tf
reload(tf)



def barndoorRmsToPxr(top=0.0, bottom=0.0, left=0.0, right=0.0, mode='expand', time=1.0):
    # this function convert barndoors attribute in RMS Light to parameters in Pxr light filter
    # note: the input angle should be greater than 0 and less than 90 degree
    # also, you should select the barn filter in scene graph of Katana to run this function
    # this function does changes the values of the selected nodes or scene graph location
    min_angle = 1.0
    top = min_angle if top<min_angle else (90.0-min_angle if top>(90.0-min_angle) else top)
    bottom = min_angle if bottom<min_angle else (90.0-min_angle if bottom>(90.0-min_angle) else bottom)
    left = min_angle if left<min_angle else (90.0-min_angle if left>(90.0-min_angle) else left)
    right = min_angle if right<min_angle else (90.0-min_angle if right>(90.0-min_angle) else right)
    max_angle = max([top, bottom, left, right])

    # get scene graph location of the selected light filters
    locations = kcf.getSelectedLocations()
    nodes = kcf.locationsToNodes(locations)

    for (l, n) in nodes.iteritems():
        if not n:
            continue
        # get parent light matrix
        light_location = os.path.dirname(l)
        lgt_matrix = tf.list_to_matrix(kcf.getWorldXform(light_location)[0])
        scale, shear, angles, trans, persp = tf.decompose_matrix(lgt_matrix)
        if scale[0]<=0 or scale[1]<=0 or scale[2]<=0:
            print 'Error: '+os.path.basename(light_location)+' has zero scale, ignored!'
            continue
        # calculate distance to the light, so that the angle between the light and filter meets the max angle
        dist_to_light_x = math.tan(max_angle/180.0*math.pi) * scale[0]
        dist_to_light_y = math.tan(max_angle/180.0*math.pi) * scale[1]
        dist_to_light = 0
        if mode=='expand':
            dist_to_light = max(dist_to_light_x, dist_to_light_y)
        else:
            dist_to_light = min(dist_to_light_x, dist_to_light_y)
        dist_to_light = 1
        # calculate refine shape of the barn door
        top_edge = (dist_to_light / math.tan(top/180.0*math.pi) - scale[1])/scale[1]
        bottom_edge = (dist_to_light / math.tan(bottom/180.0*math.pi) - scale[1])/scale[1]
        left_edge = (dist_to_light / math.tan(left/180.0*math.pi) - scale[0])/scale[0]
        right_edge = (dist_to_light / math.tan(right/180.0*math.pi) - scale[0])/scale[0]

        # let's set the parameters on the selected light filters
        # light filter is a group, so let's get their children and set the transform parameters
        light_create_nodes = [i for i in n.getChildren() if i.getType().lower()=='lightcreate']
        if not light_create_nodes:
            print 'Error: failed to find lightCreate node in '+os.path.basename(l)+"'s children, ignored!"
            continue
        param_value_dict = {'transform.translate.x':[0, time], \
                            'transform.translate.y':[0, time], \
                            'transform.translate.z':[-dist_to_light, time]}
        kcf.setParameters(param_value_dict, light_create_nodes[0])

        # set the refine edges of the barn door
        light_filter_nodes = [i for i in n.getChildren() if i.getType().lower()=='material']
        if not light_create_nodes:
            print 'Error: failed to find lightFilter material in '+os.path.basename(l)+"'s children, ignored!"
            continue
        param_value_dict = {'top.value':[top_edge, time], 'bottom.value':[bottom_edge, time], \
                            'left.value':[left_edge, time], 'right.value':[right_edge, time]}
        kcf.setParameters(param_value_dict, light_filter_nodes[0])

