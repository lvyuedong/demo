//-
// ==========================================================================
// Copyright 1995,2006,2008 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk
// license agreement provided at the time of installation or download,
// or which otherwise accompanies this software in either electronic
// or hard copy form.
// ==========================================================================
//+

// 
// Description: 
//  The draw data for curvedArrowsLocator node. The vertex and face
//  lists here are used to draw the locator in curvedArrowsNode.cpp.
//  If you intend on using this file for your own locator code, you
//  should statically define the data in a cpp file and forward
//  declare the definitions.
//

#ifndef __stereoSafePlane_h 
#define __stereoSafePlane_h 

//#include <maya/MTypes.h> 

#define STEREO_ORIGIN \
	fsVertexOrg[0] = 0.0; \
	fsVertexOrg[1] = 0.0; \
	fsVertexOrg[2] = 0.0;

#define STEREO_INTEROCULAR \
	fsVertexOcularLeft[0] = 0.0; \
	fsVertexOcularLeft[1] = 0.0; \
	fsVertexOcularLeft[2] = 0.0; \
	fsVertexOcularRight[0] = 0.0; \
	fsVertexOcularRight[1] = 0.0; \
	fsVertexOcularRight[2] = 0.0;

/*
{ 0, 3, 2, 1 }	red plane
{ 4, 7, 6, 5 }	redWash plane
{ 8, 11, 10, 9 }	yellowWash plane
{ 12, 15, 14, 13 }	yellow plane
{ 16, 19, 18, 17 }	green plane
{ 20, 23, 22, 21 }	cyan plane
*/
#define STEREO_PLANE_VERTEXLIST \
		fsVertexList[0][0] = -0.5; \
	fsVertexList[0][1] = -0.5; \
	fsVertexList[0][2] = 0.0; \
	fsVertexList[1][0] = 0.5; \
	fsVertexList[1][1] = -0.5; \
	fsVertexList[1][2] = 0.0; \
	fsVertexList[2][0] = 0.5; \
	fsVertexList[2][1] = 0.5; \
	fsVertexList[2][2] = 0.0; \
	fsVertexList[3][0] = -0.5; \
	fsVertexList[3][1] = 0.5; \
	fsVertexList[3][2] = 0.0; \
		fsVertexList[4][0] = -0.5; \
	fsVertexList[4][1] = -0.5; \
	fsVertexList[4][2] = 0.0; \
	fsVertexList[5][0] = 0.5; \
	fsVertexList[5][1] = -0.5; \
	fsVertexList[5][2] = 0.0; \
	fsVertexList[6][0] = 0.5; \
	fsVertexList[6][1] = 0.5; \
	fsVertexList[6][2] = 0.0; \
	fsVertexList[7][0] = -0.5; \
	fsVertexList[7][1] = 0.5; \
	fsVertexList[7][2] = 0.0; \
		fsVertexList[8][0] = -0.5; \
	fsVertexList[8][1] = -0.5; \
	fsVertexList[8][2] = 0.0; \
	fsVertexList[9][0] = 0.5; \
	fsVertexList[9][1] = -0.5; \
	fsVertexList[9][2] = 0.0; \
	fsVertexList[10][0] = 0.5; \
	fsVertexList[10][1] = 0.5; \
	fsVertexList[10][2] = 0.0; \
	fsVertexList[11][0] = -0.5; \
	fsVertexList[11][1] = 0.5; \
	fsVertexList[11][2] = 0.0; \
		fsVertexList[12][0] = -0.5; \
	fsVertexList[12][1] = -0.5; \
	fsVertexList[12][2] = 0.0; \
	fsVertexList[13][0] = 0.5; \
	fsVertexList[13][1] = -0.5; \
	fsVertexList[13][2] = 0.0; \
	fsVertexList[14][0] = 0.5; \
	fsVertexList[14][1] = 0.5; \
	fsVertexList[14][2] = 0.0; \
	fsVertexList[15][0] = -0.5; \
	fsVertexList[15][1] = 0.5; \
	fsVertexList[15][2] = 0.0;\
		fsVertexList[16][0] = -0.5; \
	fsVertexList[16][1] = -0.5; \
	fsVertexList[16][2] = 0.0; \
	fsVertexList[17][0] = 0.5; \
	fsVertexList[17][1] = -0.5; \
	fsVertexList[17][2] = 0.0; \
	fsVertexList[18][0] = 0.5; \
	fsVertexList[18][1] = 0.5; \
	fsVertexList[18][2] = 0.0; \
	fsVertexList[19][0] = -0.5; \
	fsVertexList[19][1] = 0.5; \
	fsVertexList[19][2] = 0.0;\
		fsVertexList[20][0] = -0.5; \
	fsVertexList[20][1] = -0.5; \
	fsVertexList[20][2] = 0.0; \
	fsVertexList[21][0] = 0.5; \
	fsVertexList[21][1] = -0.5; \
	fsVertexList[21][2] = 0.0; \
	fsVertexList[22][0] = 0.5; \
	fsVertexList[22][1] = 0.5; \
	fsVertexList[22][2] = 0.0; \
	fsVertexList[23][0] = -0.5; \
	fsVertexList[23][1] = 0.5; \
	fsVertexList[23][2] = 0.0;

#define STEREO_PLANE_VERTEXLISTSIZE \
fsVertexListSize = sizeof(fsVertexList)/sizeof(fsVertexList[0]);

#define STEREO_PLANE_NORMALLIST \
	for(int i=0; i<24; i++){ \
		fsNormalList[i][0] = 0; \
		fsNormalList[i][1] = 0; \
		fsNormalList[i][2] = 1; \
	}
// static unsigned int fsNormalListSize = sizeof(fsNormalList)/sizeof(fsNormalList[0]);

typedef unsigned int uint3[3]; 

#define STEREO_PLANE_FACELIST \
	fsFaceList[0][0] = 1;\
	fsFaceList[0][1] = 2;\
	fsFaceList[0][2] = 4;\
	fsFaceList[1][0] = 4;\
	fsFaceList[1][1] = 2;\
	fsFaceList[1][2] = 3;\
	fsFaceList[2][0] = 5;\
	fsFaceList[2][1] = 6;\
	fsFaceList[2][2] = 8;\
	fsFaceList[3][0] = 8;\
	fsFaceList[3][1] = 6;\
	fsFaceList[3][2] = 7;\
	fsFaceList[4][0] = 9;\
	fsFaceList[4][1] = 10;\
	fsFaceList[4][2] = 12;\
	fsFaceList[5][0] = 12;\
	fsFaceList[5][1] = 10;\
	fsFaceList[5][2] = 11;\
	fsFaceList[6][0] = 13;\
	fsFaceList[6][1] = 14;\
	fsFaceList[6][2] = 16;\
	fsFaceList[7][0] = 16;\
	fsFaceList[7][1] = 14;\
	fsFaceList[7][2] = 15;\
	fsFaceList[8][0] = 17;\
	fsFaceList[8][1] = 18;\
	fsFaceList[8][2] = 20;\
	fsFaceList[9][0] = 20;\
	fsFaceList[9][1] = 18;\
	fsFaceList[9][2] = 19;\
	fsFaceList[10][0] = 21;\
	fsFaceList[10][1] = 22;\
	fsFaceList[10][2] = 24;\
	fsFaceList[11][0] = 24;\
	fsFaceList[11][1] = 22;\
	fsFaceList[11][2] = 23;
	//{1, 2, 4},
	//{4, 2, 3},
	//{5, 6, 8},
	//{8, 6, 7},
	//{9, 10, 12},
	//{12, 10, 11},
	//{13, 14, 16},
	//{16, 14, 15}

#define STEREO_PLANE_FACELISTSIZE \
fsFaceListSize = sizeof(fsFaceList)/sizeof(fsFaceList[0]);

#define STEREO_PLANE_FACEVERTEXNORMALLIST \
	fsFaceVertexNormalList[0][0] = 1;\
	fsFaceVertexNormalList[0][1] = 2;\
	fsFaceVertexNormalList[0][2] = 4;\
	fsFaceVertexNormalList[1][0] = 4;\
	fsFaceVertexNormalList[1][1] = 2;\
	fsFaceVertexNormalList[1][2] = 3;\
	fsFaceVertexNormalList[2][0] = 5;\
	fsFaceVertexNormalList[2][1] = 6;\
	fsFaceVertexNormalList[2][2] = 8;\
	fsFaceVertexNormalList[3][0] = 8;\
	fsFaceVertexNormalList[3][1] = 6;\
	fsFaceVertexNormalList[3][2] = 7;\
	fsFaceVertexNormalList[4][0] = 9;\
	fsFaceVertexNormalList[4][1] = 10;\
	fsFaceVertexNormalList[4][2] = 12;\
	fsFaceVertexNormalList[5][0] = 12;\
	fsFaceVertexNormalList[5][1] = 10;\
	fsFaceVertexNormalList[5][2] = 11;\
	fsFaceVertexNormalList[6][0] = 13;\
	fsFaceVertexNormalList[6][1] = 14;\
	fsFaceVertexNormalList[6][2] = 16;\
	fsFaceVertexNormalList[7][0] = 16;\
	fsFaceVertexNormalList[7][1] = 14;\
	fsFaceVertexNormalList[7][2] = 15;\
	fsFaceVertexNormalList[8][0] = 17;\
	fsFaceVertexNormalList[8][1] = 18;\
	fsFaceVertexNormalList[8][2] = 20;\
	fsFaceVertexNormalList[9][0] = 20;\
	fsFaceVertexNormalList[9][1] = 18;\
	fsFaceVertexNormalList[9][2] = 19;\
	fsFaceVertexNormalList[10][0] = 21;\
	fsFaceVertexNormalList[10][1] = 22;\
	fsFaceVertexNormalList[10][2] = 24;\
	fsFaceVertexNormalList[11][0] = 24;\
	fsFaceVertexNormalList[11][1] = 22;\
	fsFaceVertexNormalList[11][2] = 23;
	//{1, 2, 4},\
	//{4, 2, 3},\
	//{5, 6, 8},\
	//{8, 6, 7},\
	//{9, 10, 12},\
	//{12, 10, 11},\
	//{13, 14, 16},\
	//{16, 14, 15} };

// static unsigned int fsFaceVertexNormalListSize = sizeof(fsFaceVertexNormalList)/sizeof(fsFaceVertexNormalList[0]);

#define STEREO_PLANE_EDGELOOP \
fsEdgeLoop[0] = 0; \
fsEdgeLoop[1] = 3; \
fsEdgeLoop[2] = 2; \
fsEdgeLoop[3] = 1; \
fsEdgeLoop1[0] = 4; \
fsEdgeLoop1[1] = 7; \
fsEdgeLoop1[2] = 6; \
fsEdgeLoop1[3] = 5; \
fsEdgeLoop2[0] = 8; \
fsEdgeLoop2[1] = 11; \
fsEdgeLoop2[2] = 10; \
fsEdgeLoop2[3] = 9; \
fsEdgeLoop3[0] = 12; \
fsEdgeLoop3[1] = 15; \
fsEdgeLoop3[2] = 14; \
fsEdgeLoop3[3] = 13; \
fsEdgeLoop4[0] = 16; \
fsEdgeLoop4[1] = 19; \
fsEdgeLoop4[2] = 18; \
fsEdgeLoop4[3] = 17; \
fsEdgeLoop5[0] = 20; \
fsEdgeLoop5[1] = 23; \
fsEdgeLoop5[2] = 22; \
fsEdgeLoop5[3] = 21; \
fsEdgeFrustumLoop1[0] = 0; \
fsEdgeFrustumLoop1[1] = 4; \
fsEdgeFrustumLoop2[0] = 3; \
fsEdgeFrustumLoop2[1] = 7; \
fsEdgeFrustumLoop3[0] = 2; \
fsEdgeFrustumLoop3[1] = 6; \
fsEdgeFrustumLoop4[0] = 1; \
fsEdgeFrustumLoop4[1] = 5;
/*
{ 0, 3, 2, 1 }	red plane
{ 4, 7, 6, 5 }	redWash plane
{ 8, 11, 10, 9 }	yellowWash plane
{ 12, 15, 14, 13 }	yellow plane
{ 16, 19, 18, 17 }	green plane
{ 20, 23, 22, 21 }	cyan plane
*/

#define STEREO_PLANE_EDGELOOPSIZE \
fsEdgeLoopSize = 4; \
fsEdgeFrustumLoopSize = 2;

#endif 
