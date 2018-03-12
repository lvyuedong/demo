# -*- coding: utf-8 -*-

import os
import sys
import stat
import shutil
import subprocess
import traceback
import math
import time
import glob
import bisect

try:
    import pymel.core as pm

    import gene.safeArea.SafeAreaClass as sa
    reload(sa)

    import commonFunc as cf
    reload(cf)

    import stereoCommonFunc as scf
    reload(scf)

    import PIL_playblastComp as pilp
    reload(pilp)
except:
    pass

import stereoVars as sv
reload(sv)

safePlaneNodeType = sv.safePlaneNodeType
convergePlaneNodeType = sv.convergePlaneNodeType

stereo_pb_window = {}
stereo_pb_continue = False

global_disp_elem = {'displayLights':False, 'allObjects':True, 'nurbsSurfaces':True, 'polymeshes':True, 'fluids':True,\
             'hud':True, 'sel':True, 'strokes':True, 'planes':False, 'lights':False, 'cameras':False, 'joints':False, \
             'ikHandles':False, 'deformers':False, 'dynamics':True, 'hairSystems':False, 'follicles':False, \
             'nCloths':False, 'nParticles':True, 'nRigids':False, 'dynamicConstraints':False, 'locators':False, \
             'pivots':False, 'dimensions':False, 'handles':False, 'textures':False, 'motionTrails':False, \
             'manipulators':False, 'clipGhosts':False, 'nurbsCurves':False, 'cv':False, 'hulls':False, 'grid':False, \
             'imagePlane':False, 'shadows':False}


def getDisplayElements(d):
    global global_disp_elem
    result = global_disp_elem
    keys = result.keys()
    for k,v in d.iteritems():
        if k in keys:
            result[k]=v
    return result

def numberAbbr(num):
    num = float(num)
    if num < 100:
        return format( num, '.02f' )
    if num >= 100 and num < 1000:
        return str( int(round(num)) )
    if num >= 1000 and num < 1000000:
        return format( num/1000.0, '.01f' ) + 'k'
    if num >= 1000000:
        return format( num/1000000, '.02f' ) + 'm'

def getCustomHUD(cam, layer):
    # this method should be used to display custom focal length when stereo playblasting
    fov = ''
    infinite = ''
    roundness = ''
    bestPosition = ''
    pink = ''
    version = ''
    if not pm.objExists(cam):
        return ''

    cam = pm.PyNode(cam)
    try:
        fov = format( round(cam.focalLength.get(t=pm.currentTime(q=True))), '.0f' )
    except:
        pass

    try:
        safePlane = cam.listRelatives(type=safePlaneNodeType, ad=True)
        if safePlane:
            if safePlane[0].hasAttr('outInfinite'):
                infinite = safePlane[0].attr('outInfinite').get(t=pm.currentTime(q=True))
                if infinite <= 0:
                    infinite = '0'
                else:
                    infinite = format( infinite, '.02f' )
            if safePlane[0].hasAttr('outRoundness'):
                roundness = safePlane[0].attr('outRoundness').get(t=pm.currentTime(q=True))
                if roundness <= 0:
                    roundness = '0'
                else:
                    roundness = format(roundness, '.02f')
            if safePlane[0].hasAttr('outBestPosition'):
                bestPosition = safePlane[0].attr('outBestPosition').get(t=pm.currentTime(q=True))
                if bestPosition <= 0:
                    bestPosition = 0
                bestPosition = numberAbbr(bestPosition)
            if safePlane[0].hasAttr('redWashPosition'):
                pink = safePlane[0].attr('redWashPosition').get(t=pm.currentTime(q=True))
                pink = format(pink, '.01f')
            if safePlane[0].hasAttr('versionSwitch'):
                version = str(safePlane[0].attr('versionSwitch').get())
    except:
        pass

    if layer=='near':
        return 'near: '+infinite+', ('+roundness+', '+bestPosition+', '+pink+')'
    elif layer=='far':
        return 'far: '+infinite+', ('+roundness+', '+bestPosition+', '+pink+')'
    else:
        return fov+', '+infinite+', ('+roundness+', '+bestPosition+', '+pink+'), ' + version

def makeBluescreen(value, renderers):
    '''
    if value is absent, then we store the default background color into value, return it, and change
    the background to blue screen.
    if the value is valid, then we simply assign the value to the background
    '''
    if not value:
        # store the default value
        for color in pm.displayRGBColor(list=True):
            if color.startswith('backgroundTop'):
                value.update( {'backgroundTop':[float(c) for c in color.strip().split(' ')[1:]]} )
            if color.startswith('backgroundBottom'):
                value.update( {'backgroundBottom':[float(c) for c in color.strip().split(' ')[1:]]} )
        value.update( {'displayGradient':pm.displayPref(query=True, displayGradient=True)} )
        # set background
        pm.displayPref(displayGradient=True)
        if renderers=='vp2Renderer':
            pm.displayRGBColor('backgroundTop', 0, 0, 0)
            pm.displayRGBColor('backgroundBottom', 0, 0, 0)
        else:
            pm.displayRGBColor('backgroundTop', 0, 0, 1)
            pm.displayRGBColor('backgroundBottom', 0, 0, 1)
        return value
    else:
        pm.displayPref(displayGradient=value['displayGradient'])
        pm.displayRGBColor('backgroundTop', value['backgroundTop'][0], value['backgroundTop'][1], value['backgroundTop'][2])
        pm.displayRGBColor('backgroundBottom', value['backgroundBottom'][0], value['backgroundBottom'][1], value['backgroundBottom'][2])

def deleteUselessHudExpression():
    try:
        # try to delete useless expression for hud updating
        if not pm.headsUpDisplay('frameCounterHUD', query=True, ex=True) and pm.objExists('frameCounterUpdate'):
            pm.delete('frameCounterUpdate')
        if not pm.headsUpDisplay('timeCodeHUD', query=True, ex=True) and pm.objExists('timeCodeUpdate'):
            pm.delete('timeCodeUpdate')
    except:
        pass

def setShaders(renderers):
    '''
    set the shaders' parameters to keep consistent between vp2 and default render
    this method need be used only for HUD material in TPR project.
    '''
    # hud shader
    try:
        hud_shaders = [s for s in pm.ls('hud_lambert*') if not str(s).endswith('SG')]
        for s in hud_shaders:
            if renderers=='vp2Renderer':
                s.attr('incandescence').set(0,0,0)
            else:
                s.attr('incandescence').set(0,0.815,1)
    except:
        pass

def restoreShaders():
    # hud shader
    try:
        hud_shaders = [s for s in pm.ls('hud_lambert*') if not str(s).endswith('SG')]
        for s in hud_shaders:
            s.attr('incandescence').set(0,0.815,1)
    except:
        pass

def buildPlayblastWindow(cameras, layer, layer_number, add_float_window, renderers, is_rear_layer=True, \
                        ratio=2.387, display_elements={}):
    print 'Start to build playblasting window...'

    p_window = None
    p_editor = None
    center = cameras['center']

    try:
        p_window = pm.window(title='stereo_pb_window', w=512, h=215)
        form = pm.formLayout()
        p_editor = pm.modelEditor(displayAppearance='smoothShaded', displayTextures=True, displayLights='default')
        #print 'set basic display mode'
        # use viewport engine
        pm.modelEditor(p_editor, e=True, rnm=renderers)
        if display_elements['displayLights']:
            pm.modelEditor(p_editor, e=True, displayLights='all')
        #print 'set displayLights'
        # display elements
        for k,v in display_elements.iteritems():
            cmd = 'modelEditor -e -'+k+(' on ' if v else ' off ')+'"'+p_editor.name()+'"'
            try:
                pm.mel.eval(cmd)
                #print 'set '+k
            except:
                pass
        # turn off sortTransparent
        pm.modelEditor(p_editor, e=True, sortTransparent=False)
        #print 'turn off sortTransparent'
        # turn off color management for view port 2.0
        #if renderers=='vp2Renderer':
        #    try:
        #        pm.modelEditor(p_editor, e=True, cmEnabled=False)
        #        print 'disable color management for viewport2.0'
        #    except:
        #        pass

        column = pm.columnLayout('true')
        pm.formLayout( form, edit=True, attachForm=[(column, 'top', 0), (column, 'left', 0), (p_editor, 'top', 0), (p_editor, 'bottom', 0), (p_editor, 'right', 0)], attachNone=[(column, 'bottom'), (column, 'right')], attachControl=(p_editor, 'left', 0, column))
        pm.showWindow( p_window )
    except:
        print traceback.format_exc()

    # hud display, we disable all available hud, only show the custom value at the top right, and restore the previous hud after playblasting
    huds_current = []
    hud_stereo = 'HudStereo'
    try:
        for huds in pm.headsUpDisplay(query=True, lh=True):
            if pm.headsUpDisplay(huds, query=True, ex=True) and pm.headsUpDisplay(huds, query=True, vis=True):
                huds_current.append(huds)
                pm.headsUpDisplay(huds, edit=True, vis=False)

        if pm.headsUpDisplay(hud_stereo, query=True, ex=True):
            pm.headsUpDisplay(hud_stereo, rem=True)

        block = pm.headsUpDisplay(nfb=4)
        if layer=='near':
            block = block + 1
        elif layer=='far':
            if layer_number==2:
                block = block + 1
            elif layer_number==3:
                block = block + 2
        try:       
            pm.headsUpDisplay( hud_stereo, ao=True, section=4, block=block, padding=15, blockSize='small', blockAlignment='right', dataAlignment='right', label='', dataFontSize='large', command=pm.Callback(getCustomHUD, str(center), layer), event='timeChanged' )
            pm.headsUpDisplay( hud_stereo, refresh=True )
        except:
            print traceback.format_exc()
        try:
            pm.toggleAxis(origin=False)
            pm.viewManip(visible=False)
        except:
            print traceback.format_exc()
    except:
        for huds in huds_current:
            if pm.headsUpDisplay(huds, query=True, ex=True):
                pm.headsUpDisplay(huds, edit=True, vis=True)
        pm.modelEditor(p_editor, edit=True, hud=False)

    # create floating window if any
    safearea = None
    if add_float_window:
        try:
            safearea_inst = sa.SafeArea()
            safearea_inst.enable()
            safearea = safearea_inst.safearea
            try:
                safearea.attr('useSpReticle').set(0)
            except:
                pass
            safearea.attr('panScanDisplayMode').set(2)
            safearea.attr('panScanLineTrans').set(1)
            safearea.attr('panScanMaskTrans').set(0)
            safearea.attr('panScanRatio').set(ratio)
            safearea.attr('panScanAspectRatio').set(ratio)
        except:
            print traceback.format_exc()

    # change background color
    bgColor = None
    if not is_rear_layer:
        bgColor = makeBluescreen({}, renderers)

    # hide stereo layer
    try:
        scf.showLayer2(layer)
    except:
        print traceback.format_exc()

    # set up expression for updating hud
    if pm.headsUpDisplay(hud_stereo, query=True, ex=True) and not pm.objExists('stereoUpdateHUD'):
        pm.expression(n='stereoUpdateHUD', ae=True, s='headsUpDisplay -r '+hud_stereo)

    global stereo_pb_window
    stereo_pb_window = { 'window':p_window, 'editor':p_editor, 'safearea':safearea, 'hud_stereo':hud_stereo, \
                            'huds_current':huds_current, 'bgColor':bgColor, 'ratio':ratio}

    return stereo_pb_window

def cleanPlayblastWindow(ui, renderers):
    print 'Remove playblasting windows and restore settings...'
    # display stereo layers if any
    try:
        scf.showLayer2()
    except:
        print traceback.format_exc()

    # recover transparent sorting
    try:
        pm.modelEditor(ui['editor'], e=True, sortTransparent=True)
    except:
        print traceback.format_exc()

    # delete hud expression
    if pm.objExists('stereoUpdateHUD'):
        pm.delete('stereoUpdateHUD')

    # delete custom hud, restore previous hud
    try:
        if pm.headsUpDisplay(ui['hud_stereo'], query=True, ex=True):
            pm.headsUpDisplay(ui['hud_stereo'], rem=True)

        for huds in ui['huds_current']:
            if pm.headsUpDisplay(huds, query=True, ex=True):
                pm.headsUpDisplay(huds, edit=True, vis=True)
    except:
        print traceback.format_exc()

    # delete safe area
    try:
        safeareaShapes = pm.ls(type='spReticleLoc')
        for safe in safeareaShapes:
            try:
                pm.delete(safe.getParent())
            except:
                pass
    except:
        print traceback.format_exc()

    # restore background color
    if ui['bgColor']:
        makeBluescreen( ui['bgColor'], renderers )

    # delete preview window
    try:
        pm.deleteUI(ui['window'].name(), window=True)
    except:
        print traceback.format_exc()

    try:
        pm.lookThru('persp')
    except:
        print traceback.format_exc()

def _get_curve_type(time, attr):
    if attr.get(t=time) != attr.get(t=time+0.1):
        return 'linear'
    else:
        return 'constant'

def linearInterp(start, end, current, value1, value2):
    if current<start or current>end:
        return False
    if current==start:
        return value1
    if current==end:
        return value2
    return value1+(value2-value1)*(float(current-start)/(end-start))

def setPanScanValues2(fwv, safearea, cut_in, cut_out, ratio, eye='left'):
    '''
        we mix keyframes of both left and right to evaluate scanValues

        example:
        timeline: 1001-----------------------------1024
        leftLeft:   |--------|-------|---------------|
        leftRight:  |----|----------------|----------|
        keyframes:  ^    ^   ^      ^    ^         ^

        keyframes structure:
        {
            time:(left_value, right_value),
            ...
        }
    '''
    l,r=(None, None)
    if eye=='left':
        l = fwv['ll']
        r = fwv['lr']
    else:
        l = fwv['rl']
        r = fwv['rr']

    # collect keyframes
    '''
        example
        keyframes = { 1001:(left_value,right_value), 1024:(left_value,right_value), ... }
    '''
    keyframes = {}
    if not l:
        l = {cut_in:0, cut_out:0}
    if not r:
        r = {cut_in:0, cut_out:0}
    keys = sorted(list(set(l.keys()+r.keys())))
    keys_l = sorted(l.keys())
    keys_r = sorted(r.keys())
    for k in keys:
        if l.has_key(k) and r.has_key(k):
            keyframes.update({k:(l[k],r[k])})
        elif l.has_key(k) and not r.has_key(k):
            index = bisect.bisect_right(keys_r, k)
            start = keys_r[index-1]
            end = keys_r[index]
            min_value = r[start]
            max_value = r[end]
            keyframes.update({k:(l[k],linearInterp(start, end, k, min_value, max_value))})
        elif not l.has_key(k) and r.has_key(k):
            index = bisect.bisect_right(keys_l, k)
            start = keys_l[index-1]
            end = keys_l[index]
            min_value = l[start]
            max_value = l[end]
            keyframes.update({k:(linearInterp(start, end, k, min_value, max_value), r[k])})
    # evaluate panScanOffset curve type
    for i in range(len(keys)-1):
        if abs(keyframes[keys[i]][0]-keyframes[keys[i+1]][0])==0 or abs(keyframes[keys[i]][1]-keyframes[keys[i+1]][1])==0:
            keyframes[keys[i]] = (keyframes[keys[i]][0], keyframes[keys[i]][1], 'step')
        else:
            keyframes[keys[i]] = (keyframes[keys[i]][0], keyframes[keys[i]][1], 'linear')
    keyframes[keys[-1]] = (keyframes[keys[-1]][0], keyframes[keys[-1]][1], 'step')


    # let's delete previous keyframes firstly
    if safearea.attr('panScanRatio').isConnected():
        pm.delete(safearea.attr('panScanRatio').listConnections())
    if safearea.attr('panScanOffset').isConnected():
        pm.delete(safearea.attr('panScanOffset').listConnections())

    # set keyframes
    for k in sorted(keyframes.keys()):
        scanRatio = ratio*(100 - keyframes[k][0] - keyframes[k][1])*0.01
        scanOffset = None
        if keyframes[k][0]==0:
            scanOffset = -1
        elif keyframes[k][1]==0:
            scanOffset = 1
        else:
            r = keyframes[k][0]/keyframes[k][1]
            scanOffset = 2*r/(1+r) - 1
        safearea.attr('panScanRatio').setKey(t=k, v=scanRatio, itt='linear', ott='linear')
        safearea.attr('panScanOffset').setKey(t=k, v=scanOffset, itt='linear', ott=keyframes[k][2])

def setPanScanValues(fwv, safearea, cut_in, cut_out, ratio, eye='left'):
    l,r=(None, None)
    if eye=='left':
        l = fwv['ll']
        r = fwv['lr']
    else:
        l = fwv['rl']
        r = fwv['rr']
    if not l:
        l = {cut_in:0}
    if not r:
        r = {cut_in:0}

    l_ratio = l[l.keys()[0]]
    r_ratio = r[r.keys()[0]]
    scanRatio = ratio*(100 - l_ratio - r_ratio )*0.01
    scanOffset = None
    if l_ratio == 0:
        scanOffset = -1
    elif r_ratio == 0:
        scanOffset = 1
    else:
        r = l_ratio/r_ratio
        scanOffset = 2*r/(1+r) - 1

    safearea.attr('panScanRatio').set(scanRatio)
    safearea.attr('panScanOffset').set(scanOffset)

def fn_playblast(stereocam, file_name, layer_number, cut_in, cut_out, is_rear_layer=True, pb_offscreen=True, \
                 renderers='base_OpenGL_Renderer', display_elements={}, \
                ext='png', widthHeight=[2048,858], enable_anim_floating_window=False):
    center = stereocam
    try:
        left = center.attr('leftCamera').get()
        right = center.attr('rightCamera').get()
    except:
        print 'Failed to get left and right camera from '+str(center)
        return []

    # disable resolution
    try:
        center.attr('displayResolution').set(0)
        center.attr('displayGateMask').set(0)
        center.attr('displayFilmGate').set(0)
    except:
        pass

    # make sure that we play frames in every frame
    try:
        pm.playbackOptions(edit=True, by=1.0)
    except:
        pass

    #get user option before building model editor
    #opt_path = pm.internalVar(usd=True).replace('\\', '/')
    #if os.path.isfile(opt_path+'updatePreviewXmlUserOption.txt'):

    # initial vars before building model editor
    if renderers=='vp2Renderer':
        # if we use viewport2(vp2) render, the images contain alpha channel, 
        # then we simply use imconvert to composite images instead of chrome keying in nuke
        # but imconvert can not recognize tif image, so we change the default tif to png
        ext = 'png'

    layer = 'main'
    if file_name.endswith('.near'):
        layer = 'near'
    elif file_name.endswith('.far'):
        layer = 'far'

    # floating window value
    fwv = scf.getFloatingWindowValues(center, cut_in, cut_out)

    add_float_window = True
    if not fwv['ll'] and not fwv['lr'] and not fwv['rl'] and not fwv['rr']:
        add_float_window = False

    cameras = {'center':center, 'left':left, 'right':right}

    deleteUselessHudExpression()

    # build the model editor
    global stereo_pb_window
    stereo_pb_window_exists = False
    for w in pm.lsUI(type='window'):
        try:
            if pm.window(w, ex=True) and w.getTitle()=='stereo_pb_window':
                stereo_pb_window_exists = True
                break
        except:
            pass
    if stereo_pb_window and stereo_pb_window['window'] and pm.window(stereo_pb_window['window'], ex=True):
        stereo_pb_window_exists = True

    ratio = float(widthHeight[0])/widthHeight[1]

    ui = {}
    if stereo_pb_window_exists:
        ui = stereo_pb_window
    else:
        ui = buildPlayblastWindow(cameras, layer, layer_number, add_float_window, renderers, is_rear_layer, ratio, display_elements)
    p_window = ui['window']
    p_editor = ui['editor']
    safearea = ui['safearea']
    hud_stereo = ui['hud_stereo']
    huds_current = ui['huds_current']
    bgColor = ui['bgColor']

    #global stereo_pb_continue
    #if enable_anim_floating_window and fwv['animated'] and not stereo_pb_continue:
    #    stereo_pb_continue = True
    #    return []

    # playblast left eye first
    try:
        try:
            if safearea:
                safearea.attr('panScanRatio').set(ratio)
                safearea.attr('panScanOffset').set(0)
        except:
            pass
        if safearea and (fwv['ll'] or fwv['lr']):
            try:
                setPanScanValues(fwv, safearea, cut_in, cut_out, ratio, eye='left')
            except:
                print traceback.format_exc()
        try:
            left.attr('overscan').unlock()
            left.attr('overscan').set(1.0)
        except:
            print traceback.format_exc()
        # disable resolution display
        try:
            left.attr('displayResolution').unlock()
            left.attr('displayResolution').set(False)
        except:
            pass
        pm.modelEditor(p_editor, edit=True, camera=left, activeView=True)
        pm.lookThru(left)
        pm.refresh()
    except:
        print traceback.format_exc()

    left_img = pm.playblast( startTime=cut_in, endTime=cut_out,  format='image', filename=file_name+'.left', \
                forceOverwrite=True, sequenceTime=0, clearCache=False, viewer=False, showOrnaments=True, \
                offScreen=True, fp=4, percent=100, compression=ext, widthHeight=(widthHeight[0],widthHeight[1]), quality=100)
    try:
        left.attr('overscan').lock()
        left.attr('displayResolution').lock()
    except:
        pass

    # right eye follows
    try:
        try:
            if safearea:
                safearea.attr('panScanRatio').set(ratio)
                safearea.attr('panScanOffset').set(0)
        except:
            pass
        if safearea and (fwv['rl'] or fwv['rr']):
            try:
                setPanScanValues(fwv, safearea, cut_in, cut_out, ratio, eye='right')
            except:
                print traceback.format_exc()
        try:
            right.attr('overscan').unlock()
            right.attr('overscan').set(1.0)
        except:
            print traceback.format_exc()
        # disable resolution display
        try:
            right.attr('displayResolution').unlock()
            right.attr('displayResolution').set(False)
        except:
            pass
        pm.modelEditor(p_editor, edit=True, camera=right, activeView=True)
        pm.lookThru(right)
        pm.refresh()
    except:
        print traceback.format_exc()

    right_img = pm.playblast( startTime=cut_in, endTime=cut_out,  format='image', filename=file_name+'.right', \
                forceOverwrite=True, sequenceTime=0, clearCache=False, viewer=False, showOrnaments=True, \
                offScreen=True, fp=4, percent=100, compression=ext, widthHeight=(widthHeight[0],widthHeight[1]), quality=100)
    try:
        right.attr('overscan').lock()
        right.attr('displayResolution').lock()
    except:
        pass

    cleanPlayblastWindow(ui, renderers)
    
    #stereo_pb_continue = False

    print left_img
    print right_img
    # the returned filename is formated as path/image_name.####.ext
    return [cf.osPathConvert(left_img), cf.osPathConvert(right_img)]

def pb_stereo(file_name, cut_in, cut_out, pb_offscreen=True, display_elements={}, ext='png', widthHeight=[2048,858], camera_grp='|cameras', renderers='base_OpenGL_Renderer'):
    ''' 
    file_name should be path + filename, without ext, number padding, left and right indicators
    
    we use png by default, png is much lighter than tif, and PIL can handle png very faster than tif,
    and png is lossless compression with alpha channel. There is no reason to use tif format unless you
    want to use the multi-layer function of tif or want to store image in floating data.
    '''

    print 'start stereo playblast!'
    # load plugins
    scf.loadStereoPlugins()
    scf.loadSpReticlePlugins()

    start_time = time.time()

    stereo_cams = [c.getParent() for c in pm.PyNode(camera_grp).listRelatives(type='stereoRigCamera', ad=True)]

    if len(stereo_cams)<=0:
        print 'Failed to find stereo camera!\n'
        return []

    file_name = cf.osPathConvert( file_name )

    if len(stereo_cams)>3:
        print 'More than 3 stereo cameras found!\n' + ', '.join([c.name() for c in stereo_cams])+'\n'
        print 'Please revise your stereo cameras settings. Playblast is terminated.'
        return []

    # determine near, main and far camera if any
    front_layer = 'main'
    rear_layer = 'main'
    if len(stereo_cams)==2:
        if 'near' in ' '.join([n.name().lower() for n in stereo_cams]):
            front_layer = 'near'
        else:
            rear_layer = 'far'
    elif len(stereo_cams)==3:
        front_layer = 'near'
        rear_layer = 'far'

    # get safe planes
    safePlanes = pm.listRelatives(camera_grp, type=safePlaneNodeType, ad=True)

    #renderers = 'base_OpenGL_Renderer'

    if renderers=='vp2Renderer':
        try:
            vpObj = pm.PyNode('hardwareRenderingGlobals')
            #vpObj.attr('vertexAnimationCache').set(2)   # hardware
            #vpObj.attr('maxHardwareLights').set(1)
            #vpObj.attr('threadDGEvaluation').set(1)
            #vpObj.attr('ssaoEnable').set(0) # turn off occlusion
            #vpObj.attr('enableTextureMaxRes').set(1)
            #vpObj.attr('textureMaxResolution').set(512)
            #vpObj.attr('transparencyAlgorithm').set(2)  #weighted average
            #vpObj.attr('colorBakeResolution').set(64)
            #vpObj.attr('bumpBakeResolution').set(64)
            #vpObj.attr('motionBlurEnable').set(0)   # disable motion blur
            vpObj.attr('lineAAEnable').set(0)   # disable smooth wireframe
            vpObj.attr('multiSampleEnable').set(1)  # enable multisampling anti-aliasing
        except:
            pass

    #try:
    #    renderers_list = pm.modelEditor('modelPanel4', q=True, rendererList=True)
    #    if 'vp2Renderer' in renderers_list:
    #        renderers = 'vp2Renderer'
    #except:
    #    pass

    #if renderers=='vp2Renderer':
    #   if we use viewport2(vp2) render, the images contain alpha channel, 
    #   then we simply use imconvert to composite images instead of chrome keying in nuke
    #   but imconvert can not recognize tif image, so we change the default tif to png
    #   ext = 'png'


    disp_elem = getDisplayElements(display_elements)

    # repair nearClipPlane connection between left, right cameras and center camera
    scf.reconnectCameras()

    imgs = {}
    if len(stereo_cams)==1:
        fn_playblast(stereocam=stereo_cams[0], file_name=file_name, layer_number=1, cut_in=cut_in, cut_out=cut_out, \
                        is_rear_layer=True, pb_offscreen=pb_offscreen, renderers=renderers, display_elements=disp_elem, \
                        ext=ext, widthHeight=widthHeight, enable_anim_floating_window=True)
    else:
        for c in stereo_cams:
            key = 'main'
            if c.name().lower().endswith('near'):
                key = 'near'
            elif c.name().lower().endswith('far'):
                key = 'far'
            is_rear_layer = False
            if key == rear_layer:
                is_rear_layer = True
            imgs.update( {key:fn_playblast(stereocam=c, file_name=file_name+'.'+key, \
                            layer_number=len(stereo_cams), cut_in=cut_in, cut_out=cut_out, \
                            is_rear_layer=is_rear_layer, pb_offscreen=pb_offscreen, renderers=renderers, \
                            display_elements=disp_elem, ext=ext, widthHeight=widthHeight, \
                            enable_anim_floating_window=(True if key==front_layer else False) )} )
        print imgs
        # composite
        composit_PIL(imgs, file_name, cut_in, cut_out, renderers)

    end_time = time.time()
    time_elapsed = end_time - start_time
    print 'Time elapsed for playblasting:   '+format(time_elapsed,'.0f')+' seconds'

def composit_PIL(imgs, file_name, cut_in, cut_out, renderers='base_OpenGL_Renderer'):
    compositeMode = 'chromeKey'
    if renderers=='vp2Renderer':
        compositeMode = 'alpha'
    pilp.main(imgs, save_path=file_name, cut_in=cut_in, cut_out=cut_out, compositeMode=compositeMode)


def get_comment_from_mov(input_mov, rvls):
    cmd = rvls+' -x '+input_mov
    (out,err) = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE).communicate()
    comment = ''
    isStereo = False
    reelname = None

    for o in out.split('\n'):
        if 'videotracks' in o.lower():
            if int(o.strip().split(' ')[-1])>1:
                isStereo = True
                continue
        if 'comment' in o.lower():
            comment = ' '.join( [c for c in o.strip().split(' ')[1:] if c] )
            if comment.endswith('loat'):
                comment = comment[:-4]  # I know this is weird
        if 'timecode/name' in o.lower() or 'timecode/reelname' in o.lower():
            reelname = o.strip().split(' ')[-1]

    start_frame = comment.split('-')[0]
    if not start_frame.isdigit():
        start_frame = None
    else:
        start_frame = int(start_frame)

    return {'start_frame':start_frame, 'comment':comment, 'isStereo':isStereo, 'reelname':reelname}

def convert2mov(img_input, mov_output, copyInfoFrom=''):
    '''
        the input images should use %04d or #### for frame padding
        if copyInfoFrom presents, this function will try to copy comment from the presented mov
    '''
    img_input = cf.osPathConvert(img_input)
    mov_output = cf.osPathConvert(mov_output)
    copyInfoFrom = cf.osPathConvert(copyInfoFrom)

    img_dir = os.path.dirname(img_input)
    img_name = os.path.basename(img_input)
    if not os.path.isdir(img_dir):
        print 'Invalid img_input: '+img_input
        return

    left_img = sorted(glob.glob(img_input.replace('%V','left').replace('%04d','*').replace('####','*')))
    right_img = sorted(glob.glob(img_input.replace('%V','right').replace('%04d','*').replace('####','*')))

    if not left_img or not right_img or len(left_img)!=len(right_img):
        print 'Failed to find left or right images, or the length of left is not equal to the right'
        return

    if not mov_output.endswith('.mov') and os.path.isdir(mov_output):
        mov_output = os.path.join( mov_output, '.'.join(img_name.split('.')[:4])+'.stereo.mov' )

    start_frame = int(left_img[0].split('.')[-2])
    end_frame = int(left_img[-1].split('.')[-2])
    reelname = img_name.split('.')[0]

    rv = cf.getRVPath()
    info = {'comment':None, 'audio':None, 'isStereo':True, 'reelname':reelname, 'start_frame':start_frame}

    if copyInfoFrom and os.path.isfile(copyInfoFrom):
        tmp = get_comment_from_mov(copyInfoFrom, rv['rvls'])
        info['comment'] = tmp['comment']
        if '.wav' in tmp['comment']:
            audio_path = [a.strip() for a in tmp['comment'].split(' ') if a.endswith('.wav')]
            if audio_path and os.path.isfile(audio_path):
                info['audio'] = audio_path[0]
    else:
        ma = str(pm.sceneName())
        slider = pm.mel.eval('$tmpVar=$gPlayBackSlider')
        audios = [a for a in pm.ls(type='audio') if reelname in a.name()]
        audio_path = ''
        if audios:
            audio_node = audios[0]
            #slider = pm.mel.eval('$tmpVar=$gPlayBackSlider')
            pm.timeControl(slider, edit=True, displaySound=True, sound=audio_node)
            audio_path = cf.osPathConvert( audio_node.attr('filename').get() )
        info['comment'] = str(start_frame)+'-'+str(end_frame)+' '+ma+' '+('' if not os.path.isfile(audio_path) else audio_path+' ')+str(start_frame)
        if os.path.isfile(audio_path):
            info['audio'] = audio_path

    cmd_str = ''
    if audio_path == '':
        cmd_str = '"' + rv['rvio'] + '" [ ' + img_input.replace('%V', 'left') + ' ' + img_input.replace('%V', 'right') + ' ] -outstereo -o ' + mov_output
    else:
        cmd_str = '"' + rv['rvio'] + '" [ ' + img_input.replace('%V', 'left') + ' ' + img_input.replace('%V', 'right') + ' ' +audio_path + ' ] -audiorate 48000 -outstereo -o ' + mov_output

    cmd_str += ' -outparams comment="%s" timecode=%s' % (info['comment'],str(info['start_frame']))

    print 'Cmd:', cmd_str
    p = subprocess.Popen(cmd_str, shell=rv['rv_shell'])
    (out, err) = p.communicate()

    #cmd_str = '"' + rv['player'] + '" -stereo scanline ' + mov_output
    #print 'Cmd:', cmd_str
    #subprocess.Popen(cmd_str, shell=True)

def get_shot_range(proj_name, shot_name):
    shot_info = sg.find_one('Shot',
                            [['code', 'is', shot_name],
                             ['project', 'name_is', proj_name]],
                            ['sg_cut_in', 'sg_cut_out', 'sg_ani_cut_in', 'sg_ani_cut_out'])
    if not shot_info:
        return [None, None]
    else:
        sg_in, sg_out = sg_utils.get_sg_in_out(shot_info)
        #return [shot_info['sg_cut_in'], shot_info['sg_cut_out']]
        return [sg_in, sg_out]


def main(scene_path='', img_dir='', mov_dir='', shot_name='', pb_offscreen=True,    \
         cut_in=None, cut_out=None, enable_audio=True, img_only=False, play_on_finish=True, \
         display_elements={'dynamics':True, 'nParticles':True}, img_compression='png', \
         widthHeight=[2048,858], camera_grp='|cameras', clean_images=True, renderers='base_OpenGL_Renderer'):
    '''
        scene_path should be a path to a maya file with .ma or .mb extension, or will be filled with current scene name
        automatically if not specified. this maya file name will be used to create mov name:
            my_scene.ma --> my_scene.stereo.mov
        
        Care must be taken that you need install rv player to convert from images to mov,
        if rv player is not available, you could disable converting by set img_only to True, but still generates images.
        
        if img_dir and mov_dir are absent, then the images and mov will be put under the subfolders named as images and data
        in the same path with the scene file
    '''
    
    # get rv path if any
    rv = cf.getRVPath(use_old_version=False)
    rvio = rv['rvio']
    opener = rv['opener']
    player = rv['player']
    rvls = rv['rvls']
    rv_shell = rv['rv_shell']

    if not os.path.isfile(rvio):
        pm.warning('Failed to find rvio path, the left and right images will not be converted to mov file.')

    # Get current maya file path
    file_path = pm.system.Path(scene_path) if scene_path else pm.sceneName()
    file_path = cf.osPathConvert(file_path)
    print 'file_path', file_path
    if not file_path:
        pm.confirmDialog(message ='Invalid scene name or scene path!')
        return

    # prepare to get proj and shot info
    tokens = file_path.split('/')
    file_name = tokens[-1]
    if not file_name.endswith('.ma') and not file_name.endswith('.mb'):
        pm.confirmDialog(message = file_name+': file name should be a maya scene file with .ma or .mb extension')
        return

    # prepare mov name
    mov_file_name = file_name[:-3] + '.stereo.mov'

    if renderers=='vp2Renderer':
        # if we use viewport2(vp2) render, the images contain alpha channel, 
        # then we simply use imconvert to composite images instead of chrome keying in nuke
        # but imconvert can not recognize tif image, so we change the default tif to png
        img_compression = 'png'

    # get shot name
    if not shot_name:
        if 'shot' in tokens:
            i = tokens.index('shot')
            shot_name = tokens[i+2]

    proj_name = dept_name = '' 

    img_dir = cf.osPathConvert(img_dir)
    if not img_dir or not os.path.isdir(img_dir):
        img_dir = os.path.dirname(file_path) + '/images/' + file_name + '/'
    img_dir = img_dir+'/' if not img_dir.endswith('/') else img_dir

    if not os.path.isdir(img_dir):
        try:
            os.makedirs(img_dir)
        except:
            pm.confirmDialog(message = 'Failed to create folder: '+img_dir)
            return
    else:
        # delete old images
        img_left_list = glob.glob(img_dir+file_name[:-3]+'.left.*.%s' % img_compression)
        img_right_list = glob.glob(img_dir+file_name[:-3]+'.right.*.%s' % img_compression)
        try:
            if clean_images:
                for img in img_left_list+img_right_list:
                    if os.path.isfile(img):
                        os.remove(img)
        except:
            pm.confirmDialog(message = 'Failed to remove old images at '+img_dir)
            cmd_str = '"' + opener + '" ' + img_dir
            os.system(cmd_str)
            return

    mov_dir = cf.osPathConvert(mov_dir)
    if not mov_dir or not os.path.isdir(mov_dir):
        mov_dir = os.path.dirname(file_path) + '/data/'
    mov_dir = mov_dir+'/' if not mov_dir.endswith('/') else mov_dir
    if not os.path.isdir(mov_dir):
        try:
            os.makedirs(mov_dir)
        except:
            pm.confirmDialog(message = 'Failed to create folder: '+mov_dir)
            return

    # get cut in and cut out
    if cut_in is None or cut_out is None:
        cut_in = pm.animation.playbackOptions(q=True, minTime=True)
        cut_out = pm.animation.playbackOptions(q=True, maxTime=True)

    print 'cut_in', cut_in
    print 'cut_out', cut_out

    # get audio file if any, we only grab the first audio track
    audios = [a for a in pm.ls(type='audio')]
    audio_path = ''
    if audios and enable_audio:
        audio_node = audios[0]
        slider = pm.mel.eval('$tmpVar=$gPlayBackSlider')
        pm.timeControl(slider, edit=True, displaySound=True, sound=audio_node)
        audio_path = cf.osPathConvert( audio_node.attr('filename').get() )
        if not os.path.isfile(audio_path):
            audio_path = ''

    # get image width and height
    if widthHeight[0]==0 or widthHeight[1]==0:
        widthHeight = [pm.PyNode('defaultResolution').attr('width').get(), pm.PyNode('defaultResolution').attr('height').get()]

    # playblast!
    pb_stereo(img_dir+file_name[:-3], cut_in, cut_out, pb_offscreen=pb_offscreen, display_elements=display_elements, ext=img_compression, widthHeight=widthHeight, camera_grp=camera_grp, renderers=renderers)

    if img_only:
        print 'Playblasted left and right images at: ', img_dir
        return img_dir

    # prepare rv converting command string
    # get left and right image path, check the image sequence
    img_left = img_dir+file_name[:-3]+'.left.#.%s' % img_compression
    img_right = img_dir+file_name[:-3]+'.right.#.%s' % img_compression
    img_left_list = sorted( glob.glob(img_left.replace('#','*')) )    # glob doesn't recognize # symbol
    img_right_list = sorted( glob.glob(img_right.replace('#','*')) )
    if not ( img_left_list and len(img_left_list)==len(img_right_list) ):
        pm.confirmDialog( title='Error', message='Failed to find images or the length of left image is not equal to the right: \n'+img_left+'\n'+img_right )
        return
    cut_in_img = int(img_left_list[0].split('.')[-2])
    cut_out_img = int(img_left_list[-1].split('.')[-2])
    # rvio command
    if audio_path == '':
        cmd_str = '"' + rvio + '" [ ' + img_left + ' ' + img_right + ' ] -outstereo -o ' + mov_dir + mov_file_name
    else:
        cmd_str = '"' + rvio + '" [ ' + img_left + ' ' + img_right + ' ' +audio_path+' ] -audiorate 48000 -outstereo -o ' + mov_dir + mov_file_name
    cmd_str += ' -outfps 24'
    cmd_str += ' -outparams comment="%s-%s %s %s"' % (cut_in_img, cut_out_img, file_path, audio_path)   # store custom contents in comment attribute
    cmd_str += ' timecode=%s' % cut_in_img          # encode timecode
    if shot_name and rv['version']>=6:
        cmd_str += ' reelname=%s' % shot_name   # encode reelname
    os.environ['RV_ENABLE_MIO_FFMPEG'] = '1'    # RV_ENABLE_MIO_FFMPEG needs to be enable to encode comment attribute

    # execute rvio command
    print 'Cmd: \n', cmd_str
    p = subprocess.Popen(cmd_str, shell=rv_shell)
    (out, err) = p.communicate()
    print 'out', out
    print 'err', err
    print 'Done'
        
    cmd_str = '"'+player+ '" -stereo scanline ' + mov_dir + mov_file_name
    if play_on_finish:
        print 'Cmd:', cmd_str
        p = subprocess.Popen(cmd_str, shell=rv_shell)
        (out, err) = p.communicate()
        print 'out', out
        print 'err', err
        print 'Done'

    return

