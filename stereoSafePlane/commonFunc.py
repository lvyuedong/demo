# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import shutil
import re
import bisect
import datetime
import StringIO

import commonVar as cvar
reload(cvar)

pm = None
mel = None
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#following from Python cookbook, #475186
def hasColors(stream):
    # stream should be sys.stdout
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False

has_color = False
try:
    has_color = hasColors(sys.stdout)
except:
    has_color = False

def printColorText(text, color=BLACK, has_color_local=has_color):
    if has_color_local:
        seq = "\x1b[1;%dm" % (30+color) + text + "\x1b[0m"
        sys.stdout.write(seq)
    else:
        sys.stdout.write(text)

def osPathConvert(path):
    path = path.replace('\\', '/')
    if os.name == 'nt':
        if path.startswith('/mnt/proj/'):
            return path.replace('/mnt/proj/', 'Z:/')
        elif path.startswith('/mnt/work/'):
            return path.replace('/mnt/work/', 'W:/')
        elif path.startswith('/output/'):
            return path.replace('/output/', 'O:/')
        elif path.startswith('/mnt/utility/'):
            return path.replace('/mnt/utility/', 'U:/')
        elif path.startswith('/mnt/public/'):
            return path.replace('/mnt/public/', 'P:/')
        elif path.startswith('/mnt/usr/'):
            return path.replace('/mnt/usr/', 'C:/Program Files/')
        else:
            return path
    else:
        if path.startswith('Z:/'):
            return path.replace('Z:/', '/mnt/proj/')
        elif path.startswith('W:/'):
            return path.replace('W:/', '/mnt/work/')
        elif path.startswith('O:/'):
            return path.replace('O:/', '/output/')
        elif path.startswith('U:/'):
            return path.replace('U:/', '/mnt/utility/')
        elif path.startswith('P:/'):
            return path.replace('P:/', '/mnt/public/')
        elif path.startswith('C:/Program Files/'):
            return path.replace('C:/Program Files/', '/mnt/usr/')
        else:
            return path
    return path

def getRVPath(use_old_version=False):
    '''
        for more info about rv player, visit http://www.tweaksoftware.com/
        rvio can be used to put multi-track video into one single movie as quicktime allows to do this,
        which is perfect way to pack left and right image sequence to fuse stereo movie.

        Since 6.x.x version, rv supports to encode reel name into quicktime movie.
        Reel name, is also shot name in our pipeline, can be recognized by editing software.
    '''
    if sys.platform.startswith('win'):
        rvio = "C:/Program Files/Tweak/RV-4.0.10-64/bin/rvio.exe"
        opener = "C:/Program Files/Internet Explorer/iexplore.exe"
        player = "C:/Program Files/Tweak/RV-4.0.10-64/bin/rv.exe"
        rv = player
        rvls = "C:/Program Files/Tweak/RV-4.0.10-64/bin/rvls.exe"
        rv_shell = False
        version = 4
    elif sys.platform.startswith('linux'):
        rvio = "/usr/local/rv/rv-Linux-x86-64-6.2.2/bin/rvio"
        opener = "gnome-open"
        player = "/usr/local/rv/rv-Linux-x86-64-6.2.2/bin/rv"
        rvls = "/usr/local/rv/rv-Linux-x86-64-6.2.2/bin/rvls"
        rv_shell = True
        version = 6
        if use_old_version or not os.path.isfile(rvio):
            rvio = "/usr/local/rv/rv-Linux-x86-64-4.0.10/bin/rvio"
            player = "/usr/local/rv/rv-Linux-x86-64-4.0.10/bin/rv"
            rvls = "/usr/local/rv/rv-Linux-x86-64-4.0.10/bin/rvls"
            version = 4
        rv = player

    return {'rvio':rvio, 'opener':opener, 'rvls':rvls, 'rv_shell':rv_shell, 'player':player, 'rv':rv, 'version':version}

def splitFrames(frame_range, numOfCores):
    '''
    this method is used initially for spliting frames, but can be used to split any list of objects.
    split the given serial frame ranges by given numOfCores(or cpus), the result can be used by multiprocessing
    result: [[x1, x2, ...], ...]
    the result will be a list includes a group of list. The number of the groups will be equal to numOfCores
    '''
    numOfCores = int(numOfCores)
    length = len(frame_range)
    remainder = length % numOfCores
    if length <= numOfCores:
        return [[i] for i in frame_range]
    elif remainder==0:
        num_element = int(length/numOfCores)
        return [ frame_range[i:i+num_element] for i in range(0, length, num_element) ]
    else:
        num_element = int(math.floor((length-remainder)/float(numOfCores))+1)
        group_end_frame = num_element*remainder
        group1 = [ frame_range[i:i+num_element] for i in range(0, group_end_frame, num_element) ]
        group2 = [ frame_range[i:i+num_element-1] for i in range(group_end_frame, length, num_element-1) ]
        return group1 + group2

def generateLayoutMovsCmd(mov1, mov2):
    # by feeding two movies, this method give the command to launch rv to display the two moves in column mode
    rv_dict = getRVPath()
    mov1 = osPathConvert(mov1)
    mov2 = osPathConvert(mov2)
    if not os.path.isfile(mov1):
        print 'Failed to find file: '+mov1
        return ''
    if not os.path.isfile(mov2):
        print 'Failed to find file: '+mov2
        return ''
    cmd = rv_dict['player']+' '+mov1+' '+mov2+' -layout column -view defaultLayout'
    return cmd

def getStepTaskMaps(step_or_task='', output_maps={}):
    if isinstance(step_or_task, dict):
        print 'If you want to get the maps, then you must feed the pair of the parameter idendifier and value'
        return []
    step_or_task = str(step_or_task).strip().lower()
    m = {'stereo':'flo', 'final_layout':'flo', 'animation':'ani', 'rough_layout':'lay', \
            'lighting':'lgt', 'cloth':'cfx', 'hair':'cfx', 'matte_painting':'dmt', \
            'paint_fix':'pfx', 'floating_window':'pfx', 'set_dressing':'set'}
    output_maps.update(m)
    if step_or_task in m.keys():
        return [m[step_or_task]]
    elif step_or_task in m.values():
        d = {}
        [d.update({v:[k]}) if not d.has_key(v) else d[v].append(k) for (k,v) in m.items()]
        return d[step_or_task]
    return []

def getLatestMov(shot, proj=cvar.default_proj):
    # retrivie task versions
    task_maps = {}
    getStepTaskMaps(output_maps=task_maps)
    '''
    init task_versions as a following dict
    {'latest':None, 'stereo':None, 'final_layout':None, 'animation':None, 'rough_layout':None, \
            'lighting':None, 'cloth':None, 'hair':None, 'matte_painting':None, \
            'paint_fix':None, 'floating_window':None, 'set_dressing':None}
    '''
    task_versions = dict.fromkeys(task_maps.keys())
    path = osPathConvert('/mnt/proj/projects/'+proj+'/shot/'+shot[:3]+'/'+shot)
    if not os.path.isdir(path):
        return task_versions
    last_version = ''
    mtime = 0
    for k in task_versions.keys():
        mov_list = [path+'/'+task_maps[k]+'/publish/'+v+'/preview/'+v+'.mov' \
                    for v in sorted(os.listdir(path+'/'+task_maps[k]+'/publish/')) \
                        if v.startswith(shot+'.%s.%s.'%(task_maps[k],k))]
        for i in range(len(mov_list)):
            if not os.path.isfile(mov_list[i]) or k=='stereo':
                mov_list[i] = path+'/'+task_maps[k]+'/publish/'+v+'/preview/'+v+'.stereo.mov'
                if not os.path.isfile(mov_list[i]):
                    mov_list[i] = ''
        mov_list = [m for m in mov_list[:] if m]
        if mov_list:
            statinfo = os.stat(mov_list[-1])
            if statinfo.st_mtime > mtime:
                mtime = statinfo.st_mtime
                last_version = mov_list[-1]
        task_versions.update({k:mov_list})
    task_versions.update({'latest':[last_version]})
    '''
    the returned dict will be formatted like this:
    {'latest':['version_path'], 'stereo':['version1_path', 'version2_path', ...], ...}
    '''
    return task_versions

def viewLatestMov(shot, proj=cvar.default_proj, latest=True, task=''):
    '''
    given shot or sequence name, this method return a rv command which
    grabs the latest movs among the tasks.
    If task is present, then we only grab the latest mov from this task, regardless of latest setting
    If latest is True, then we compare the time stamp among the movs, and use the latest version.
    If latest is False, then we only use the version from the last step if any, regardless of the time
    '''
    shots = filterShots(shot, proj)
    if not shots:
        print 'Failed to find any shots! please check your shot and project name.'
        return ''
    is_multi_shots = True if len(shots)>1 else False
    rv_dict = getRVPath()
    task_order = ['floating_window', 'paint_fix', 'lighting', 'matte_painting', 'set_dressing', 'stereo', \
                    'final_layout', 'cloth', 'hair', 'animation', 'rough_layout']

    no_publish_warning = os.path.join( os.path.dirname(__file__), 'refs/no_publish_#.png' )
    mov_list = []
    failed = []
    if is_multi_shots:
        # we use status of shots from shotgun to filter omit shots out
        import production.shotgun_connection as shotgun_connection
        reload(shotgun_connection)
        sg = shotgun_connection.Connection('get_project_info').get_sg()
        info = sg.find('Shot', [['project', 'name_is', proj], ['sg_sequence', 'name_is', shots[0][:3]], \
                        ['code', 'starts_with', shots[0][:3]], ['sg_status_list', 'is_not', 'omt']], \
                        ['code'])
        tmp = []
        for i in info:
            tmp.append(i['code'])
        shots = sorted( list(set(shots).intersection(tmp)) )

    for s in shots:
        task_versions = getLatestMov(s, proj)
        if not [v for v in task_versions.values() if v]:
            # if there is no any publish version found for this shot
            mov_list.append(no_publish_warning.replace('#', 'version'))
            failed.append(s+': no publish version for this shot')
            continue
        if task:
            if task in task_order and task_versions[task]:
                mov_list.append(task_versions[task][-1])
            else:
                mov_list.append(no_publish_warning.replace('#', task))
                failed.append(s+': no publish version for the '+task+' task')
        elif latest:
            if task_versions.has_key('latest') and task_versions['latest']:
                mov_list.append(task_versions['latest'][-1])
        else:
            for t in task_order:
                if task_versions.has_key(t) and task_versions[t]:
                    mov_list.append(task_versions[t][-1])
                    break

    if not mov_list:
        print 'Failed to find any movs!'
        return ''
    if failed:
        print '\n'.join(failed)

    cmd = rv_dict['player']+' '+' '.join(mov_list)
    return cmd

def regulateTaskName(t):
    task_maps = {}
    getStepTaskMaps(output_maps=task_maps)
    t = str(t).lower().strip().replace(' ', '_')
    if t not in task_maps.keys():
        if 'floating' in t or 'fw' in t:
            return 'floating_window'
        if 'pfx' in t or 'paintfix' in t or 'fix' in t:
            return 'paint_fix'
        if 'light' in t or 'lgt' in t:
            return 'lighting'
        if 'matte' in t or 'mp' in t or 'dmt' in t:
            return 'matte_painting'
        if 'set' in t:
            return 'set_dressing'
        if 'final' in t or 'flo' in t:
            return 'final_layout'
        if 'ani' in t:
            return 'animation'
        if 'rough' in t or 'layout' in t or 'rlo' in t:
            return 'rough_layout'
        return ''
    else:
        return t

def compareLatestMov(task1, task2, shot, proj=cvar.default_proj, output_versions={}, only_retriving=False, viewing=False, latest=True):
    '''compare the two latest mov previews of the tasks,
    if the task names are the same, then compare the two most recent versions of the task.
    Return a rv command.

    This method may be also used for retriving the latests mov versions for all task,
    just feed the output_versions as a dict, and switch only_retriving to True

    if viewing is True, then this method switch to viewLatestMov method
    '''
    task1 = regulateTaskName(task1)
    task2 = regulateTaskName(task2)

    if viewing:
        # viewLatestMov mode
        rv_cmd = viewLatestMov(shot, proj, latest, task1)
        if rv_cmd:
            os.system(rv_cmd)
        return rv_cmd

    if not shot or not isinstance(shot, str) or not len(shot)==6 or \
        not shot[0].isalpha() or not shot[1:].isdigit():
        print 'compareLatestVersions: invalid shot name '+str(shot)
        return ''

    task_versions = getLatestMov(shot, proj)

    output_versions.clear()
    output_versions.update(task_versions)
    if only_retriving:
        return ''

    if task1 not in task_versions.keys() or task2 not in task_versions.keys():
        print 'Invalid task name found: '+task1+' '+task2
        print 'The task name should be one of the following names:\n' + ', '.join(task_versions.keys())
        return ''
    # compare
    if len(task_versions[task1])<1:
        print 'There is no versions found for task '+task1
        return ''
    if len(task_versions[task2])<1:
        print 'There is no versions found for task '+task2
        return ''
    mov1 = task_versions[task1][-1]
    mov2 = task_versions[task2][-1]
    if mov1 == mov2:
        if len(task_versions[task2])>1:
            mov2 = task_versions[task2][-2]
        else:
            print 'There is only one version for task '+task2+\
                ', are you really comparing the same tasks among the most recent versions of '+task2+'?'
            return ''
    rv_cmd = generateLayoutMovsCmd(mov1, mov2)
    os.system(rv_cmd)
    # generate shell script
    #script_name = 'shell_script_'+shot+'_'+os.path.basename(mov1.split('.')[2])+'_'+\
    #                os.path.basename(mov2.split('.')[2])
    #script_path = '/tmp/compare_latest_versions/'
    return rv_cmd

def time2Durations(t):
    # t should be measured in second, as returned by time.time()
    s = t%60
    m = math.floor(t/60.0)
    h = math.floor(m/60.0)
    d = math.floor(h/24.0)
    return format(d, '.0f')+' days '+format(math.fmod(h,24),'.0f')+' hours '+format(math.fmod(m,60),'.0f')+' minutes '+format(s,'.0f')+' seconds'

def stripMultiSpaces(shotname):
    spaces = re.findall(' {2,}', shotname)
    spaces = list(set(spaces))
    for s in spaces:
        shotname = shotname.replace(s, ' ')
    return shotname

def getShotsFromSeq(seq, projname):
    try:
        shots = [s.lower() for s in os.listdir('/mnt/proj/projects/'+projname+'/shot/'+seq)]
    except:
        printColorText( 'Error, invalid sequence name: '+seq+'\n', RED )
        return []
    return shots

def suppressPrint(func_object, param_list, stdout_bool=True, stderr_bool=True):
    if not isinstance(param_list, type([])):
        print 'suppressPrint needs a parameter list'
        return

    actualstdout = None
    actualstderr = None
    if stdout_bool:
        actualstdout = sys.stdout
        sys.stdout = StringIO.StringIO()
    if stderr_bool:
        actualstderr = sys.stderr
        sys.stderr = StringIO.StringIO()

    try:
        result = func_object(*param_list)
    except:
        if stdout_bool and actualstdout:
            sys.stdout = actualstdout
        if stderr_bool and actualstderr:
            sys.stderr = actualstderr
        print traceback.format_exc()
        return

    if stdout_bool:
        sys.stdout = actualstdout
    if stderr_bool:
        sys.stderr = actualstderr

    return result

def getUsername():
    return os.environ.get('USERNAME')

def publishVersionUp(path):
    # find the next hightest version of the publish folder
    if not os.path.isdir(path):
        return ''
    versions = sorted([v for v in os.listdir(path) if re.findall('[a-z][0-9]{5}.[a-z]+.[a-z]+.v[0-9]{3}', v)])
    if not versions:
        return ''
    version_num = '.v'+format(int(versions[-1][-3:])+1, '03d')
    return os.path.join(path, versions[-1].replace(versions[-1][-5:], version_num))

def versionUp(v=1, backup_path=''):
    # find the next hightest version number in the backup folder
    version = format(v, '03d')
    if not os.path.isdir(os.path.join(backup_path, version)):
        return os.path.join(backup_path, version)
    else:
        return versionUp(v+1, backup_path)

def createBackupFolder(backup_path):
    if not os.path.isdir(backup_path):
        try:
            os.mkdir(backup_path)
        except:
            print 'Failed to create backup folder: '+backup_path
            return False
    return True

def backup(files_list, source, target, mode='move'):
    for f in files_list:
        s = os.path.join(source, f)
        d = os.path.join(target, f)
        try:
            if mode=='move':
                shutil.move(s, d)
            elif mode=='copy':
                shutil.copyfile(s, d)
        except:
            print 'Failed to move '+s+' to '+d

def findMethods(obj, method_name):
    methods = dir(obj)
    result = []
    for m in methods:
        if method_name.lower() in m.lower():
            result.append(m)
    return result

def findAttrs(obj, attr_name):
    try:
        global pm
        if pm is None:
            import pymel.core as pm
        global mel
        if mel is None:
            import maya.mel as mel
    except:
        pass
        
    attrs = pm.listAttr(obj)
    result = []
    for a in attrs:
        if attr_name.lower() in a.lower():
            result.append(a)
    return result


class UTC(datetime.tzinfo):
    """
    UTC
    a very simple tzinfo object which can be passed to datetime object
    """
    def utcoffset(self, dt):
        return datetime.timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return datetime.timedelta(0)

timestamp_default = datetime.datetime(1,1,1, tzinfo=UTC())

def getTime(path, isDatetime=False):
    try:
        mtime = os.stat(path).st_mtime
        if isDatetime:
            return datetime.datetime.fromtimestamp(mtime, UTC())
        else:
            return mtime
    except:
        print traceback.format_exc()
        return None