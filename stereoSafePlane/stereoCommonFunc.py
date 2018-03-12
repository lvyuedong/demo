__author__ = 'lvyuedong'

import os
import traceback
try:
    import pymel.core as pm
    import maya.mel as mel
except:
    pass
import math
import xml.etree.ElementTree as ET

import stereoVars as sv
reload(sv)
import commonVar as cvar
reload(cvar)

try:
    import stereo.commonFunc as cf
    reload(cf)
except:
    pass

animCurveType = sv.animCurveType
safePlaneNodeType = sv.safePlaneNodeType
convergePlaneNodeType = sv.convergePlaneNodeType
safePlaneAttrMap = sv.safePlaneAttrMap1

def getMayaVersions(numeric=False):
    from pymel import versions
    if not numeric:
        return str(versions.current())[:4]+'-x64'
    else:
        return versions.current()

def loadStereoPlugins():
    # load stereo plugins
    import maya.mel as mel
    maya_version = getMayaVersions()
    env = mel.eval('getenv MAYA_PLUG_IN_PATH')
    env += ':/mnt/utility/toolset/applications/maya/'+maya_version+'/plugins'
    mel.eval('putenv "MAYA_PLUG_IN_PATH" "'+env+'"')
    try:
        pm.loadPlugin('stereoSafePlane', quiet=True)
    except:
        print 'Failed to load stereoSafePlane plugin'

def loadSpReticlePlugins():
    # load plugins
    import maya.mel as mel
    maya_version = getMayaVersions()
    env = mel.eval('getenv MAYA_PLUG_IN_PATH')
    env += ':/mnt/utility/toolset/applications/maya/'+maya_version+'/plugins'
    mel.eval('putenv "MAYA_PLUG_IN_PATH" "'+env+'"')
    try:
        pm.loadPlugin('spReticleLoc', quiet=True)
    except:
        print 'Failed to load spReticleLoc plugin'

def getFileLocation():
    return os.path.dirname(__file__)

def compareFloatList(a, b, tolerate=0.001):
    if len(a) != len(b):
        return False

    for i in range(len(a)):
        if math.fabs(a[i]-b[i]) > tolerate:
            return False
    return True

def getStereoSafePlaneFromSelection(target=[safePlaneNodeType,convergePlaneNodeType]):
    '''
    return a list contains dict: [ {'camera':stereoCamera,'safe':safePlane,'converge':convergePlane}, ... ]
    Note: results are transform nodes
    '''
    sel = pm.ls(sl=True)
    if not sel:
        return []

    planes = []
    for s in sel:
        node_type = pm.nodeType(s.name())
        if node_type=='transform' or node_type=='stereoRigTransform':
            s = s.getShape()
        else:
            continue
        if not s:
            continue

        if node_type=='camera' or node_type in [safePlaneNodeType,convergePlaneNodeType]:
            # convert to stereoRigCamera if any
            try:
                tmp = s.getParent().getParent().getShape()
                if tmp.type()=='stereoRigCamera':
                    s = tmp
                else:
                    continue
            except:
                continue

        if s.type()=='stereoRigCamera':
            d = { 'camera':s.getParent(), 'safe':None, 'converge':None }
            for y in s.getParent().listRelatives(ad=True, pa=True, type=target):
                if y.type() == safePlaneNodeType:
                    d['safe'] = y.getParent()
                elif y.type() == convergePlaneNodeType:
                    d['converge'] = y.getParent()
            planes.append(d)

    return planes

def reconnectCameras():
    stereo_cams = pm.ls(type='stereoRigCamera')
    for cam in stereo_cams:
        try:
            left = cam.getParent().attr('leftCam').listConnections(d=True)[0]
            right = cam.getParent().attr('rightCam').listConnections(d=True)[0]
            cam.attr('nearClipPlane') >> left.attr('nearClipPlane')
            cam.attr('farClipPlane') >> left.attr('farClipPlane')
            cam.attr('nearClipPlane') >> right.attr('nearClipPlane')
            cam.attr('farClipPlane') >> right.attr('farClipPlane')
        except:
            pass

def createAndConnectStereoCameras(sel=[], interactive=True, stereo_type=0, base_percent=0.7):
    cams = createStereoCameras(sel, interactive, stereo_type, base_percent)
    result = {}
    for k,v in cams.iteritems():
        result.update( connectStereoCameras(k, v, base_percent=base_percent) )
    return result

def addFloatingWindowAttr(stereoCamera):
    if not pm.objExists(stereoCamera):
        return
    else:
        stereoCamera = pm.PyNode(stereoCamera)

    attr_dict = {'LL':'LeftEye_Left', 'LR':'LeftEye_Right', 'RL':'RightEye_Left', 'RR':'RightEye_Right', 'LT':'LeftTop_Scale', 'LB':'LeftBottom_Scale', 'RT':'RightTop_Scale', 'RB':'RightBottom_Scale'}
    for k in ['LL', 'LR', 'RL', 'RR', 'LT', 'LB', 'RT', 'RB']:
        v = attr_dict[k]
        if not stereoCamera.hasAttr(v):
            pm.addAttr(stereoCamera, shortName=k, longName=v, defaultValue=0, minValue=0, maxValue=100, keyable=True)

def getFloatingValue(cam, attr_name, cut_in, cut_out):
    result = {}
    curve_list = pm.findKeyframe(cam, curve=True, at=attr_name)
    attr = cam.attr(attr_name)
    if curve_list:
        c = pm.PyNode(curve_list[0])
        if not c.isStatic():
            for i in range(0, c.numKeys()):
                result.update({int(c.getTime(i)):c.getValue(i)})
    if not result:
        result = {cut_in:attr.get()}
    if len(result.values())==1 and result.values()==[0]:
        result = {}
    return result

def getFloatingWindowValues(cam, cut_in, cut_out):
    '''
    data struct:
    {
        'll':{time:value, time:value, ...},
        'lr':{time:value, time:value, ...},
        ...
        'animated':             False,
        'hasfloatWinScaleAttr': False
    }
    '''

    ll, lr, rl, rr, lt, lb, rt, rb = ({}, {}, {}, {}, {}, {}, {}, {})

    ll = getFloatingValue(cam, 'LeftEye_Left', cut_in, cut_out)
    lr = getFloatingValue(cam, 'LeftEye_Right', cut_in, cut_out)
    rl = getFloatingValue(cam, 'RightEye_Left', cut_in, cut_out)
    rr = getFloatingValue(cam, 'RightEye_Right', cut_in, cut_out)

    hasfloatWinScaleAttr = True if cam.hasAttr('LeftTop_Scale') and cam.hasAttr('LeftBottom_Scale') and cam.hasAttr('RightTop_Scale') and cam.hasAttr('RightBottom_Scale') else False
    if hasfloatWinScaleAttr:
        lt = getFloatingValue(cam, 'LeftTop_Scale', cut_in, cut_out)
        lb = getFloatingValue(cam, 'LeftBottom_Scale', cut_in, cut_out)
        rt = getFloatingValue(cam, 'RightTop_Scale', cut_in, cut_out)
        rb = getFloatingValue(cam, 'RightBottom_Scale', cut_in, cut_out)

    is_float_window_animated = False
    for i in [ll, lr, rl, rr, lt, lb, rt, rb]:
        if len(i)>=2:
            keys = sorted(i.keys())
            diff = i[keys[0]]
            for k in keys[1:]:
                if diff != i[k]:
                    is_float_window_animated = True
                    break
        if is_float_window_animated:
            break

    return {'ll':ll, 'lr':lr, 'rl':rl, 'rr':rr, 'lt':lt, 'lb':lb, 'rt':rt, 'rb':rb, \
            'animated':is_float_window_animated, 'hasfloatWinScaleAttr':hasfloatWinScaleAttr}

def listAdd(input_list):
    r = 0
    for i in input_list:
        r = r + i
    return r

def isListAnimated(input_list):
    if len(input_list)<=1:
        return False
    previous = input_list[0]
    for i in range(len(input_list)):
        if input_list[i] != previous:
            return True
    return False

def getFloatingWindowFromXML_deprecated(xml_path):
    '''
        old method returns list of floatingWindow values, instead of dict
        data structure
        {
            'll':[value1, value2],
            'lr':[value1, value2],
            ...
            'animated':             False,
            'hasFloatingWindow':    False,
            'start':                start_frame,
            'end':                  end_frame,
            'pfx_notes':            ''
        }
    '''
    floatingWindow = {'hasFloatingWindow':False, 'll':[], 'lr':[], 'rl':[], 'rr':[], \
                        'lt':[], 'lb':[], 'rt':[], 'rb':[], 'animated':False}

    tree = ET.parse(xml_path)
    root = tree.getroot()

    time_inst = root.find('time')
    start_frame = float( time_inst.find('start').get('value') )
    end_frame = float( time_inst.find('end').get('value') )

    window_inst = root.find('windows')
    isAnim = False if window_inst.get('isAnimation') == 'no' else True
    ll_inst = window_inst.find('left_left')
    lr_inst = window_inst.find('left_right')
    rl_inst = window_inst.find('right_left')
    rr_inst = window_inst.find('right_right')
    ll = [float(str(ll_inst.get('value')).split(' ')[0])] if not isAnim else [float(v) for v in str(ll_inst.get('value')).split(' ')]
    lr = [float(str(lr_inst.get('value')).split(' ')[0])] if not isAnim else [float(v) for v in str(lr_inst.get('value')).split(' ')]
    rl = [float(str(rl_inst.get('value')).split(' ')[0])] if not isAnim else [float(v) for v in str(rl_inst.get('value')).split(' ')]
    rr = [float(str(rr_inst.get('value')).split(' ')[0])] if not isAnim else [float(v) for v in str(rr_inst.get('value')).split(' ')]
    if listAdd(ll) == 0 and listAdd(lr) == 0 and listAdd(rl) == 0 and listAdd(rr) == 0:
        return floatingWindow
    else:
        floatingWindow['hasFloatingWindow'] = True
        pfx_string = ''
        if listAdd(ll) > 0:
            if isListAnimated(ll):
                pfx_string += ', L-'
                floatingWindow['animated'] = True
            else:
                pfx_string += ', L-' + format(int(math.ceil(20.48*ll[0])), '1d')
        elif listAdd(rl) > 0:
            if isListAnimated(rl):
                pfx_string += ', L+'
                floatingWindow['animated'] = True
            else:
                pfx_string += ', L+' + format(int(math.ceil(20.48*rl[0])), '1d')
        if listAdd(rr) > 0:
            if isListAnimated(rr):
                pfx_string += ', R-'
                floatingWindow['animated'] = True
            else:
                pfx_string += ', R-' + format(int(math.ceil(20.48*rr[0])), '1d')
        elif listAdd(lr) > 0:
            if isListAnimated(lr):
                pfx_string += ', R+'
                floatingWindow['animated'] = True
            else:
                pfx_string += ', R+' + format(int(math.ceil(20.48*lr[0])), '1d')

        if pfx_string.startswith(', '):
            pfx_string = pfx_string[2:]

        floatingWindow['ll'].extend(ll)
        floatingWindow['lr'].extend(lr)
        floatingWindow['rl'].extend(rl)
        floatingWindow['rr'].extend(rr)
        floatingWindow.update( {'start':start_frame, 'end':end_frame, 'pfx_notes':pfx_string} )

    return floatingWindow

def getFloatingWindowFromXML(shotcode, proj=cvar.default_proj):
    '''
        data structure
        {
            'll':{time:value, time:value, ...},
            'lr':{time:value, time:value, ...},
            ...
            'animated':             False,
            'hasFloatingWindow':    False,
            'start':                start_frame,
            'end':                  end_frame,
            'pfx_notes':            ''
        }
    '''
    floatingWindow = {'hasFloatingWindow':False, 'll':{}, 'lr':{}, 'rl':{}, 'rr':{}, \
                            'lt':{}, 'lb':{}, 'rt':{}, 'rb':{}, 'animated':False}
    
    path = cf.osPathConvert( '/mnt/proj/projects/'+proj+'/shot/'+shotcode[:3]+'/'+shotcode+'/flo/publish/' )
    if not os.path.isdir(path):
        print 'XML path is not valid: '+path
        return floatingWindow
    versions = sorted([ d for d in os.listdir(path) if d.startswith(shotcode) and '.flo.stereo.' in d ])
    if not versions:
        print 'Failed to find flo.stereo publish version in path: '+path
        return floatingWindow
    if proj=='god':
        path = path + versions[-1] + '/stereo_data/' + shotcode + '_stereo_data.xml'
    else:
        path = path + versions[-1] + '/camera/stereo_data/'
        if os.path.isfile(path+shotcode+'_stereo_data_Near.xml'):
            path = path+shotcode+'_stereo_data_Near.xml'
        elif os.path.isfile(path+shotcode+'_stereo_data.xml'):
            path = path+shotcode+'_stereo_data.xml'
        else:
            print 'Failed to find xml'
            return floatingWindow

    tree = ET.parse(path)
    root = tree.getroot()

    time_inst = root.find('time')
    start_frame = float( time_inst.find('start').get('value') )
    end_frame = float( time_inst.find('end').get('value') )

    window_inst = root.find('windows')
    isAnim_attr = window_inst.get('isAnimation')
    if isAnim_attr:     # old attribute
        return getFloatingWindowFromXML_deprecated(path)

    attributes = [['left_left', 'll'], ['left_right','lr'], ['right_left','rl'], ['right_right','rr']]
    for a in attributes:
        fw_inst = window_inst.find(a[0])
        try:
            v = str(fw_inst.get('value')).split(' ')
        except:
            continue
        if not v or (len(v)==1 and not v[0].replace('.','').isdigit()):
            continue
        if len(v)==1:
            if float(v[0])<=0.001:
                continue
            else:
                floatingWindow[a[1]].update({int(start_frame):float(v[0])})
        else:
            floatingWindow['animated'] = True
            for i in range(0, len(v), 2):
                floatingWindow[a[1]].update({int(v[i]):float(v[i+1])})

    if not floatingWindow['ll'] and not floatingWindow['lr'] and not floatingWindow['rl'] and not floatingWindow['rr']:
        return floatingWindow
    else:
        floatingWindow['hasFloatingWindow'] = True
        pfx_string = ''
        attributes = [[', L-', 'll'], [', R+','lr'], [', L+','rl'], [', R-','rr']]
        for a in attributes:
            if floatingWindow[a[1]]:
                if len(floatingWindow[a[1]])==1:
                    pfx_string += a[0] + format( int(math.ceil(20.48*floatingWindow[a[1]].values()[0])), '1d' )
                else:
                    pfx_string += a[0] + '{'
                    for k in sorted(floatingWindow[a[1]].keys()):
                        pfx_string += str(k)+':'+ format(int(math.ceil(20.48*floatingWindow[a[1]][k])), '1d')+', '
                    if pfx_string.strip().endswith(','):
                        pfx_string = pfx_string.strip()[:-1]
                    pfx_string += '}'

        if pfx_string.startswith(', '):
            pfx_string = pfx_string[2:]

        floatingWindow.update({'start':start_frame, 'end':end_frame, 'pfx_notes':pfx_string})

    return floatingWindow

def addRoundnessRatio(safePlane, convergePlane):
    if not pm.objExists(safePlane):
        return
    else:
        safePlane = pm.PyNode(safePlane)

    if not safePlane.hasAttr('roundnessRatio'):
        try:
            pm.addAttr(safePlane, shortName='rr', longName='roundnessRatio', defaultValue=0, keyable=True)
            safePlane.outRoundness >> safePlane.roundnessRatio
            safePlane.attr('roundnessRatio').lock()
        except:
            print traceback.format_exc()

    if not pm.objExists(convergePlane):
        return
    else:
        convergePlane = pm.PyNode(convergePlane)

    if not convergePlane.hasAttr('roundnessRatio'):
        try:
            pm.addAttr(convergePlane, shortName='rr', longName='roundnessRatio', defaultValue=0, keyable=True)
            safePlane.outRoundness >> convergePlane.roundnessRatio
            convergePlane.attr('roundnessRatio').lock()
        except:
            print traceback.format_exc()


def createStereoCameras(sel=[], interactive=True, stereo_type=0, base_percent=0.7):
    '''
    interactive mode will prompted a window to choose what type of stereo camera should be created.
    the parameter stereo_type is in effect only if interactive is False
    stereo_type 0: middle stereo camera
    stereo_type 1: near stereo camera
    stereo_type 2: far stereo camera
    '''
    try:
        pm.system.loadPlugin('stereoCamera', quiet=True)
    except:
        pass

    if not sel:
        sel = pm.ls(sl=True, type='transform')
    if not sel:
        pm.warning('Please select one camera at least.')
        return

    if not isinstance(sel, type([])):
        sel = [sel]

    stereo_cams = {}
    for s in sel:
        try:
            import maya.app.stereo.stereoCameraRig
        except:
            print traceback.format_exc()
        try:
            s = pm.PyNode(s)
            if pm.nodeType( s.getShape() ) != 'camera':
                pm.warning(s.name()+' is not a camera, please select camera transform node, ignored.')
                continue
        except:
            continue

        cam_name = s.longName()
        if interactive:
            # interactive mode will overwrite stereo_type parameter
            if pm.objExists(cam_name+'_stereoCamera'):
                if pm.objExists(cam_name+'_stereoCamera_Near') and pm.objExists(cam_name+'_stereoCamera_Far'):
                    pm.confirmDialog(title='Warning', message='There are triple stereo cameras exist in the scene, ignored the process.', button='Alright', defaultButton='Alright', cancelButton='Alright', dismissString='Alright')
                    continue
                else:
                    if pm.objExists(cam_name+'_stereoCamera_Near'):
                        anw = pm.confirmDialog(title='Warning', message=cam_name+': Main and Near stereo camera already exist, proceed to create Far stereo camera. Proceed any way?', button=['No', 'Yes'], defaultButton='Yes', cancelButton='No', dismissString='No')
                        if anw=='Yes':
                            stereo_type = 2
                        else:
                            continue
                    elif pm.objExists(cam_name+'_stereoCamera_Far'):
                        anw = pm.confirmDialog(title='Warning', message=cam_name+': Main and Far stereo camera already exist, proceed to create Near stereo camera. Proceed any way?', button=['No', 'Yes'], defaultButton='Yes', cancelButton='No', dismissString='No')
                        if anw=='Yes':
                            stereo_type = 1
                        else:
                            continue
                    else:
                        anw = pm.confirmDialog(title='Warning', message=cam_name+': Main stereo camera already exist, proceed to create Near or Far stereo camera:',  button=['Cancel', 'Near', 'Far'], defaultButton='Cancel', cancelButton='Cancel', dismissString='Cancel')
                        if anw=='Near':
                            stereo_type = 1
                        elif anw=='Far':
                            stereo_type = 2
                        else:
                            continue
            else:
                stereo_type = 0

        # create
        stereo_cam_name = {0:cam_name+'_stereoCamera', \
                            1:cam_name+'_stereoCamera_Near', \
                            2:cam_name+'_stereoCamera_Far'}.get(stereo_type)
        if pm.objExists(stereo_cam_name):
            pm.warning(stereo_cam_name+' already exists, ignored!')
            continue               
        parent = s.getParent()
        tmp = maya.app.stereo.stereoCameraRig.createStereoCameraRig()
        tmp[0] = pm.PyNode(tmp[0])
        # put the stereo camera under the same parent node
        if parent:
            pm.parent( tmp[0], parent )
        pm.rename( tmp[0], stereo_cam_name )
        addFloatingWindowAttr( tmp[0] )
        stereo_cams.update( {s:tmp[0]} )

    return stereo_cams

def createStereoSafePlanes(stereoCamera, base_percent=0.7, far1=0.5, far2=1.0, near1=-1.0, near2=-2.0):
    if not pm.objExists(stereoCamera):
        print 'Failed to find stereo camera: '+str(stereoCamera)
        return []
    else:
        stereoCamera = pm.PyNode(stereoCamera)

    try:
        pm.system.loadPlugin(safePlaneNodeType, quiet=True)
    except:
        print traceback.format_exc()
        return

    safePlane = []
    convergePlane = []
    safePlane = [s.getParent() for s in pm.listRelatives(stereoCamera, ad=True, pa=True, type=safePlaneNodeType)]
    convergePlane = [c.getParent() for c in pm.listRelatives(stereoCamera, ad=True, pa=True, type=convergePlaneNodeType)]
    if safePlane and convergePlane:
        return {'safePlane':safePlane[0], 'convergePlane':convergePlane[0]}

    try:
        if safePlane:
            pm.delete(safePlane)
        if convergePlane:
            pm.delete(convergePlane)
    except:
        print traceback.format_exc()

    # safe plane
    safePlaneShape = pm.createNode(safePlaneNodeType)
    safePlane = safePlaneShape.getParent()
    stereoCameraShape = stereoCamera.getShape()

    pm.transformLimits(safePlane, tz=(-999999,-0.001), etz=(False, True))
    safePlane.attr('translateZ').set(-20)
    safePlane.attr('translateZ') >> safePlaneShape.attr('translateZ')
    stereoCameraShape.attr('cameraAperture') >> safePlaneShape.attr('filmAperture')
    stereoCameraShape.attr('focalLength') >> safePlaneShape.attr('focalLength')
    stereoCameraShape.attr('zeroParallax') >> safePlaneShape.attr('zeroParallax')
    safePlaneShape.attr('outInterocular') >> stereoCameraShape.attr('interaxialSeparation')

    for a in ['translateX', 'translateY', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleZ']:
        safePlane.attr(a).lock()
        safePlane.attr(a).setKeyable(False)

    for a in ['localPositionX', 'localPositionY', 'localPositionZ', 'localScaleX', 'localScaleY', 'localScaleZ']:
        safePlane.attr(a).setKeyable(False)
        safePlane.attr(a).showInChannelBox(False)

    safePlane.attr('translateZ').set(-20)
    safePlaneShape.attr(safePlaneAttrMap['base']).set(base_percent)
    safePlaneShape.attr(safePlaneAttrMap['farthest']).set(far2)
    safePlaneShape.attr(safePlaneAttrMap['far']).set(far1)
    safePlaneShape.attr(safePlaneAttrMap['near']).set(near1)
    safePlaneShape.attr(safePlaneAttrMap['nearest']).set(near2)
    if safePlaneShape.hasAttr('versionSwitch'):
        safePlaneShape.attr('versionSwitch').set(2)

    pm.parent(safePlane, stereoCamera, relative=True)

    # converge plane
    convergePlaneShape = pm.createNode(convergePlaneNodeType)
    convergePlane = convergePlaneShape.getParent()

    pm.transformLimits(convergePlane, tz=(-999999,-0.001), etz=(False, True))
    convergePlane.attr('translateZ').set(-10)
    convergePlane.attr('translateZ') >> convergePlaneShape.attr('translateZ')
    stereoCameraShape.attr('cameraAperture') >> convergePlaneShape.attr('filmAperture')
    stereoCameraShape.attr('focalLength') >> convergePlaneShape.attr('focalLength')
    convergePlaneShape.attr('zeroParallax') >> stereoCameraShape.attr('zeroParallax')

    for a in ['translateX', 'translateY', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleZ']:
        convergePlane.attr(a).lock()
        convergePlane.attr(a).setKeyable(False)

    for a in ['localPositionX', 'localPositionY', 'localPositionZ', 'localScaleX', 'localScaleY', 'localScaleZ']:
        convergePlane.attr(a).setKeyable(False)
        convergePlane.attr(a).showInChannelBox(False)

    for a in ['focalLength', 'horizontalFilmAperture', 'verticalFilmAperture', 'translateZ']:
        convergePlaneShape.attr(a).setKeyable(False)
        convergePlaneShape.attr(a).showInChannelBox(False)

    pm.parent(convergePlane, stereoCamera, relative=True)

    return {'safePlane':safePlane, 'convergePlane':convergePlane}


def connectStereoCameras(camera, stereo_cams, base_percent=0.7, interactive=False, threshod=0.001):
    if not pm.objExists(camera):
        print 'The given center camera does not exists: '+str(camera)
        return
    else:
        camera = pm.PyNode(camera)

    if not isinstance(stereo_cams, type([])):
        stereo_cams = [stereo_cams]

    stereoCameras = {}

    for s in stereo_cams:
        s = pm.PyNode(s)

        # constrain stereo camera to main camera
        pm.pointConstraint(camera, s, offset=(0,0,0), weight=1)
        pm.orientConstraint(camera, s, offset=(0,0,0), weight=1)

        # local pivot alignment
        rot_local = pm.xform(camera, query=True, os=True, rp=True)
        scale_local = pm.xform(camera, query=True, os=True, sp=True)
        local_pivot_bool = False
        for v in rot_local:
            if math.fabs(v) >= threshod:
                local_pivot_bool = True
                pm.xform(s, os=True, rp=tuple(rot_local))
                break
        for v in scale_local:
            if math.fabs(v) >= threshod:
                local_pivot_bool = True
                pm.xform(s, os=True, sp=tuple(scale_local))
                break

        if interactive and local_pivot_bool:
            pm.confirmDialog(title='Warning', message='Found non-zero value on local pivot attribute of camera!', button='OK', defaultButton='OK', cancelButton='OK', dismissString='OK')

        # connect attributes of cameras
        for a in ['focalLength', 'horizontalFilmAperture', 'verticalFilmAperture']:
            camera.attr(a) >> s.attr(a)

        try:
            filmFit = camera.attr('filmFit').get()
            if filmFit==0:
                filmFit = 1
                camera.attr('filmFit').set(filmFit)
            s.attr('filmFit').set(filmFit)
            s.getShape().attr('stereo').set(2)
            s.getShape().attr('displayResolution').set(0)
        except:
            print traceback.format_exc()

        # create safe plane
        planes = createStereoSafePlanes(s)
        # add roundness ratio
        addRoundnessRatio(planes['safePlane'], planes['convergePlane'])

        stereoCameras.update( {s:{'camera':camera, 'safePlane':planes['safePlane'], 'convergePlane':planes['convergePlane'], 'node':s}} )

    return stereoCameras

def copyStereoAttrs(src, des):
    '''
    src and des must be the python node of stereoRigTransform
    '''
    if pm.nodeType(src)!='stereoRigTransform':
        if pm.nodeType(src)=='stereoRigCamera':
            src = src.getParent()
        else:
            pm.warning( 'Please input the stereoRigTransform to copy the attributes' )
            return False
    if pm.nodeType(des)!='stereoRigTransform':
        if pm.nodeType(des)=='stereoRigCamera':
            des = des.getParent()
        else:
            pm.warning( 'Please input the stereoRigTransform to copy the attributes' )
            return False
    # get safe plane
    src_safePlane = [c.getParent() for c in src.listRelatives(ad=True, pa=True, type=safePlaneNodeType)]
    des_safePlane = [c.getParent() for c in des.listRelatives(ad=True, pa=True, type=safePlaneNodeType)]
    src_convergePlane = [c.getParent() for c in src.listRelatives(ad=True, pa=True, type=convergePlaneNodeType)]
    des_convergePlane = [c.getParent() for c in des.listRelatives(ad=True, pa=True, type=convergePlaneNodeType)]
    if not src_safePlane or not des_safePlane or not src_convergePlane or not des_convergePlane:
        pm.warning( 'Failed to find safe or converge planes for the specified stereo cameras' )
        return False

    # copy attrs
    copyAttrs( src, des, ['nearClipPlane', 'farClipPlane', 'LeftEye_Left', 'LeftEye_Right', 'RightEye_Left', 'RightEye_Right', 'LeftTop_Scale', 'LeftBottom_Scale', 'RightTop_Scale', 'RightBottom_Scale'] )
    attr_list = safePlaneAttrMap.values()
    copyAttrs( src_safePlane[0], des_safePlane[0], attr_list )
    copyAttrs( src_convergePlane[0], des_convergePlane[0], ['translateZ'] )

    return True

def copyAttrs(src, des, attr=[]):
    if not attr:
        attr = ['nearClipPlane', 'farClipPlane', 'LeftEye_Left', 'LeftEye_Right', 'RightEye_Left', 'RightEye_Right', 'LeftTop_Scale', 'LeftBottom_Scale', 'RightTop_Scale', 'RightBottom_Scale']
        attr.extend( safePlaneAttrMap.values() )
    for a in attr:
        if not des.hasAttr(a):
            continue
        # delete keys for des firstly
        curves_des = list(set(des.attr(a).listConnections(s=True, p=True, type=animCurveType)))
        if curves_des:
            for c in curves_des:
                #c // des.attr(a)
                #if not c.listConnections():
                pm.delete( c )
        # then copy value from src to des
        curves = list(set(src.attr(a).listConnections(s=True, type=animCurveType)))
        if curves:
            dup = pm.duplicate( curves[0], n=des.name()+'_'+a )
            if dup and isinstance(dup, type([])):
                dup = dup[0]
            dup.output >> des.attr(a)
        else:
            des.attr(a).set( src.attr(a).get() )


def showSafePlaneExclusively():
    if not pm.objExists('|cameras'):
        pm.warning('Failed to find |cameras group, ignored the process!')
        return

    sel = pm.ls(sl=True)
    stereo_cams = []
    for s in sel:
        if pm.nodeType(s)=='stereoRigTransform':
            stereo_cams.append(s)
        elif pm.nodeType(s)=='stereoRigCamera':
            stereo_cams.append(s.getParent())
        elif pm.nodeType(s)=='transform':
            if pm.objExists(s.name()+'_stereoCamera') and pm.nodeType(s.name()+'_stereoCamera')=='stereoRigTransform':
                stereo_cams.append(pm.PyNode(s.name()+'_stereoCamera'))
                continue
            p = s.getParent()
            if pm.nodeType(p)=='stereoRigTransform':
                stereo_cams.append(p)
            
    stereo_planes = pm.listRelatives('|cameras', ad=True, type=[safePlaneNodeType,convergePlaneNodeType])
    for s in stereo_planes:
        hidden = True
        for c in stereo_cams:
            if s.isChildOf(c):
                hidden = False
                break
        try:
            if hidden:
                s.getParent().attr('v').set(0)
            else:
                s.getParent().attr('v').set(1)
        except:
            print traceback.format_exc()

def showHideAllSafePlane(show=True):
    if not pm.objExists('|cameras'):
        pm.warning('Failed to find |cameras group, ignored the process!')
        return

    stereo_planes = pm.listRelatives('|cameras', ad=True, type=[safePlaneNodeType,convergePlaneNodeType])
    for s in stereo_planes:
        try:
            s.getParent().attr('v').set(show)
        except:
            print traceback.format_exc()

def setObjectVisibilityOn(obj):
    if not obj:
        return
    if not isinstance(obj, type([])):
        obj = [obj]
    for o in obj:
        if not pm.Attribute(o.name()+'.visibility').isConnected() and not pm.Attribute(o.name()+'.visibility').isLocked():
            pm.Attribute(o.name()+'.visibility').set(1)
        if not pm.Attribute(o.name()+'.drawOverride').isConnected() and not pm.Attribute(o.name()+'.drawOverride').isLocked():
            pm.Attribute(o.name()+'.overrideVisibility').set(1)
            pm.Attribute(o.name()+'.overrideEnabled').set(0)

def setObjectVisibilityOff(obj):
    if not obj:
        return
    if not isinstance(obj, type([])):
        obj = [obj]
    for o in obj:
        if not pm.Attribute(o.name()+'.visibility').isConnected() and not pm.Attribute(o.name()+'.visibility').isLocked():
            pm.Attribute(o.name()+'.visibility').set(0)
        elif not pm.Attribute(o.name()+'.drawOverride').isConnected() and not pm.Attribute(o.name()+'.drawOverride').isLocked():
            pm.Attribute(o.name()+'.overrideVisibility').set(0)
            pm.Attribute(o.name()+'.overrideEnabled').set(1)

def findStereoLayers():
    layers = {'main':[], 'near':[], 'far':[]}
    safePlanes = pm.ls(type=safePlaneNodeType)
    for s in safePlanes:
        stereo_cam = s.outInterocular.outputs()
        if stereo_cam and stereo_cam[0].type() == 'stereoRigTransform':
            if stereo_cam[0].name().endswith('_stereoCamera_Near'):
                layers['near'].append(s)
            elif stereo_cam[0].name().endswith('_stereoCamera_Far'):
                layers['far'].append(s)
            elif stereo_cam[0].name().endswith('_stereoCamera'):
                layers['main'].append(s)
    return layers

def getObjectsFromLayer(layer):
    objects = []
    if not pm.objExists(layer):
        return
    layer = pm.PyNode(layer)
    if not pm.hasAttr(layer, 'stereo_layer'):
        return
    obj_string = layer.stereo_layer.get()
    if obj_string:
        objects = [pm.PyNode(o.strip()) for o in obj_string.split(';') if pm.objExists(o.strip())]
    return objects
                
def switchLayer(layer=''):
    '''
    This method can be used for showing or hiding objects in the stereo layers
    layer: near, main, far
    '''

    layers = findStereoLayers()

    if not layers.has_key(layer):
        return

    for l in layers[layer]:
        if not pm.hasAttr(l, 'stereo_layer'):
            continue
        if not pm.hasAttr(l, 'stereo_layer_visibility'):
            pm.addAttr(l, ln='stereo_layer_visibility', at='bool')
            l.stereo_layer_visibility.set(1)

        objects = getObjectsFromLayer(l)

        if l.stereo_layer_visibility.get():
            setObjectVisibilityOff(objects)
            l.stereo_layer_visibility.set(0)
        else:
            setObjectVisibilityOn(objects)
            l.stereo_layer_visibility.set(1)

def selectLayer(layer=''):
    '''
    This method can be used for selecting objects in the stereo layers
    layer: near, main, far
    '''
    layers = findStereoLayers()
    if not layers.has_key(layer):
        return

    sel = []
    for l in layers[layer]:
        if not pm.hasAttr(l, 'stereo_layer'):
            continue
        objects = getObjectsFromLayer(l)
        sel.extend(objects)
    sel = list(set(sel))
    pm.select(sel)

def showLayer2(layer=''):
    '''
    This method should be only used for playblasting. To use for UI version, refer to switchLayer method
    layer: near, main, far
    '''
    safePlanes = pm.ls(type=safePlaneNodeType)

    if not layer:
        # show all objects
        for s in safePlanes:
            if pm.hasAttr(s, 'stereo_layer'):
                objects = getObjectsFromLayer(s)
                setObjectVisibilityOn(objects)
            if pm.hasAttr(s, 'stereo_layer_visibility'):
                s.stereo_layer_visibility.set(1)
        return

    layers = findStereoLayers()
    if not layers.has_key(layer):
        return

    objects_current_layer = getObjectsFromLayer(layers[layer][0])

    for s in safePlanes:
        if not pm.hasAttr(s, 'stereo_layer'):
            continue

        objects = getObjectsFromLayer(s)
        if s in layers[layer]:
            # show
            setObjectVisibilityOn(objects)
            if pm.hasAttr(s, 'stereo_layer_visibility'):
                s.stereo_layer_visibility.set(1)
        else:
            # hide
            # subtract the objects in the current layer from the other layer
            objects = list(set(objects).difference(objects_current_layer))
            setObjectVisibilityOff(objects)
            if pm.hasAttr(s, 'stereo_layer_visibility'):
                s.stereo_layer_visibility.set(0)


def addObjectToLayer2(layer='main', mode=0):
    '''
    mode 0: add object
    mode 1: delete object
    mode 2: delete all objects in all layers
    '''

    safePlanes = pm.ls(type=safePlaneNodeType)

    if mode==2:
        for safe in safePlanes:
            if not pm.hasAttr(safe, 'stereo_layer') or not pm.hasAttr(safe, 'stereo_layer_visibility'):
                continue
            objects = getObjectsFromLayer(safe)
            setObjectVisibilityOn(objects)
            safe.stereo_layer.set('')
            safe.stereo_layer_visibility.set(1)
        return

    layers = findStereoLayers()

    if not layers[layer]:
        pm.warning('There is no '+layer+' stereo camera in the scene, ignored.')
        return

    l = layers[layer][0]
    if not pm.hasAttr(l, 'stereo_layer'):
        pm.addAttr(l, ln='stereo_layer', dt='string')
    if not pm.hasAttr(l, 'stereo_layer_visibility'):
        pm.addAttr(l, ln='stereo_layer_visibility', at='bool')
    # get original
    objects = getObjectsFromLayer(l)

    sel = pm.ls(sl=True)
    failed = []

    for s in sel:
        if mode==0:     # add
            if s in objects:
                continue
            # use pm.Attribute instead of obj.attr in case of assemblyReference
            if not pm.Attribute(s.name()+'.visibility').isConnected() and not pm.Attribute(s.name()+'.visibility').isLocked():
                objects.append(s)
            elif not pm.Attribute(s.name()+'.drawOverride').isConnected() and not pm.Attribute(s.name()+'.drawOverride').isLocked():
                objects.append(s)
            else:
                failed.append(s)
        elif mode==1:   # remove
            if s in objects:
                objects.remove(s)

    objects = list(set(objects))
    for l in layers[layer]:
        if not pm.hasAttr(l, 'stereo_layer'):
            pm.addAttr(l, ln='stereo_layer', dt='string')
        if not pm.hasAttr(l, 'stereo_layer_visibility'):
            pm.addAttr(l, ln='stereo_layer_visibility', at='bool')
        l.stereo_layer_visibility.set(1)
        l.stereo_layer.set(';'.join([o.name() for o in objects]))

    if failed:
        pm.warning('Failed to add the following objects to stereo layer, whose attributes of visibility and drawOverride are used in another case:\n'+' '.join(failed))
        pm.select(failed)


# old method
def showLayer(layer='', show=True):
    layers_list = ['main', 'near', 'far']

    if not layer:
        # we show all objects in the stereo layer if layer is empty
        for l in layers_list:
            if pm.objExists('stereo_'+l):
                tmp = pm.PyNode('stereo_'+l)
                tmp.attr('v').set(1)
                if pm.hasAttr(tmp, 'stereo_hidden'):
                    for o in tmp.attr('stereo_hidden').get().split(';'):
                        try:
                            if pm.objExists(o):
                                pm.setAttr(o+'.overrideVisibility', 1)
                                pm.setAttr(o+'.overrideEnabled', 0)
                        except:
                            print traceback.format_exc()
        return

    for l in layers_list:
        if l==layer:
            if pm.objExists('stereo_'+l):
                tmp = pm.PyNode('stereo_'+l)
                tmp.attr('v').set(int(show))
                if pm.hasAttr(tmp, 'stereo_hidden'):
                    for o in tmp.attr('stereo_hidden').get().split(';'):
                        try:
                            if pm.objExists(o):
                                pm.setAttr(o+'.overrideVisibility', int(show))
                                pm.setAttr(o+'.overrideEnabled', int(not show))
                        except:
                            print traceback.format_exc()
        else:
            if pm.objExists('stereo_'+l):
                tmp = pm.PyNode('stereo_'+l)
                tmp.attr('v').set(int(not show))
                if pm.hasAttr(tmp, 'stereo_hidden'):
                    for o in tmp.attr('stereo_hidden').get().split(';'):
                        try:
                            if pm.objExists(o):
                                pm.setAttr(o+'.overrideEnabled', int(show))
                                pm.setAttr(o+'.overrideVisibility', int(not show))
                        except:
                            print traceback.format_exc()

def addObjectToLayer(layer='main', mode=0):
    '''
    assembly references can not be added to display layer, so we add text description to layer attribute
    mode 0: add object
    mode 1: delete object
    mode 2: delete all objects in all layers
    '''
    layer = 'stereo_' + layer
    
    if mode==2:
        for l in ['stereo_main', 'stereo_near', 'stereo_far']:
            if not pm.objExists(l):
                continue
            tmp = pm.PyNode(l)
            obj_display = pm.listConnections(tmp.attr('drawInfo'), d=True)
            for o in obj_display:
                try:
                    tmp.drawInfo // o.drawOverride
                    o.attr('overrideVisibility').set(1)
                    o.attr('overrideEnabled').set(0)
                except:
                    pass
            if not pm.hasAttr(tmp, 'stereo_hidden'):
                continue
            obj_string = tmp.attr('stereo_hidden').get()
            if obj_string:
                obj_string = [o.strip() for o in obj_string.split(';')]
                for o in obj_string:
                    try:
                        if not pm.objExists(o):
                            continue
                        o.attr('overrideVisibility').set(1)
                        o.attr('overrideEnabled').set(0)
                    except:
                        pass
                tmp.attr('stereo_hidden').set('')

    if not pm.objExists(str(layer)):
        layer = pm.createDisplayLayer(name=str(layer), e=True)
    else:
        layer = pm.PyNode(str(layer))

    if not pm.hasAttr(layer, 'stereo_hidden'):
        pm.addAttr(layer, ln='stereo_hidden', dt='string')

    hidden_obj = []
    hidden_string = []

    # get original
    hidden_obj.extend( pm.listConnections(layer.attr('drawInfo'), d=True) )

    hidden_string_orig = layer.attr('stereo_hidden').get()
    if hidden_string_orig:
        hidden_string.extend( [o.strip() for o in hidden_string_orig.split(';')] )

    sel = pm.ls(sl=True)

    for s in sel:
        # does it ends with :master or _AR
        if not s.name().endswith(':master') and not s.name().endswith('_AR'):
            # is it sit in lay
            if not s.isChildOf('|assets|lay'):
                print s.name()+' was not added to hidden layer, because its name does not ends with :master'
                return

        if mode==0:
            # try add to display layer first
            add_to_display = False
            if s not in hidden_obj:
                try:
                    layer.drawInfo >> s.drawOverride
                    add_to_display = True
                except:
                    add_to_display = False
            if not add_to_display and s.name() not in hidden_string:
                hidden_string.append(s.name())
        elif mode==1:
            if s in hidden_obj:
                try:
                    layer.drawInfo // s.drawOverride
                    s.attr('overrideVisibility').set(1)
                    s.attr('overrideEnabled').set(0)
                except:
                    pass
            if s.name() in hidden_string:
                hidden_string.remove(s.name())

    layer.attr('stereo_hidden').set( ';'.join(hidden_string) )

def findValidNamespace(ns):
    if pm.namespace(ex=ns):
        if ns[-1].isdigit():
            ns = ns[:-1] + format(int(ns[-1])+1, '01d')
        else:
            ns = ns + '1'
        return findValidNamespace(ns)
    else:
        return ns

def cleanNamespace(ns='previous'):
    try:
        if pm.objExists(ns+':cameras'):
            pm.delete(ns+':cameras')

        if pm.namespace(ex=ns):
            pm.namespace(rm=ns)
    except:
        print traceback.format_exc()

def getStereoSettings(camera_path):
    camera_path = camera_path.replace('\\', '/')
    tmp = camera_path.split('/')
    shot = tmp[tmp.index('shot')+2]
    
    if not os.path.isdir( camera_path ):
        print 'Failed to find the camera folder: '+path
        return False

    camera = os.path.join(camera_path, shot+'_cam_raw.ma')
    if not os.path.isfile(camera):
        camera = os.path.join(camera_path, shot+'_cam_anim.ma')
        if not os.path.isfile(camera):
            print 'Failed to find the camera file: '+camera
            return False

    # clean namespace
    cleanNamespace()

    # create namespace
    pm.namespace(set=':')
    ns = findValidNamespace('previous')

    pm.importFile(camera, ns=ns)
    
    pre_stereo_cams = pm.listRelatives(ns+':cameras', ad=True, type='stereoRigTransform')
    stereo_cams = pm.listRelatives('|cameras', ad=True, type='stereoRigTransform')

    if len(pre_stereo_cams) != len(stereo_cams):
        print 'The latest stereo camera is different with current camera, aborted!'
        print 'The previous has '+str(len(pre_stereo_cams))+' stereo cameras, the current has '+str(len(stereo_cams))+' stereo cameras.'
        cleanNamespace(ns)
        return False

    pre_cams = {}
    cams = {}
    for c in pre_stereo_cams:
        if c.name().endswith('_Near'):
            pre_cams.update({'near':c})
        elif c.name().endswith('_Far'):
            pre_cams.update({'far':c})
        else:
            pre_cams.update({'main':c})
    for c in stereo_cams:
        if c.name().endswith('_Near'):
            cams.update({'near':c})
        elif c.name().endswith('_Far'):
            cams.update({'far':c})
        else:
            cams.update({'main':c})

    if sorted(pre_cams.keys()) != sorted(cams.keys()):
        print 'The latest stereo camera is different with current camera, aborted!'
        print 'The previous has '+','.join(pre_cams.keys())+' stereo cameras, while the current has '+','.join(cams.keys())+' stereo cameras.'
        cleanNamespace(ns)
        return False

    for k in pre_cams.keys():
        copyStereoAttrs(pre_cams[k], cams[k])

    # clear the scene
    cleanNamespace(ns)

    print 'Import and copy the latest stereo camera successfully!'
    return True
