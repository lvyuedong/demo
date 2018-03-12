# -*- coding: utf-8 -*-
__author__ = 'lvyuedong'

import os
import sys
import traceback
import math
import shutil
import subprocess
import multiprocessing as mp
import time
import optparse

python_path = '/'.join(__file__.replace('\\','/').split('/')[:-2])
print 'python path: '+python_path
sys.path.append(python_path)
import commonFunc as cf
reload(cf)

EXT = ['tif','tiff','png','jpg','jpeg','tga','exr','sgi','tga','iff','dpx','bmp','hdr','gif','ppm','xpm']

def findTexture(path, ext=EXT):
    tex = []
    for path, dirs, files in os.walk(path):
        tex_converted = [f for f in files if f.endswith('.tex')]
        for f in list(set(files).difference(tex_converted)):
            tmp = f.split('.')
            if tmp[-1].lower() not in ext:
                continue
            img_name = '.'.join(tmp[:-1]) 
            if img_name+'.tex' in tex_converted or f+'.tex' in tex_converted:
                continue
            tex.append(os.path.join(path,f))
    tex = list(set(tex))
    return tex

def texConvertSingleThread(txmake, input_img, ch, mode, output):
    # input_img should be a list
    if not input_img:
        output.put( {'empty input_img':False} )
        return

    channels = ','.join([str(c) for c in ch])
    mode = '' if mode=='black' else '-mode '+mode+' '
    for i in input_img:
        print '"'+txmake+'" -ch '+channels+' '+mode+'"'+i+'" "'+i+'.tex"'
        try:
            os.system('"'+txmake+'" -ch '+channels+' '+mode+'"'+i+'" "'+i+'.tex"' )
        except:
            output.put( {i:False} )
    output.put( {'convert successfully':True} )

def multiProcess(param=[]):
    '''
        param is a list of func and parameters
        param = [ func, [args1], [args2], ... ]
    '''
    output = mp.Queue()
    processes = [ mp.Process( target=param[0], args=tuple( param[n+1]+[output] ) ) for n in range(len(param)-1) ]
    print 'number of process: '+str(len(processes))
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    results = [output.get() for p in processes]
    return results

def channelSelect(ch):
    ch_dict = {'r':0, 'g':1, 'b':2}
    ch_list = []
    for i in range(len(ch)):
        try:
            ch_list.append( ch_dict[ch[i]] )
        except:
            pass
    return ch_list

def main(path, ch='rgb', numOfCores=0, mode='black'):
    path = path.replace('\\', '/').strip()
    textures = findTexture(path)
    cf.printColorText( '\nThe following texture will be converted: \n', cf.GREEN )
    print '\n'.join(textures)

    txmake_path='/opt/pixar/RenderManProServer-21.5/bin/txmake'
    print '\ntxmake path: '+txmake_path

    # collect parameters for multi-processing
    failed = []
    if numOfCores==0:
        numOfCores = mp.cpu_count()
    img_index = range(len(textures))
    ch_list = channelSelect(ch)
    mode = mode.lower().strip()
    if mode not in ['black', 'clamp', 'periodic']:
        mode = 'black' if '0' in mode else 'clamp' if '1' in mode else 'periodic'
    
    param = [texConvertSingleThread]
    for index_grp in cf.splitFrames(img_index, numOfCores):
        t = [textures[i] for i in index_grp]
        param.append( [ txmake_path, t, ch_list, mode ] )
    # multi process
    cf.printColorText('\nStart to convert...\n', cf.GREEN)
    start_time = time.time()
    result = multiProcess( param )
    # check result
    error_tex = []
    for r in result:
        try:
            if not r.values()[0]:
                cf.printColorText('\nFailed to convert: ' + str(r.keys()[0])+'\n', cf.RED)
                error_tex.append( str(r.keys()[0]) )
        except:
            print traceback.format_exc()
    # print time
    end_time = time.time()
    time_elapsed = end_time - start_time
    if time_elapsed > 0:
        print ('Time elapsed for total of %d textures: '+cf.time2Durations(time_elapsed)) % (len(textures))

if __name__ == '__main__':
    ''' === Args Parsing === '''
    parser = optparse.OptionParser()
    parser.add_option('-p', '--path', dest='path', help='project name', default='')
    parser.add_option('-c', '--ch', dest='channels', help='channels, like rgb, bbb...', default='rgb')
    parser.add_option('-t', '--threads', dest='threads', help='threads, default is the number of cpu cores', default=0)
    parser.add_option('-m', '--mode', dest='mode', help='set wrap mode for s and t, black|clamp|periodic', default='black')

    (options, args) = parser.parse_args()
    main( options.path, options.channels, options.threads, options.mode )

    sys.exit(0)