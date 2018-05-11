# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import numpy as np

def list2array(v):
    if isinstance(v, list):
        return np.array(v)
    return v

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
    # v1 can be np array or a list
    return np.linalg.norm(v)

def vector_unit(v):
    if isinstance(v, list):
        v = np.array(v)
    length = vector_norm(v)
    return v/length

def cross(v1, v2):
    # return nomalized cross product
    # v1 and v2 both can be np array or a list
    return vector_unit( np.cross(v1, v2) )

def dot(v1, v2):
    # v1 and v2 both can be np array or a list
    return np.dot(v1,v2)

def subtract(v1, v2):
    if isinstance(v1, list) and isinstance(v2, list):
        return np.array([v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]])
    return v1 - v2

def add(v1, v2):
    if isinstance(v1, list) and isinstance(v2, list):
        return np.array([v2[0]+v1[0], v2[1]+v1[1], v2[2]+v1[2]])
    return v1 + v2

def multiply(v1, v2):
    if isinstance(v1, list) and isinstance(v2, list):
        return np.array([v2[0]*v1[0], v2[1]*v1[1], v2[2]*v1[2]])
    return v1 * v2

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

'''
The following class comes from
http://cgvr.informatik.uni-bremen.de/teaching/cg_literatur/lighthouse3d_view_frustum_culling/index.html
with minor modification and bug fix
'''
class Plane():
    ''' class of plane. define a plane by three points or by
        one normal and one point. distance method to calculate
        the distance from point to plane'''
    def __init__(self, v1=None, v2=None, v3=None):
        self.normal = None
        self.point = None
        self.d = None
        if v1 != None and v2 != None and v3 != None:
            self.set3Points(v1, v2, v3)
            
    def set3Points(self, v1, v2, v3):
        aux1 = subtract(v1, v2)
        aux2 = subtract(v3, v2)
        self.normal = vector_unit(cross(aux2, aux1))
        self.point = list2array(v2)
        self.d = -(self.normal[0] * self.point[0] + \
                   self.normal[1] * self.point[1] + \
                   self.normal[2] * self.point[2])
        
    def setNormalAndPoint(self, normal, point):
        self.normal = vector_unit(normal)
        self.point = list2array(point)
        self.d = -(self.normal[0] * self.point[0] + \
                   self.normal[1] * self.point[1] + \
                   self.normal[2] * self.point[2])
        
    def setCoefficients(self, a, b, c, w):
        self.normal = list2array([a,b,c])
        l = vector_norm(self.normal)
        self.normal = vector_unit(self.normal)
        self.d = w/l
        
    def getDistance(self, p):
        p = list2array(p)
        return self.d + (self.normal[0] * p[0] + self.normal[1] * p[1] + \
                   self.normal[2] * p[2])
    
    
class AAbox():
    ''' define axis aligned bounding box class '''
    def __init__(self, bbox_list=None, xmin=None, xmax=None, ymin=None, \
                 ymax=None, zmin=None, zmax=None):
        if bbox_list:
            self.xmin, self.xmax = bbox_list[0], bbox_list[1]
            self.ymin, self.ymax = bbox_list[2], bbox_list[3]
            self.zmin, self.zmax = bbox_list[4], bbox_list[5]
        else:
            self.xmin, self.xmax = xmin, xmax
            self.ymin, self.ymax = ymin, ymax
            self.zmin, self.zmax = zmin, zmax
        self.radious = 0
        
    def getVertexP(self, normal):
        ''' given the plane normal direction, return the maximum positive corner
            of the bounding box '''
        normal = list2array(normal)
        p = list2array([self.xmin, self.ymin, self.zmin])
        if normal[0] >= 0:
            p[0] = self.xmax
        if normal[1] >= 0:
            p[1] = self.ymax
        if normal[2] >= 0:
            p[2] = self.zmax
        return p
    
    def getVertexN(self, normal):
        ''' given the plane normal direction, return the miniumu negative corner
            of the bounding box '''
        normal = list2array(normal)
        n = list2array([self.xmax, self.ymax, self.zmax])
        if normal[0] >= 0:
            n[0] = self.xmin
        if normal[1] >= 0:
            n[1] = self.ymin
        if normal[2] >= 0:
            n[2] = self.zmin
        return n
    
    def getRadius():
        self.radius = vector_norm(subtract([self.xmax, self.ymax, self.zmax], \
                                           [self.xmin, self.ymin, self.zmin]))
        return self.radius
    
class Frustum():
    ''' define frustum of camera, method of deciding if the given bounding box
        in the frustum '''
    def __init__(self):
        self.status = {'outside':0, 'intersect':1, 'inside':2}
        # six planes composed of the frustum volume
        self.planes = {'top':None, 'bottom':None, 'left':None, 'right':None, 'near':None, 'far':None}
        # four corner of the near plane, ntl means near top left
        self.ntl, self.ntr, self.nbl, self.nbr = None, None, None, None
        self.ftl, self.ftr, self.fbl, self.fbr = None, None, None, None
        self.nearD, self.farD = 0.1, 99999999
        self.ratio = None
        self.angle = None   # vertical fov
        self.tang = None    # tangent of fov
        # width and height of near and far plane
        self.nw, self.nh, self.fw, self.fh = None, None, None, None
        # center of near and far plane
        self.nc, self.fc = None, None
        # axis of camera in world space
        self.X, self.Y, self.Z = None, None, None
        
    def setCamInternals(self, angle, ratio, nearD=None, farD=None):
        # parameter angle should be the vertical fov
        # by default, the fov in katana is the vertical fov
        self.ratio = ratio
        self.angle = angle
        if nearD != None: self.nearD = nearD
        if farD != None: self.farD = farD
        self.tang = math.tan(self.angle * math.pi / 360.0)
        self.nh = self.nearD * self.tang
        self.nw = self.nh * self.ratio
        self.fh = self.farD * self.tang
        self.fw = self.fh * self.ratio
        
    def setCamDef(self, position, forward, up):
        ''' input the position, forward and up vector of camera,
            caculate the axis and eight corners of the planes '''
        p = list2array(position)
        f = list2array(forward)
        u = list2array(up)
        self.Z = -vector_unit(f)
        self.Y = vector_unit(u)
        self.Z = vector_unit(cross(self.Y, self.Z))
        # center point of near and far plane
        self.nc = p - self.Z * self.nearD
        self.fc = p - self.Z * self.farD
        # let's calculate the corners
        self.ntl = self.nc + self.Y * self.nh - self.X * self.nw
        self.ntr = self.nc + self.Y * self.nh + self.X * self.nw
        self.nbl = self.nc - self.Y * self.nh - self.X * self.nw
        self.nbr = self.nc - self.Y * self.nh + self.X * self.nw
        self.ftl = self.fc + self.Y * self.fh - self.X * self.fw
        self.ftr = self.fc + self.Y * self.fh + self.X * self.fw
        self.fbl = self.fc - self.Y * self.fh - self.X * self.fw
        self.fbr = self.fc - self.Y * self.fh + self.X * self.fw
        self.planes['top'] = Plane(self.ntr, self.ntl, self.ftl)
        self.planes['bottom'] = Plane(self.nbl, self.nbr, self.fbr)
        self.planes['left'] = Plane(self.ntl, self.nbl, self.fbl)
        self.planes['right'] = Plane(self.nbr, self.ntr, self.fbr)
        self.planes['near'] = Plane(self.ntl, self.ntr, self.nbr)
        self.planes['far'] = Plane(self.ftr, self.ftl, self.fbl)
        
    def pointInFrustum(self, p):
        for k in ['left', 'right', 'top', 'bottom', 'near', 'far']:
            if self.planes[k].getDistance(p) < 0:
                return self.status['outside']
        return self.status['inside']
    
    def sphereInFrustum(self, p, radius):
        for k in ['left', 'right', 'top', 'bottom', 'near', 'far']:
            distance = self.planes[k].getDistance(p)
            if distance < -radius:
                return self.status['outside']
            elif distance < radius:
                return self.status['intersect']
        return self.status['inside']
    
    def boxInFrustum(self, b):
        intersect = False
        for k in ['left', 'right', 'top', 'bottom', 'near', 'far']:
            if self.planes[k].getDistance(b.getVertexP(self.planes[k].normal)) < 0:
                return self.status['outside']
            elif self.planes[k].getDistance(b.getVertexN(self.planes[k].normal)) < 0:
                intersect = True
        if intersect:
            return self.status['intersect']
        return self.status['inside']
    
