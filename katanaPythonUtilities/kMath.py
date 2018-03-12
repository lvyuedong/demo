# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import numpy as np

def rad_to_deg(angle):
    if type(angle) in [float, int]:
        return angle/math.pi*180.0
    elif type(angle) in [list, np.ndarray]:
        angle = np.array(angle)
        angle = angle / math.pi * 180.0
        return angle

def deg_to_rad(angle):
    if type(angle) in [float, int]:
        return angle/180.0 * math.pi
    elif type(angle) in [list, np.ndarray]:
        angle = np.array(angle)
        angle = angle / 180.0 * math.pi
        return angle

def vector_norm(v):
    return np.linalg.norm(v)

def vector_unit(v):
    if isinstance(v, list):
        v = np.array(v)
    length = vector_norm(v)
    return v/length

def cross(v1, v2):
    # return nomalized cross product
    # v1 and v2 both should be a array like list
    return vector_unit( np.cross(v1, v2) )

def dot(v1, v2):
    return np.dot(v1,v2)

def subtract(v1, v2):
    return np.array([v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]])

def add(v1, v2):
    return np.array([v2[0]+v1[0], v2[1]+v1[1], v2[2]+v1[2]])

def multiply(v1, v2):
    return np.array([v2[0]*v1[0], v2[1]*v1[1], v2[2]*v1[2]])

def vector_reflect(v, n):
    if isinstance(v, list):
        v = np.array(v)
    if isinstance(n, list):
        n = np.array(n)
    n = vector_unit(n)
    v_dot_n = dot(v,n)
    if v_dot_n>0:
        v = -v
        v_dot_n = -v_dot_n
    r = v - 2*v_dot_n*n
    return r

def vector_to_rotation(v, face_axis='-z'):
    '''
    The default rotation order is XYZ
    we use -z as the vector direction
    '''
    v = vector_unit(v)
    pi_2 = math.pi * 0.5
    # deal with special case: the vector is aligned with world y axis
    rot = [0, 0, 0]
    if v[0]==0 and v[2]==0:
        if v[1]==0:
            return rot
        # suppose the vector is aligned with +y
        rot = [pi_2, 0, 0]
        # inverse if the vector is aligned with -y
        if v[1]<0:
            rot = [-pi_2, 0, 0]
        return rot
    # get the unit vector on the xz plane
    vector_xz = vector_unit(np.array([v[0],0,v[2]]))
    # use -z to get the rotation in y axis
    ry = math.acos(-vector_xz[2])
    if vector_xz[0]>0:
        ry = math.pi + math.pi - ry
    ry = math.fmod(ry, math.pi+math.pi)
    # use +y to get the rotation in x axis
    rx = math.asin(v[1])

    return np.array([rx, ry, 0])

def list_to_matrix(l, mirror=False):
    # only valid for 4x4, 1x4, 3x3, 1x3 matrix
    # if mirror is true, then 4x4 or 3x3 matrix elements will be mirrored against diagonal line
    if not isinstance(l, list):
        try:
            l = list(l)
        except:
            pass
    length = len(l)
    if length!=16 and length!=4 and length!=9 and length!=3:
        print 'Error, list_to_matrix needs 16, 9, 4 or 3 elements of array'
        return []
    matrix = None
    if length == 16:
        if mirror:
            matrix = np.array([ [l[0], l[4], l[8],  l[12]], \
                                   [l[1], l[5], l[9],  l[13]], \
                                   [l[2], l[6], l[10], l[14]], \
                                   [l[3], l[7], l[11], l[15]] ])
        else:
            matrix = np.array([ [l[0],  l[1],  l[2],  l[3]], \
                                   [l[4],  l[5],  l[6],  l[7]], \
                                   [l[8],  l[9],  l[10], l[11]], \
                                   [l[12], l[13], l[14], l[15]] ])
    elif length == 9:
        if mirror:
            matrix = np.array([ [l[0], l[3], l[6]], \
                                   [l[1], l[4], l[7]], \
                                   [l[2], l[5], l[8]] ])
        else:
            matrix = np.array([ [l[0], l[1], l[2]], \
                                   [l[3], l[4], l[5]], \
                                   [l[6], l[7], l[8]] ])
    elif length == 4:
        if mirror:
            matrix = np.array( [ [l[0]],  [l[1]],  [l[2]],  [l[3]] ] )
        else:
            matrix = np.array([ [l[0],  l[1],  l[2],  l[3]] ])
    elif length == 3:
        if mirror:
            matrix = np.array( [ [l[0]],  [l[1]],  [l[2]] ] )
        else:
            matrix = np.array([ [l[0],  l[1],  l[2]] ])

    return matrix

def matrix_identity(dim=4):
    return np.identity(dim)

def matrix_mirror(m):
    return list_to_matrix(list(m.reshape(1, m.size)[0]), mirror=True)

def matrix_mul(m1, m2):
    # the m1 and m2 should be a matrix
    if isinstance(m1, list):
        m1 = list_to_matrix(m1)
    if isinstance(m2, list):
        m2 = list_to_matrix(m2)
    if not isinstance(m1, np.ndarray) or not isinstance(m2, np.ndarray):
        return []
    if m1.ndim != m2.ndim:
        print 'Error, matrix_mul needs np.ndarray datas with same dimension'
        return []
    if m1.ndim!=2:
        print 'Error, matrix_mul needs data with 2 dimension np.ndarray datas'
        return []
    if m1.shape[1] != m2.shape[0]:
        print 'Error, matrix_mul can not multiply '+'%dx%d'%m1.shape+' with '+'%dx%d'%m2.shape+' matrix'
        return []
    
    matrix = np.zeros((m1.shape[0], m2.shape[1]))
    # we need mirror m2 to make accessing easy
    m2 = matrix_mirror(m2)
    for i in range(m1.shape[0]):
        for j in range(m2.shape[1]):
            ixj = 0
            for k in range(m1.shape[1]):
                ixj += m1[i][k] * m2[j][k]
            matrix[i][j] = ixj
    return np.array(matrix)

def matrix_inverse(matrix):
    """
    Return inverse of square transformation matrix.
    """
    return np.linalg.inv(matrix)

def is_same_matrix(m1, m2):
    if len(m1) != len(m2):
        return False
    if isinstance(m1, list):
        m1 = np.array(m1)
    if isinstance(m2, list):
        m2 = np.array(m2)
    return np.allclose(m1, m2)
