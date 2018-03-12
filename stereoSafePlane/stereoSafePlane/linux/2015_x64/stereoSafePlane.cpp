
// Description: 

#include <maya/MPxLocatorNode.h> 
#include <maya/MString.h> 
#include <maya/MTypeId.h> 
#include <maya/MPlug.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MColor.h>
#include <maya/M3dView.h>
#include <maya/MFnPlugin.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnTransform.h>
#include <maya/MMatrix.h>
#include <maya/MTypes.h>
#include <math.h>
#include <stereoSafePlane.h>

#define M_PI       3.14159265358979323846
#define M_PI_2     1.57079632679489661923
#define MAYA_CONSTANT 12.7

#define PERRORfail(stat,msg) \
    if (!(stat)) { stat.perror((msg)); return (stat); }


///////////////////////////////////////////
//	stereoSafePlane                  //
///////////////////////////////////////////

struct stereoParam{
	double x;	//position of redWash plane
	double convergence;
	double percent;
	double focal;
	double film[2];
	double tan_fov[2];
	double green;
	double red;
	double redWash;	// percentage of parallax of redWash plane
	double yellowWash;
	double yellow;
	double size;
	double interocular;
	double further_pos;
	double near_pos;
	double nearer_pos;
	double custom_pos;
	double best_pos;
	double visionField;
	double circle;
	double circle_pos;
};

class stereoSafePlane : public MPxLocatorNode
{
	double *fsVertexOrg;
	double *fsVertexOcularLeft;
	double *fsVertexOcularRight;
	double **fsVertexList;
	unsigned int fsVertexListSize;
	double **fsNormalList;
	unsigned int **fsFaceList;
	unsigned int fsFaceListSize;
	unsigned int **fsFaceVertexNormalList;
	unsigned int *fsEdgeLoop;
	unsigned int *fsEdgeLoop1;
	unsigned int *fsEdgeLoop2;
	unsigned int *fsEdgeLoop3;
	unsigned int *fsEdgeLoop4;
	unsigned int *fsEdgeLoop5;
	unsigned int *fsEdgeFrustumLoop1;
	unsigned int *fsEdgeFrustumLoop2;
	unsigned int *fsEdgeFrustumLoop3;
	unsigned int *fsEdgeFrustumLoop4;
	unsigned int fsEdgeLoopSize;
	unsigned int fsEdgeFrustumLoopSize;
	struct stereoParam param;

public:
	stereoSafePlane();
	virtual ~stereoSafePlane(); 

	virtual void			postConstructor(); 
	
    virtual MStatus   		compute( const MPlug&, MDataBlock&);

	virtual void            draw( M3dView & view, const MDagPath & path, 
								  M3dView::DisplayStyle style,
								  M3dView::DisplayStatus status );

	virtual void			drawConvergenceLine( M3dView &, M3dView::DisplayStatus );
	virtual void			drawFrustumLine( M3dView &, M3dView::DisplayStatus );
	virtual void			drawEdgeLoop( M3dView &, M3dView::DisplayStatus );
	virtual void			drawCircle( M3dView &, M3dView::DisplayStatus );
	
	virtual bool			getCoreData( struct stereoParam * );
	virtual void			moveOutOfControl();
	virtual void			moveAlongZ(double *, double *, double *, double *, double *);
	virtual void			moveScale(double *, double *, double *, double *, double *, double *);
	virtual double			moveVertexList();

	virtual void			printInfo();
	
	virtual bool            isBounded() const;
	virtual MBoundingBox    boundingBox() const; 
	virtual bool			isTransparent() const; 
	virtual bool			drawLast() const; 

	static  void *          creator();
	static  MStatus         initialize();

	//input
	static  MObject			aEnableTransparencySort; 
	static  MObject			aEnableDrawLast; 
	static  MObject			aTransparency;
	static	MObject			aZeroParallax;
	static	MObject			aTranslateZ;
	static	MObject			aPercentage;
	static	MObject			aFocalLength;
	static	MObject			aFilmAperture;
	static	MObject			aRedPosition;
	static	MObject			aRedWashPosition;
	static	MObject			aYellowWashPosition;
	static	MObject			aYellowPosition;
	static	MObject			aGreenPosition;
	static	MObject			aSize;
	static	MObject			aDrawFrustum;
	static	MObject			aDrawConvergenceLine;
	static	MObject			aHideNearerPlane;
	static	MObject			aHideNearPlane;
	static	MObject			aHideFarPlane;
	static	MObject			aHideFurtherPlane;
	static	MObject			aHideCustomPlane;
	static	MObject			aHideCyanPlane;
	static	MObject			aVisionField;
	static	MObject			aHideCircle;
	static	MObject			aCircle;		// this is the position of the screen with real size, default 900 cm

	//output
	static	MObject			aInterocular;
	static	MObject			aFurtherPosition;
	static	MObject			aFarPosition;
	static	MObject			aNearPosition;
	static	MObject			aNearerPosition;
	static	MObject			aCustomPosition;
	static	MObject			aBestPosition;
	
public: 
	static	MTypeId		id;
};

MTypeId stereoSafePlane::id( 0x08192B );
MObject stereoSafePlane::aEnableTransparencySort; 
MObject stereoSafePlane::aEnableDrawLast;
MObject stereoSafePlane::aTransparency;
MObject	stereoSafePlane::aZeroParallax;
MObject stereoSafePlane::aTranslateZ;
MObject	stereoSafePlane::aPercentage;
MObject	stereoSafePlane::aFocalLength;
MObject	stereoSafePlane::aFilmAperture;
MObject	stereoSafePlane::aRedPosition;
MObject	stereoSafePlane::aRedWashPosition;
MObject	stereoSafePlane::aYellowWashPosition;
MObject	stereoSafePlane::aYellowPosition;
MObject	stereoSafePlane::aGreenPosition;
MObject	stereoSafePlane::aSize;
MObject	stereoSafePlane::aDrawFrustum;
MObject	stereoSafePlane::aDrawConvergenceLine;
MObject	stereoSafePlane::aHideNearerPlane;
MObject	stereoSafePlane::aHideNearPlane;
MObject	stereoSafePlane::aHideFarPlane;
MObject	stereoSafePlane::aHideFurtherPlane;
MObject	stereoSafePlane::aHideCustomPlane;
MObject stereoSafePlane::aInterocular;
MObject stereoSafePlane::aFurtherPosition;
MObject stereoSafePlane::aFarPosition;
MObject stereoSafePlane::aNearPosition;
MObject stereoSafePlane::aNearerPosition;
MObject	stereoSafePlane::aCustomPosition;
MObject stereoSafePlane::aBestPosition;
MObject	stereoSafePlane::aHideCyanPlane;
MObject	stereoSafePlane::aVisionField;
MObject	stereoSafePlane::aHideCircle;
MObject	stereoSafePlane::aCircle;

stereoSafePlane::stereoSafePlane() {
	fsVertexOrg = new double [3];
	STEREO_ORIGIN

	fsVertexOcularLeft = new double [3];
	fsVertexOcularRight = new double [3];
	STEREO_INTEROCULAR

	fsVertexList = new double* [24];
	for (int i = 0; i < 24; ++i)
		fsVertexList[i] = new double [3];
	STEREO_PLANE_VERTEXLIST
	STEREO_PLANE_VERTEXLISTSIZE

	fsNormalList = new double* [24];
	for (int i = 0; i < 24; ++i)
		fsNormalList[i] = new double [3];
	STEREO_PLANE_NORMALLIST
	
	fsFaceList = new unsigned int* [12];
	for (int i = 0; i < 12; ++i)
		fsFaceList[i] = new unsigned int [3];
	STEREO_PLANE_FACELIST
	STEREO_PLANE_FACELISTSIZE

	fsFaceVertexNormalList = new unsigned int* [12];
	for (int i = 0; i < 12; ++i)
		fsFaceVertexNormalList[i] = new unsigned int [3];
	STEREO_PLANE_FACEVERTEXNORMALLIST

	fsEdgeLoop = new unsigned int [4];
	fsEdgeLoop1 = new unsigned int [4];
	fsEdgeLoop2 = new unsigned int [4];
	fsEdgeLoop3 = new unsigned int [4];
	fsEdgeLoop4 = new unsigned int [4];
	fsEdgeLoop5 = new unsigned int [4];
	fsEdgeFrustumLoop1 = new unsigned int [4];
	fsEdgeFrustumLoop2 = new unsigned int [4];
	fsEdgeFrustumLoop3 = new unsigned int [4];
	fsEdgeFrustumLoop4 = new unsigned int [4];
	STEREO_PLANE_EDGELOOP
	STEREO_PLANE_EDGELOOPSIZE
}

stereoSafePlane::~stereoSafePlane() {
	delete [] fsVertexOrg;

	for (int i = 0; i < 24; ++i)
		delete [] fsVertexList[i];
	delete [] fsVertexList;

	for (int i = 0; i < 24; ++i)
		delete [] fsNormalList[i];
	delete [] fsNormalList;

	for (int i = 0; i < 12; ++i)
		delete [] fsFaceList[i];
	delete [] fsFaceList;

	for (int i = 0; i < 12; ++i)
		delete [] fsFaceVertexNormalList[i];
	delete [] fsFaceVertexNormalList;

	delete [] fsEdgeLoop;
	delete [] fsEdgeLoop1;
	delete [] fsEdgeLoop2;
	delete [] fsEdgeLoop3;
	delete [] fsEdgeLoop4;
	delete [] fsEdgeLoop5;
	delete [] fsEdgeFrustumLoop1;
	delete [] fsEdgeFrustumLoop2;
	delete [] fsEdgeFrustumLoop3;
	delete [] fsEdgeFrustumLoop4;
}

void stereoSafePlane::postConstructor() 
{
}

MStatus stereoSafePlane::compute( const MPlug& plug, MDataBlock& data)
{ 
	MStatus stat;

	if( plug != aInterocular ){
		return MS::kUnknownParameter; 
	}

	//MObject thisNode = thisMObject();
	//MFnDagNode fnDagNode(thisNode);
	//MFnTransform fnParentTransform(fnDagNode.parent(0));
	//MStatus stat2;
	//MVector translate = fnParentTransform.getTranslation( MSpace::kTransform , &stat2 );
	//if( stat2 == MStatus::kSuccess ){
		struct stereoParam myData;

		MDataHandle translateH = data.inputValue( aTranslateZ, &stat );
		PERRORfail( stat, "compute getting translateZ attr" );
		myData.x = -translateH.asFloat();

		MDataHandle zeroParallaxH = data.inputValue( aZeroParallax, &stat );
		PERRORfail( stat, "compute getting zeroParallax attr" );
		myData.convergence = zeroParallaxH.asFloat();

		MDataHandle percentageH = data.inputValue( aPercentage, &stat );
		PERRORfail( stat, "comput getting percentage attr" );
		myData.percent = percentageH.asFloat();
		myData.percent = myData.percent/100;
		//printf("percent: %f\n", myData.percent );

		MDataHandle focalLengthH = data.inputValue( aFocalLength, &stat );
		PERRORfail( stat, "compute getting focalLength attr" );
		myData.focal = focalLengthH.asFloat();
		//printf("focal: %f\n", myData.focal );

		MDataHandle filmHandle = data.inputValue( aFilmAperture, &stat );
		PERRORfail( stat, "compute getting filmAperture attr");
		float *film = filmHandle.asFloat2();
		myData.film[0] = film[0];
		myData.film[1] = film[1];
		//printf("film1: %f\n", myData.film[0] );
		//printf("film2: %f\n", myData.film[1] );

		MDataHandle greenHandle = data.inputValue( aGreenPosition, &stat );
		PERRORfail( stat, "compute getting greenPosition attr");
		myData.green = greenHandle.asFloat();

		MDataHandle redHandle = data.inputValue( aRedPosition, &stat );
		PERRORfail( stat, "compute getting redPosition attr");
		myData.red = redHandle.asFloat();
		//printf("red: %f\n", myData.red );

		MDataHandle redWashHandle = data.inputValue( aRedWashPosition, &stat );
		PERRORfail( stat, "compute getting redWashPosition attr");
		myData.redWash = redWashHandle.asFloat();

		MDataHandle yellowWashHandle = data.inputValue( aYellowWashPosition, &stat );
		PERRORfail( stat, "compute getting yellowWashPosition attr");
		myData.yellowWash = yellowWashHandle.asFloat();

		MDataHandle yellowHandle = data.inputValue( aYellowPosition, &stat );
		PERRORfail( stat, "compute getting yellowPosition attr");
		myData.yellow = yellowHandle.asFloat();

		MDataHandle visionHandle = data.inputValue( aVisionField, &stat );
		PERRORfail( stat, "compute getting vision field attr");
		myData.visionField = visionHandle.asFloat();

		MDataHandle circleHandle = data.inputValue( aCircle, &stat );
		PERRORfail( stat, "compute getting circle attr");
		myData.circle = circleHandle.asFloat();

		getCoreData( &myData );

		MDataHandle outInterocularHandle = data.outputValue( aInterocular );
		outInterocularHandle.set( float(myData.interocular) );
		outInterocularHandle.setClean();

		MDataHandle outFurtherPosHandle = data.outputValue( aFurtherPosition );
		outFurtherPosHandle.set( float(myData.further_pos) );
		outFurtherPosHandle.setClean();

		MDataHandle outFarPosHandle = data.outputValue( aFarPosition );
		outFarPosHandle.set( float(myData.x) );
		outFarPosHandle.setClean();

		MDataHandle outNearPosHandle = data.outputValue( aNearPosition );
		outNearPosHandle.set( float(myData.near_pos) );
		outNearPosHandle.setClean();

		MDataHandle outNearerPosHandle = data.outputValue( aNearerPosition );
		outNearerPosHandle.set( float(myData.nearer_pos) );
		outNearerPosHandle.setClean();

		MDataHandle outCustomPosHandle = data.outputValue( aCustomPosition );
		outCustomPosHandle.set( float(myData.custom_pos) );
		outCustomPosHandle.setClean();

		MDataHandle outBestPosHandle = data.outputValue( aBestPosition );
		outBestPosHandle.set( float(myData.best_pos) );
		outBestPosHandle.setClean();
	//}

	return MS::kSuccess;
}

void stereoSafePlane::drawConvergenceLine( M3dView &view, M3dView::DisplayStatus status )
{
	glPushAttrib( GL_CURRENT_BIT ); 
	if ( status == M3dView::kActive || status == M3dView::kLead) {
		view.setDrawColor( 13, M3dView::kActiveColors );
	} else {
		view.setDrawColor( 14, M3dView::kDormantColors );
	}

	double cp = param.x - param.convergence;

	//convergence line
	glBegin( GL_LINE_STRIP );
	glVertex3d(fsVertexOcularLeft[0], fsVertexOcularLeft[1], fsVertexOcularLeft[2]);
	glVertex3d(0.0,0.0,cp);
	glEnd();

	glBegin( GL_LINE_STRIP );
	glVertex3d(fsVertexOcularRight[0], fsVertexOcularRight[1], fsVertexOcularRight[2]);
	glVertex3d(0.0,0.0,cp);
	glEnd();

	glPopAttrib();
}

void stereoSafePlane::drawFrustumLine( M3dView &view, M3dView::DisplayStatus status )
{
	glPushAttrib( GL_CURRENT_BIT ); 
	if ( status == M3dView::kActive || status == M3dView::kLead) {
		view.setDrawColor( 13, M3dView::kActiveColors );
	} else {
		view.setDrawColor( 14, M3dView::kDormantColors );
	}

	unsigned int i; 

	//Frustum
	int start = 0;
	if(fsVertexList[0][2]>=0) start = 1;	//don't draw line between red wash plane and red plane if the depth value greater than zero

	glBegin( GL_LINE_STRIP );
	for ( i = start; i < fsEdgeFrustumLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeFrustumLoop1[i]][0], 
					fsVertexList[fsEdgeFrustumLoop1[i]][1],
					fsVertexList[fsEdgeFrustumLoop1[i]][2]);
	}
	glVertex3d(fsVertexOrg[0], fsVertexOrg[1], fsVertexOrg[2]);
	glEnd();

	glBegin( GL_LINE_STRIP ); 
	for ( i = start; i < fsEdgeFrustumLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeFrustumLoop2[i]][0], 
					fsVertexList[fsEdgeFrustumLoop2[i]][1],
					fsVertexList[fsEdgeFrustumLoop2[i]][2]);
	}
	glVertex3d(fsVertexOrg[0], fsVertexOrg[1], fsVertexOrg[2]);
	glEnd();

	glBegin( GL_LINE_STRIP ); 
	for ( i = start; i < fsEdgeFrustumLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeFrustumLoop3[i]][0], 
					fsVertexList[fsEdgeFrustumLoop3[i]][1],
					fsVertexList[fsEdgeFrustumLoop3[i]][2]);
	}
	glVertex3d(fsVertexOrg[0], fsVertexOrg[1], fsVertexOrg[2]);
	glEnd();

	glBegin( GL_LINE_STRIP ); 
	for ( i = start; i < fsEdgeFrustumLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeFrustumLoop4[i]][0], 
					fsVertexList[fsEdgeFrustumLoop4[i]][1],
					fsVertexList[fsEdgeFrustumLoop4[i]][2]);
	}
	glVertex3d(fsVertexOrg[0], fsVertexOrg[1], fsVertexOrg[2]);
	glEnd();

	glPopAttrib();
}

void stereoSafePlane::drawEdgeLoop( M3dView &view, M3dView::DisplayStatus status )
{
	glPushAttrib( GL_CURRENT_BIT );
	if ( status == M3dView::kActive || status == M3dView::kLead) {
		view.setDrawColor( 13, M3dView::kActiveColors );
	} else {
		view.setDrawColor( 14, M3dView::kDormantColors );
	}

	unsigned int i;

	//Edge of planes
	// red plane
	if( fsVertexList[0][2] < 0 ) {
		glBegin( GL_LINE_LOOP ); 
		for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
			glVertex3d( fsVertexList[fsEdgeLoop[i]][0], 
						fsVertexList[fsEdgeLoop[i]][1],
						fsVertexList[fsEdgeLoop[i]][2]);
		}
		glEnd();
	}

	// red wash plane
	glBegin( GL_LINE_LOOP ); 
	for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeLoop1[i]][0], 
					fsVertexList[fsEdgeLoop1[i]][1],
					fsVertexList[fsEdgeLoop1[i]][2]);
	}
	glEnd();

	// yellow wash plane
	glBegin( GL_LINE_LOOP ); 
	for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeLoop2[i]][0], 
					fsVertexList[fsEdgeLoop2[i]][1],
					fsVertexList[fsEdgeLoop2[i]][2]);
	}
	glEnd();

	// yellow plane
	glBegin( GL_LINE_LOOP ); 
	for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeLoop3[i]][0], 
					fsVertexList[fsEdgeLoop3[i]][1],
					fsVertexList[fsEdgeLoop3[i]][2]);
	}
	glEnd();

	// green plane
	if( fsVertexList[16][2] < param.x ){
		glBegin( GL_LINE_LOOP ); 
		for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
			glVertex3d( fsVertexList[fsEdgeLoop4[i]][0], 
						fsVertexList[fsEdgeLoop4[i]][1],
						fsVertexList[fsEdgeLoop4[i]][2]);
		}
		glEnd();
	}

	// cyan plane
	glBegin( GL_LINE_LOOP ); 
	for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeLoop5[i]][0], 
					fsVertexList[fsEdgeLoop5[i]][1],
					fsVertexList[fsEdgeLoop5[i]][2]);
	}
	glEnd();

	glPopAttrib();
}

void stereoSafePlane::drawCircle( M3dView &view, M3dView::DisplayStatus status ){
	glPushAttrib( GL_CURRENT_BIT );
	//glPushAttrib( GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_ENABLE_BIT | GL_PIXEL_MODE_BIT ); 

	if ( status == M3dView::kActive || status == M3dView::kLead) {
		view.setDrawColor( 13, M3dView::kActiveColors );
	} else {
		view.setDrawColor( 14, M3dView::kDormantColors );
	}

	unsigned int num_segments = 360;

	double theta = 2 * M_PI / double(num_segments);
	double c = cos(theta);//precalculate the sine and cosine
	double s = sin(theta);
	double t;
	double r = param.circle * 0.1;

	double x = r;//we start at angle = 0 
	double y = 0.0;
	double z = param.x - param.circle_pos;
    
	glColor3f( 0.1f, 1, 1);	
	glBegin(GL_LINE_LOOP); 
	for(unsigned int ii = 0; ii < num_segments; ii++) 
	{ 
		glVertex3d(x, y, z);//output vertex 
        
		//apply the rotation matrix
		t = x;
		x = c * x - s * y;
		y = s * t + c * y;
	} 
	glEnd(); 

	glPopAttrib();
}

void stereoSafePlane::moveOutOfControl()
{
	fsVertexOrg[0] = 0.0;
	fsVertexOrg[1] = 0.0;
	fsVertexOrg[2] = 0.0;

	fsVertexOcularLeft[0] = 0.0;
	fsVertexOcularLeft[1] = 0.0;
	fsVertexOcularLeft[2] = 0.0;

	fsVertexOcularRight[0] = 0.0;
	fsVertexOcularRight[1] = 0.0;
	fsVertexOcularRight[2] = 0.0;

	for(int i=0; i<24; i++)
		fsVertexList[i][2] = 0.0;
	
	fsVertexList[0][0] = -0.5;		fsVertexList[0][1] = -0.5;
	fsVertexList[1][0] = 0.5;		fsVertexList[1][1] = -0.5;
	fsVertexList[2][0] = 0.5;		fsVertexList[2][1] = 0.5;
	fsVertexList[3][0] = -0.5;		fsVertexList[3][1] = 0.5;

	fsVertexList[4][0] = -0.5;		fsVertexList[4][1] = -0.5;
	fsVertexList[5][0] = 0.5;		fsVertexList[5][1] = -0.5;
	fsVertexList[6][0] = 0.5;		fsVertexList[6][1] = 0.5;
	fsVertexList[7][0] = -0.5;		fsVertexList[7][1] = 0.5;

	fsVertexList[8][0] = -0.5;		fsVertexList[8][1] = -0.5;
	fsVertexList[9][0] = 0.5;		fsVertexList[9][1] = -0.5;
	fsVertexList[10][0] = 0.5;		fsVertexList[10][1] = 0.5;
	fsVertexList[11][0] = -0.5;		fsVertexList[11][1] = 0.5;

	fsVertexList[12][0] = -0.5;		fsVertexList[12][1] = -0.5;
	fsVertexList[13][0] = 0.5;		fsVertexList[13][1] = -0.5;
	fsVertexList[14][0] = 0.5;		fsVertexList[14][1] = 0.5;
	fsVertexList[15][0] = -0.5;		fsVertexList[15][1] = 0.5;

	fsVertexList[16][0] = -0.5;		fsVertexList[16][1] = -0.5;
	fsVertexList[17][0] = 0.5;		fsVertexList[17][1] = -0.5;
	fsVertexList[18][0] = 0.5;		fsVertexList[18][1] = 0.5;
	fsVertexList[19][0] = -0.5;		fsVertexList[19][1] = 0.5;

	fsVertexList[20][0] = -0.5;		fsVertexList[20][1] = -0.5;
	fsVertexList[21][0] = 0.5;		fsVertexList[21][1] = -0.5;
	fsVertexList[22][0] = 0.5;		fsVertexList[22][1] = 0.5;
	fsVertexList[23][0] = -0.5;		fsVertexList[23][1] = 0.5;
}

void stereoSafePlane::moveAlongZ(double *red, double *yellowWash, double *yellow, double *green, double *cyan)
{
	//red plane
	int i;
	for(i=0; i<= 3; i++)
		fsVertexList[i][2] = -*red;

	//yellowWash plane
	for(i=8; i<=11; i++)
		fsVertexList[i][2] = -*yellowWash;

	//yellow plane
	for(i=12; i<=15; i++)
		fsVertexList[i][2] = -*yellow;

	//green plane
	for(i=16; i<=19; i++)
		fsVertexList[i][2] = -*green;

	//cyan plane
	for(i=20; i<=23; i++)
		fsVertexList[i][2] = -*cyan;
}

void stereoSafePlane::moveScale(double *red, double *redWash, double *yellowWash, double *yellow, double *green, double *cyan)
{
	fsVertexList[0][0] = -*red;			fsVertexList[0][1] = -*(red+1);
	fsVertexList[1][0] = *red;			fsVertexList[1][1] = -*(red+1);
	fsVertexList[2][0] = *red;			fsVertexList[2][1] = *(red+1);
	fsVertexList[3][0] = -*red;			fsVertexList[3][1] = *(red+1);

	fsVertexList[4][0] = -*redWash;		fsVertexList[4][1] = -*(redWash+1);
	fsVertexList[5][0] = *redWash;		fsVertexList[5][1] = -*(redWash+1);
	fsVertexList[6][0] = *redWash;		fsVertexList[6][1] = *(redWash+1);
	fsVertexList[7][0] = -*redWash;		fsVertexList[7][1] = *(redWash+1);

	fsVertexList[8][0] = -*yellowWash;	fsVertexList[8][1] = -*(yellowWash+1);
	fsVertexList[9][0] = *yellowWash;	fsVertexList[9][1] = -*(yellowWash+1);
	fsVertexList[10][0] = *yellowWash;	fsVertexList[10][1] = *(yellowWash+1);
	fsVertexList[11][0] = -*yellowWash;	fsVertexList[11][1] = *(yellowWash+1);

	fsVertexList[12][0] = -*yellow;		fsVertexList[12][1] = -*(yellow+1);
	fsVertexList[13][0] = *yellow;		fsVertexList[13][1] = -*(yellow+1);
	fsVertexList[14][0] = *yellow;		fsVertexList[14][1] = *(yellow+1);
	fsVertexList[15][0] = -*yellow;		fsVertexList[15][1] = *(yellow+1);

	fsVertexList[16][0] = -*green;		fsVertexList[16][1] = -*(green+1);
	fsVertexList[17][0] = *green;		fsVertexList[17][1] = -*(green+1);
	fsVertexList[18][0] = *green;		fsVertexList[18][1] = *(green+1);
	fsVertexList[19][0] = -*green;		fsVertexList[19][1] = *(green+1);

	fsVertexList[20][0] = -*cyan;		fsVertexList[20][1] = -*(cyan+1);
	fsVertexList[21][0] = *cyan;		fsVertexList[21][1] = -*(cyan+1);
	fsVertexList[22][0] = *cyan;		fsVertexList[22][1] = *(cyan+1);
	fsVertexList[23][0] = -*cyan;		fsVertexList[23][1] = *(cyan+1);
}

bool stereoSafePlane::getCoreData( struct stereoParam *input )
{
	if(input->focal > 0 && input->convergence < input->x && input->red > input->redWash && input->yellow < input->yellowWash ){
	//if(input->focal > 0 && input->convergence < input->x ){
		//double tan_half_angle_H = MAYA_CONSTANT * input->film[0] / input->focal;
		//double tan_half_angle_V = MAYA_CONSTANT * input->film[1] / input->focal;
		double tan_half_angle_H = 12.7 * input->film[0] / input->focal;
		double tan_half_angle_V = 12.7 * input->film[1] / input->focal;
		input->tan_fov[0] = tan_half_angle_H;
		input->tan_fov[1] = tan_half_angle_V;
		double screen_width_half = tan_half_angle_H * input->convergence;
		
		double ocular = 2 * input->redWash * input->percent * screen_width_half * input->x / fabs( input->x - input->convergence );
		input->interocular = ocular;

		double factor1 = ocular * input->convergence;
		double factor2 = 2 * screen_width_half;

		double red_pos =  ocular - input->red * input->percent * factor2;
		if(red_pos != 0){
			input->further_pos = factor1 / red_pos;
		}

		double yellowW_pos = ocular - input->yellowWash * input->percent * factor2;
		if(yellowW_pos != 0){
			input->near_pos = factor1 / yellowW_pos;
		}

		double yellow_pos = ocular - input->yellow * input->percent * factor2;
		if(yellow_pos != 0){
			input->nearer_pos = factor1 / yellow_pos;
		}

		double green_pos = ocular - input->green * input->percent * factor2;
		if(green_pos != 0){
			input->custom_pos = factor1 / green_pos;
		}else input->custom_pos = 0;

		//then we compute the ideal location for orthostereoscopic
		
		double viewing_half_angle = tan(input->visionField*0.5*M_PI/180.0);
		double best_distance = screen_width_half / viewing_half_angle;		// the recomanded viewing angle is 50 degree according to THX
		double human_ocular = 2 * screen_width_half * input->percent;
		factor1 = human_ocular * best_distance;
		double cyan_pos = human_ocular - input->green * input->percent * factor2;
		if(cyan_pos != 0){
			input->best_pos = input->convergence - best_distance + factor1 / cyan_pos;
		}else input->best_pos = 0;

		// compute the circle position in real unit
		input->circle_pos = input->circle * 0.5 / tan_half_angle_H;

	}else {
		return false;
	}

	return true;
}

double stereoSafePlane::moveVertexList()
{
	// the basic idea is to make redWash plane and zero plane movable with returned corresponding interocular distance 
	double ocular = 0;

	if( getCoreData(&param) ){
		
		ocular = param.interocular;

		double red_pos;
		if( param.further_pos != 0 ){
			red_pos = param.further_pos - param.x;
		} else red_pos = -param.x - 2;

		double yellowW_pos;
		if( param.near_pos != 0){
			yellowW_pos = param.near_pos - param.x;
		} else yellowW_pos = -param.x - 1.5;

		double yellow_pos;
		if( param.nearer_pos != 0){
			yellow_pos = param.nearer_pos - param.x;
		}else yellow_pos = -param.x - 1;

		double green_pos;
		if( param.custom_pos != 0 ){
			green_pos = param.custom_pos - param.x;
		}else green_pos = -param.x - 3;

		double cyan_pos;
		if( param.best_pos != 0 ){
			cyan_pos = param.best_pos - param.x;
		}else cyan_pos = -param.x - 4;

		moveAlongZ(&red_pos, &yellowW_pos, &yellow_pos, &green_pos, &cyan_pos);

		double tan_half_angle_H = param.tan_fov[0];
		double tan_half_angle_V = param.tan_fov[1];

		double red_scale[] = { fabs(param.x+red_pos) * tan_half_angle_H * param.size, fabs(param.x+red_pos) * tan_half_angle_V * param.size };
		double redW_scale[] = { fabs(param.x) * tan_half_angle_H * param.size, fabs(param.x) * tan_half_angle_V * param.size };
		double yellowW_scale[] = { fabs(param.x+yellowW_pos) * tan_half_angle_H * param.size, fabs(param.x+yellowW_pos) * tan_half_angle_V * param.size };
		double yellow_scale[] = { fabs(param.x+yellow_pos) * tan_half_angle_H * param.size, fabs(param.x+yellow_pos) * tan_half_angle_V * param.size };
		double green_scale[] = { fabs(param.x+green_pos) * tan_half_angle_H * param.size, fabs(param.x+green_pos) * tan_half_angle_V * param.size };
		double cyan_scale[] = { fabs(param.x+cyan_pos) * tan_half_angle_H * param.size, fabs(param.x+cyan_pos) * tan_half_angle_V * param.size };

		moveScale(red_scale, redW_scale, yellowW_scale, yellow_scale, green_scale, cyan_scale);

		//set origin vertex
		fsVertexOrg[2] = param.x;

		//set ocular vertex
		fsVertexOcularLeft[2] = param.x;
		fsVertexOcularRight[2] = param.x;
		fsVertexOcularLeft[0] = -ocular/2;
		fsVertexOcularRight[0] = -fsVertexOcularLeft[0];
	}else {
		moveOutOfControl();	
	}

	return ocular;
}

void stereoSafePlane::printInfo( )
{
	printf("convergence: %f\n", param.convergence);
	printf("film H: %f\n", param.film[0]);
	printf("film V: %f\n", param.film[1]);
	printf("focal: %f\n", param.focal);
	printf("percent: %f\n", param.percent);
	printf("x: %f\n", param.x);
}

void stereoSafePlane::draw( M3dView & view, const MDagPath & /*path*/, 
							 M3dView::DisplayStyle style,
							 M3dView::DisplayStatus status )
{ 

	// Get the size
	MObject thisNode = thisMObject();
	MPlug tPlug =		MPlug( thisNode, aTransparency );
	MPlug drawFrustumPlug = MPlug( thisNode, aDrawFrustum );
	MPlug drawConvergencePlug = MPlug( thisNode, aDrawConvergenceLine );
	MPlug bHideNearPlug = MPlug( thisNode, aHideNearPlane );
	MPlug bHideNearerPlug = MPlug( thisNode, aHideNearerPlane );
	MPlug bHideFarPlug = MPlug( thisNode, aHideFarPlane );
	MPlug bHideFurtherPlug = MPlug( thisNode, aHideFurtherPlane );
	MPlug bHideCustomPlug = MPlug( thisNode, aHideCustomPlane );
	MPlug bHideCyanPlug = MPlug( thisNode, aHideCyanPlane );
	MPlug bHideCirclePlug = MPlug( thisNode, aHideCircle );

	float a;
	tPlug.getValue( a );
	bool bDrawFrustum, bDrawConvergence, bHideNear, bHideNearer, bHideFar, bHideFurther, bHideCustom, bHideCyan, bHideCircle;
	drawFrustumPlug.getValue( bDrawFrustum );
	drawConvergencePlug.getValue( bDrawConvergence );
	bHideNearPlug.getValue( bHideNear );
	bHideNearerPlug.getValue( bHideNearer );
	bHideFarPlug.getValue( bHideFar );
	bHideFurtherPlug.getValue( bHideFurther );
	bHideCustomPlug.getValue( bHideCustom );
	bHideCyanPlug.getValue( bHideCyan );
	bHideCirclePlug.getValue( bHideCircle );

	//get parent transform
	//MFnDagNode fnDagNode(thisNode);
	//MFnTransform fnParentTransform(fnDagNode.parent(0));
	//MStatus stat;
	//MVector translate = fnParentTransform.getTranslation( MSpace::kTransform , &stat );
	//if( stat == MStatus::kSuccess ){
		MPlug translatePlug =	MPlug( thisNode, aTranslateZ );
		MPlug zeroPlug =	MPlug( thisNode, aZeroParallax );
		MPlug percentPlug = MPlug( thisNode, aPercentage );
		MPlug focalPlug =	MPlug( thisNode, aFocalLength );
		MPlug filmPlug =	MPlug( thisNode, aFilmAperture );	//filmPlug is a compound plug
		MPlug greenPlug =	MPlug( thisNode, aGreenPosition );
		MPlug redPlug =		MPlug( thisNode, aRedPosition );
		MPlug redWPlug =	MPlug( thisNode, aRedWashPosition );
		MPlug yellowWPlug = MPlug( thisNode, aYellowWashPosition );
		MPlug yellowPlug =	MPlug( thisNode, aYellowPosition );
		MPlug sizePlug	=	MPlug( thisNode, aSize );
		MPlug visionPlug =  MPlug( thisNode, aVisionField );
		MPlug circlePlug = MPlug( thisNode, aCircle );

		//param.x = -translate.z;
		translatePlug.getValue( param.x );
		param.x = -param.x;
		zeroPlug.getValue( param.convergence );
		percentPlug.getValue( param.percent );
		param.percent = param.percent / 100.0;
		focalPlug.getValue( param.focal );
		if( filmPlug.numChildren() == 2 ){
			MPlug filmH = filmPlug.child(0);
			MPlug filmV = filmPlug.child(1);
			filmH.getValue( param.film[0] );
			filmV.getValue( param.film[1] );
		}
		greenPlug.getValue( param.green );
		redPlug.getValue( param.red );
		redWPlug.getValue( param.redWash );
		yellowWPlug.getValue( param.yellowWash );
		yellowPlug.getValue( param.yellow );
		sizePlug.getValue( param.size );
		visionPlug.getValue( param.visionField );
		circlePlug.getValue( param.circle );

		//printInfo();
		moveVertexList();
	//}

	//draw
	view.beginGL(); 

	if( (style == M3dView::kFlatShaded) ||
	    (style == M3dView::kGouraudShaded) ) {
		// Push the color settings
		glPushAttrib( GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_ENABLE_BIT | 
					  GL_PIXEL_MODE_BIT ); 
	
		if ( a < 1.0f ) { 
			glEnable( GL_BLEND );
			glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
		}

		unsigned int *vid = NULL;
		unsigned int *nid = NULL;
		unsigned int i = 0;
		unsigned int j = 0;
		
		if( fsVertexList[0][2] < 0 && !bHideFurther ) {	// only draw red plane when its' depth less than zero
			glColor4f( 1.0f, 0.1f, 0.1f, a );	
			glBegin( GL_TRIANGLES ); 
			for ( i = 0; i < 2; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i]; 
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		if( !bHideFar ) {
			glColor4f( 1, 0.5, 0.5, a );			
			glBegin( GL_TRIANGLES ); 
			for ( i = 2 ; i < 4; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i];
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		if( !bHideNear ) {
			glColor4f( 1, 1, 0.5, a );	
			glBegin( GL_TRIANGLES ); 
			for ( i = 4 ; i < 6; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i]; 
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		if( !bHideNearer ) {
			glColor4f( 1.0f, 1.0f, 0.1f, a );		
			glBegin( GL_TRIANGLES ); 
			for ( i = 6 ; i < 8; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i]; 
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0],
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		if( fsVertexList[16][2] < param.x && !bHideCustom ) {	// only draw green plane when its' depth less than translateZ
			glColor4f( 0.1f, 1, 0.1f, a );			
			glBegin( GL_TRIANGLES ); 
			for ( i = 8 ; i < 10; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i];
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		if( !bHideCyan ) {	// draw cyan plane
			glColor4f( 0.1f, 1, 1, a );			
			glBegin( GL_TRIANGLES ); 
			for ( i = 10 ; i < 12; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i];
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		glPopAttrib(); 

		if( !bHideCircle ){		// draw circle
			drawCircle( view, status );
		}
		drawEdgeLoop( view, status );
		if(bDrawFrustum) drawFrustumLine( view, status );
		if(bDrawConvergence) drawConvergenceLine( view, status );
	} else { 
		if( !bHideCircle ){		// draw circle
			drawCircle( view, status );
		}
		drawEdgeLoop( view, status );
		if(bDrawFrustum) drawFrustumLine( view, status );
		if(bDrawConvergence) drawConvergenceLine( view, status );
	}

	view.endGL(); 
}

bool stereoSafePlane::isTransparent( ) const
{
	MObject thisNode = thisMObject(); 
	MPlug plug( thisNode, aEnableTransparencySort ); 
	bool value; 
	plug.getValue( value ); 
	return value; 
}

bool stereoSafePlane::drawLast() const
{
    MObject thisNode = thisMObject();
    MPlug plug( thisNode, aEnableDrawLast );
    bool value;
    plug.getValue( value );
    return value;
}

bool stereoSafePlane::isBounded() const
{ 
	return false;
}

MBoundingBox stereoSafePlane::boundingBox() const
{   
	MBoundingBox bbox; 
	
	unsigned int i;
	for ( i = 0; i < fsVertexListSize; i ++ ) { 
		double *pt = fsVertexList[i]; 
		bbox.expand( MPoint( pt[0], pt[1], pt[2] ) ); 
	}
	return bbox; 
}

void* stereoSafePlane::creator()
{
	return new stereoSafePlane();
}

MStatus stereoSafePlane::initialize()
{ 
	MStatus stat;

	MFnNumericAttribute nAttr;
	
	// transparency
	aTransparency = nAttr.create( "transparency", "t", MFnNumericData::kFloat );
	nAttr.setDefault( 0.5 );
	nAttr.setMin( 0 );
	nAttr.setMax( 1 );
	nAttr.setKeyable( true );
	stat = addAttribute( aTransparency );
	PERRORfail( stat, "addAttribute transparency" );

	// transparencySort
	aEnableTransparencySort = nAttr.create( "transparencySort", "ts", MFnNumericData::kBoolean ); 
	nAttr.setDefault( true );   
	stat = addAttribute( aEnableTransparencySort );
	PERRORfail( stat, "addAttribute transparencySort" );

	// drawLast
    aEnableDrawLast = nAttr.create( "drawLast", "dL", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	stat = addAttribute( aEnableDrawLast );
	PERRORfail( stat, "addAttribute drawLast" );

	// zeroParallax
	aZeroParallax = nAttr.create( "zeroParallax", "zp", 
						  MFnNumericData::kFloat, 0.0001 );
	nAttr.setKeyable( true );
	stat = addAttribute( aZeroParallax );
	PERRORfail( stat, "addAttribute zeroParallax" );

	// translateZ
	aTranslateZ = nAttr.create( "translateZ", "tz", 
						  MFnNumericData::kFloat, 0 );
	stat = addAttribute( aTranslateZ );
	PERRORfail( stat, "addAttribute translateZ" );

	// percentage
	aPercentage = nAttr.create( "percentage", "p", 
						  MFnNumericData::kFloat, 0.7 );
	nAttr.setKeyable( true );
	stat = addAttribute( aPercentage );
	PERRORfail( stat, "addAttribute percentage" );

	// aRedPosition
	aRedPosition = nAttr.create( "redPosition", "rp", MFnNumericData::kFloat, 2 );
	nAttr.setMin( 0 );
	nAttr.setKeyable( true );
	stat = addAttribute( aRedPosition );
	PERRORfail( stat, "addAttribute redPosition" );

	// aRedWashPosition
	aRedWashPosition = nAttr.create( "redWashPosition", "lrp", MFnNumericData::kFloat, 1 );
	nAttr.setMin( 0 );
	nAttr.setKeyable( true );
	stat = addAttribute( aRedWashPosition );
	PERRORfail( stat, "addAttribute redWashPosition" );

	// aYellowWashPosition
	aYellowWashPosition = nAttr.create( "yellowWashPosition", "lyp", MFnNumericData::kFloat, -1 );
	nAttr.setMax( 0 );
	nAttr.setKeyable( true );
	stat = addAttribute( aYellowWashPosition );
	PERRORfail( stat, "addAttribute yellowWashPosition" );

	// aYellowPosition
	aYellowPosition = nAttr.create( "yellowPosition", "yp", MFnNumericData::kFloat, -2 );
	nAttr.setMax( 0 );
	nAttr.setKeyable( true );
	stat = addAttribute( aYellowPosition );
	PERRORfail( stat, "addAttribute yellowPosition" );

	// aGreenPosition
	aGreenPosition = nAttr.create( "greenPosition", "gp", MFnNumericData::kFloat, 0.5 );
	//nAttr.setMin( 0 );
	nAttr.setKeyable( true );
	stat = addAttribute( aGreenPosition );
	PERRORfail( stat, "addAttribute greenPosition" );

	//aSize
	aSize = nAttr.create( "size", "s", MFnNumericData::kFloat, 1);
	stat = addAttribute( aSize );
	nAttr.setKeyable( true );
	PERRORfail( stat, "addAttribute size" );

	// drawFrustum
    aDrawFrustum = nAttr.create( "drawFrustum", "dF", MFnNumericData::kBoolean );
    nAttr.setDefault( true );
	nAttr.setKeyable( true );
	stat = addAttribute( aDrawFrustum );
	PERRORfail( stat, "addAttribute drawFrustum" );

	// drawConvergenceLine
    aDrawConvergenceLine = nAttr.create( "drawConvergenceLine", "dCL", MFnNumericData::kBoolean );
    nAttr.setDefault( true );
	nAttr.setKeyable( true );
	stat = addAttribute( aDrawConvergenceLine );
	PERRORfail( stat, "addAttribute drawConvergenceLine" );

	// hide nearer plane
    aHideNearerPlane = nAttr.create( "hideNearerPlane", "hNerP", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideNearerPlane );
	PERRORfail( stat, "addAttribute hideNearerPlane" );

	// hide near plane
    aHideNearPlane = nAttr.create( "hideNearPlane", "hNP", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideNearPlane );
	PERRORfail( stat, "addAttribute hideNearPlane" );

	// hide far plane
    aHideFarPlane = nAttr.create( "hideFarPlane", "hFP", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideFarPlane );
	PERRORfail( stat, "addAttribute hideFarPlane" );

	// hide further plane
    aHideFurtherPlane = nAttr.create( "hideFurtherPlane", "hFurP", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideFurtherPlane );
	PERRORfail( stat, "addAttribute hideFurtherPlane" );

	// hide custom plane
    aHideCustomPlane = nAttr.create( "hideCustomPlane", "hCusP", MFnNumericData::kBoolean );
    nAttr.setDefault( true );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideCustomPlane );
	PERRORfail( stat, "addAttribute hideCustomPlane" );

	// focalLength
	aFocalLength = nAttr.create( "focalLength", "fl", 
						  MFnNumericData::kFloat, 35 );
	stat = addAttribute( aFocalLength );
	PERRORfail( stat, "addAttribute focalLength" );

	// filmAperture
	MObject filmAH = nAttr.create("horizontalFilmAperture", "hfa", MFnNumericData::kFloat, 1.417);
	MObject filmAV = nAttr.create("verticalFilmAperture", "vfa", MFnNumericData::kFloat, 0.945);
	aFilmAperture = nAttr.create( "filmAperture", "fa", filmAH, filmAV);
	stat = addAttribute( aFilmAperture );
	PERRORfail( stat, "addAttribute filmAperture" );

	//output interocular
	aInterocular = nAttr.create( "outInterocular", "oi", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aInterocular );
	PERRORfail( stat, "addAttribute outInterocular");

	//output further position
	aFurtherPosition = nAttr.create( "outFurtherPosition", "oFurP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aFurtherPosition );
	PERRORfail( stat, "addAttribute outFurtherPosition");

	//output far position
	aFarPosition = nAttr.create( "outFarPosition", "oFP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aFarPosition );
	PERRORfail( stat, "addAttribute outFarPosition");

	//output near position
	aNearPosition = nAttr.create( "outNearPosition", "oNP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aNearPosition );
	PERRORfail( stat, "addAttribute outNearPosition");

	//output nearer position
	aNearerPosition = nAttr.create( "outNearerPosition", "oNerP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aNearerPosition );
	PERRORfail( stat, "addAttribute outNearerPosition");

	//output custom position
	aCustomPosition = nAttr.create( "outCustomPosition", "oCusP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aCustomPosition );
	PERRORfail( stat, "addAttribute outCustomPosition");

	//output best position
	aBestPosition = nAttr.create( "outBestPosition", "oBstP", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	nAttr.setKeyable( false );
	stat = addAttribute( aBestPosition );
	PERRORfail( stat, "addAttribute outBestPosition");

	// hide cyan plane
	aHideCyanPlane = nAttr.create( "hideCyanPlane", "hCynP", MFnNumericData::kBoolean );
    nAttr.setDefault( true );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideCyanPlane );
	PERRORfail( stat, "addAttribute hideCyanPlane" );

	// vision field
	aVisionField = nAttr.create( "visionField", "vsn", MFnNumericData::kFloat, 50 );
	nAttr.setKeyable( true );
	stat = addAttribute( aVisionField );
	PERRORfail( stat, "addAttribute visionField" );

	// hide circle
	aHideCircle = nAttr.create( "hideCircle", "hCrcl", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHideCircle );
	PERRORfail( stat, "addAttribute hideCircle" );

	// circle value
	aCircle = nAttr.create( "circle", "crcl", MFnNumericData::kFloat, 900 );
	nAttr.setKeyable( true );
	stat = addAttribute( aCircle );
	PERRORfail( stat, "addAttribute circle" );


	attributeAffects(aZeroParallax, aInterocular);
	attributeAffects(aTranslateZ, aInterocular);
	attributeAffects(aPercentage, aInterocular);
	attributeAffects(aFocalLength, aInterocular);
	attributeAffects(aFilmAperture, aInterocular);
	attributeAffects(aRedWashPosition, aInterocular);
	attributeAffects(aGreenPosition, aInterocular);
	attributeAffects(aYellowWashPosition, aInterocular);
	attributeAffects(aYellowPosition, aInterocular);
	attributeAffects(aRedPosition, aInterocular);

	attributeAffects(aZeroParallax, aFurtherPosition);
	attributeAffects(aTranslateZ, aFurtherPosition);
	attributeAffects(aRedPosition, aFurtherPosition);
	attributeAffects(aRedWashPosition, aFurtherPosition);
	attributeAffects(aPercentage, aFurtherPosition);
	attributeAffects(aFocalLength, aFurtherPosition);
	attributeAffects(aFilmAperture, aFurtherPosition);

	attributeAffects(aZeroParallax, aFarPosition);
	attributeAffects(aTranslateZ, aFarPosition);
	//attributeAffects(aRedWashPosition, aFarPosition);
	//attributeAffects(aPercentage, aFarPosition);
	//attributeAffects(aFocalLength, aFarPosition);
	//attributeAffects(aFilmAperture, aFarPosition);

	attributeAffects(aZeroParallax, aNearPosition);
	attributeAffects(aTranslateZ, aNearPosition);
	attributeAffects(aYellowWashPosition, aNearPosition);
	attributeAffects(aRedWashPosition, aNearPosition);
	attributeAffects(aPercentage, aNearPosition);
	attributeAffects(aFocalLength, aNearPosition);
	attributeAffects(aFilmAperture, aNearPosition);

	attributeAffects(aZeroParallax, aNearerPosition);
	attributeAffects(aTranslateZ, aNearerPosition);
	attributeAffects(aYellowPosition, aNearerPosition);
	attributeAffects(aRedWashPosition, aNearerPosition);
	attributeAffects(aPercentage, aNearerPosition);
	attributeAffects(aFocalLength, aNearerPosition);
	attributeAffects(aFilmAperture, aNearerPosition);

	attributeAffects(aZeroParallax, aCustomPosition);
	attributeAffects(aTranslateZ, aCustomPosition);
	attributeAffects(aGreenPosition, aCustomPosition);
	attributeAffects(aRedWashPosition, aCustomPosition);
	attributeAffects(aPercentage, aCustomPosition);
	attributeAffects(aFocalLength, aCustomPosition);
	attributeAffects(aFilmAperture, aCustomPosition);

	attributeAffects(aZeroParallax, aBestPosition);
	attributeAffects(aGreenPosition, aBestPosition);
	attributeAffects(aRedWashPosition, aBestPosition);
	attributeAffects(aVisionField, aBestPosition);
	attributeAffects(aPercentage, aBestPosition);
	attributeAffects(aFocalLength, aBestPosition);
	attributeAffects(aFilmAperture, aBestPosition);

	return MS::kSuccess;
}


///////////////////////////////////////////
//	stereoConvergePlane                  //
///////////////////////////////////////////

class stereoConvergePlane : public MPxLocatorNode
{
	double **fsVertexList;
	unsigned int fsVertexListSize;
	double **fsNormalList;
	unsigned int **fsFaceList;
	unsigned int fsFaceListSize;
	unsigned int **fsFaceVertexNormalList;
	unsigned int *fsEdgeLoop;
	unsigned int fsEdgeLoopSize;
	struct stereoParam param;

public:
	stereoConvergePlane();
	virtual ~stereoConvergePlane(); 

	virtual void			postConstructor(); 
	
    virtual MStatus   		compute( const MPlug&, MDataBlock&);

	virtual void            draw( M3dView & view, const MDagPath & path, 
								  M3dView::DisplayStyle style,
								  M3dView::DisplayStatus status );

	virtual void			drawEdgeLoop( M3dView &, M3dView::DisplayStatus );
	
	virtual void			moveOutOfControl();
	virtual void			moveScale(double *);
	virtual void			moveVertexList();
	
	virtual bool            isBounded() const;
	virtual MBoundingBox    boundingBox() const; 
	virtual bool			isTransparent() const; 
	virtual bool			drawLast() const; 

	static  void *          creator();
	static  MStatus         initialize();

	//input
	static  MObject			aEnableTransparencySort; 
	static  MObject			aEnableDrawLast;
	static  MObject			aTransparency;
	static	MObject			aFocalLength;
	static	MObject			aFilmAperture;
	static	MObject			aSize;
	static	MObject			aHidePlane;
	static	MObject			aTranslateZ;

	//output
	static	MObject			aZeroParallax;
public: 
	static	MTypeId		id;

};

MTypeId stereoConvergePlane::id( 0x08192C );
MObject stereoConvergePlane::aEnableTransparencySort; 
MObject stereoConvergePlane::aEnableDrawLast;
MObject stereoConvergePlane::aTransparency;
MObject	stereoConvergePlane::aFocalLength;
MObject	stereoConvergePlane::aFilmAperture;
MObject	stereoConvergePlane::aSize;
MObject stereoConvergePlane::aHidePlane;
MObject	stereoConvergePlane::aTranslateZ;
MObject stereoConvergePlane::aZeroParallax;

stereoConvergePlane::stereoConvergePlane() {
	fsVertexList = new double* [4];
	for (int i = 0; i < 4; ++i)
		fsVertexList[i] = new double [3];

	fsVertexList[0][0] = -0.5;
	fsVertexList[0][1] = -0.5;
	fsVertexList[0][2] = 0;
	fsVertexList[1][0] = 0.5;
	fsVertexList[1][1] = -0.5;
	fsVertexList[1][2] = 0;
	fsVertexList[2][0] = 0.5;
	fsVertexList[2][1] = 0.5;
	fsVertexList[2][2] = 0;
	fsVertexList[3][0] = -0.5;
	fsVertexList[3][1] = 0.5;
	fsVertexList[3][2] = 0;
	fsVertexListSize = sizeof(fsVertexList)/sizeof(fsVertexList[0]);

	fsNormalList = new double* [4];
	for (int i = 0; i < 4; ++i)
		fsNormalList[i] = new double [3];
	for(int i=0; i<4; i++){
		fsNormalList[i][0] = 0;
		fsNormalList[i][1] = 0;
		fsNormalList[i][2] = 1;
	}
	
	fsFaceList = new unsigned int* [2];
	for (int i = 0; i < 2; ++i)
		fsFaceList[i] = new unsigned int [3];
	fsFaceList[0][0] = 1;
	fsFaceList[0][1] = 2;
	fsFaceList[0][2] = 4;
	fsFaceList[1][0] = 4;
	fsFaceList[1][1] = 2;
	fsFaceList[1][2] = 3;
	fsFaceListSize = sizeof(fsFaceList)/sizeof(fsFaceList[0]);

	fsFaceVertexNormalList = new unsigned int* [2];
	for (int i = 0; i < 2; ++i)
		fsFaceVertexNormalList[i] = new unsigned int [3];
	fsFaceVertexNormalList[0][0] = 1;
	fsFaceVertexNormalList[0][1] = 2;
	fsFaceVertexNormalList[0][2] = 4;
	fsFaceVertexNormalList[1][0] = 4;
	fsFaceVertexNormalList[1][1] = 2;
	fsFaceVertexNormalList[1][2] = 3;

	fsEdgeLoop = new unsigned int [4];
	fsEdgeLoop[0] = 0;
	fsEdgeLoop[1] = 3;
	fsEdgeLoop[2] = 2;
	fsEdgeLoop[3] = 1;
	fsEdgeLoopSize = 4;
}

stereoConvergePlane::~stereoConvergePlane() {
	for (int i = 0; i < 4; ++i)
		delete [] fsVertexList[i];
	delete [] fsVertexList;

	for (int i = 0; i < 4; ++i)
		delete [] fsNormalList[i];
	delete [] fsNormalList;

	for (int i = 0; i < 2; ++i)
		delete [] fsFaceList[i];
	delete [] fsFaceList;

	for (int i = 0; i < 2; ++i)
		delete [] fsFaceVertexNormalList[i];
	delete [] fsFaceVertexNormalList;

	delete [] fsEdgeLoop;
}

void stereoConvergePlane::postConstructor() 
{
}

MStatus stereoConvergePlane::compute( const MPlug& plug, MDataBlock& data)
{ 
	MStatus stat;

	if( plug != aZeroParallax ){
		return MS::kUnknownParameter; 
	}

	//MObject thisNode = thisMObject();
	//MFnDagNode fnDagNode(thisNode);
	//MFnTransform fnParentTransform(fnDagNode.parent(0));
	//MStatus stat2;
	//MVector translate = fnParentTransform.getTranslation( MSpace::kTransform , &stat2 );
	//if( stat2 == MStatus::kSuccess ){

		MDataHandle translateH = data.inputValue( aTranslateZ, &stat );
		PERRORfail( stat, "compute getting translateZ attr" );
		float z = -translateH.asFloat();

		MDataHandle outZeroParallaxHandle = data.outputValue( aZeroParallax );
		outZeroParallaxHandle.set( z );
		outZeroParallaxHandle.setClean();
	//}

	return MS::kSuccess;
}

void stereoConvergePlane::drawEdgeLoop( M3dView &view, M3dView::DisplayStatus status )
{
	glPushAttrib( GL_CURRENT_BIT ); 
	if ( status == M3dView::kActive || status == M3dView::kLead) {
		view.setDrawColor( 13, M3dView::kActiveColors );
	} else {
		view.setDrawColor( 14, M3dView::kDormantColors );
	}

	unsigned int i;

	//Edge of planes
	glBegin( GL_LINE_LOOP ); 
	for ( i = 0; i < fsEdgeLoopSize; i ++ ) { 
		glVertex3d( fsVertexList[fsEdgeLoop[i]][0], 
					fsVertexList[fsEdgeLoop[i]][1],
					fsVertexList[fsEdgeLoop[i]][2]);
	}
	glEnd();

	glPopAttrib();
}

void stereoConvergePlane::moveOutOfControl()
{
	for(int i=0; i<=3; i++)
		fsVertexList[i][2] = 0;
	
	fsVertexList[0][0] = -0.5;		fsVertexList[0][1] = -0.5;
	fsVertexList[1][0] = 0.5;		fsVertexList[1][1] = -0.5;
	fsVertexList[2][0] = 0.5;		fsVertexList[2][1] = 0.5;
	fsVertexList[3][0] = -0.5;		fsVertexList[3][1] = 0.5;
}

void stereoConvergePlane::moveScale(double *scale)
{
	fsVertexList[0][0] = -*scale;			fsVertexList[0][1] = -*(scale+1);
	fsVertexList[1][0] = *scale;			fsVertexList[1][1] = -*(scale+1);
	fsVertexList[2][0] = *scale;			fsVertexList[2][1] = *(scale+1);
	fsVertexList[3][0] = -*scale;			fsVertexList[3][1] = *(scale+1);
}


void stereoConvergePlane::moveVertexList()
{
	double scale[2];

	if(param.focal != 0){
		//double tan_half_angle_H = MAYA_CONSTANT * param.film[0] / param.focal;
		//double tan_half_angle_V = MAYA_CONSTANT * param.film[1] / param.focal;
		double tan_half_angle_H = 12.7 * param.film[0] / param.focal;
		double tan_half_angle_V = 12.7 * param.film[1] / param.focal;
		scale[0] = fabs(param.x) * tan_half_angle_H * param.size;
		scale[1] = fabs(param.x) * tan_half_angle_V * param.size;	
	}else{
		scale[0] = param.size*0.5;
		scale[1] = param.size*0.5;
	}

	moveScale(scale);
}

void stereoConvergePlane::draw( M3dView & view, const MDagPath & /*path*/, 
							 M3dView::DisplayStyle style,
							 M3dView::DisplayStatus status )
{ 

	// Get the size
	MObject thisNode = thisMObject();
	MPlug tPlug =		MPlug( thisNode, aTransparency );
	MPlug bHidePlanePlug = MPlug( thisNode, aHidePlane );

	float a;
	tPlug.getValue( a );
	bool bHidePlane;
	bHidePlanePlug.getValue( bHidePlane );

	//get parent transform
	//MFnDagNode fnDagNode(thisNode);
	//MFnTransform fnParentTransform(fnDagNode.parent(0));
	//MStatus stat;
	//MVector translate = fnParentTransform.getTranslation( MSpace::kTransform , &stat );
	//if( stat == MStatus::kSuccess ){
		MPlug focalPlug =	MPlug( thisNode, aFocalLength );
		MPlug filmPlug =	MPlug( thisNode, aFilmAperture );	//filmPlug is a compound plug
		MPlug sizePlug	=	MPlug( thisNode, aSize );
		MPlug translatePlug = MPlug( thisNode, aTranslateZ );

		focalPlug.getValue( param.focal );
		if( filmPlug.numChildren() == 2 ){
			MPlug filmH = filmPlug.child(0);
			MPlug filmV = filmPlug.child(1);
			filmH.getValue( param.film[0] );
			filmV.getValue( param.film[1] );
		}
		sizePlug.getValue( param.size );
		translatePlug.getValue( param.x );
		param.x = -param.x;

		moveVertexList();
	//}

	//draw
	view.beginGL(); 

	if( (style == M3dView::kFlatShaded) ||
	    (style == M3dView::kGouraudShaded) ) {
		// Push the color settings
		glPushAttrib( GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_ENABLE_BIT | 
					  GL_PIXEL_MODE_BIT ); 
	
		if ( a < 1.0f ) { 
			glEnable( GL_BLEND );
			glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
		}

		unsigned int *vid = NULL;
		unsigned int *nid = NULL;
		unsigned int i = 0;
		unsigned int j = 0;
		
		if( !bHidePlane ) {
			glColor4f( 0.1f, 0.1f, 1.0f, a );	
			glBegin( GL_TRIANGLES ); 
			for ( i = 0; i < 2; i ++ ) { 
				vid = fsFaceList[i];
				nid = fsFaceVertexNormalList[i]; 
				for ( j = 0; j < 3; j ++ ) { 
					glNormal3d( fsNormalList[nid[j]-1][0], 
								fsNormalList[nid[j]-1][1], 
								fsNormalList[nid[j]-1][2] );
					glVertex3d( fsVertexList[vid[j]-1][0], 
								fsVertexList[vid[j]-1][1],
								fsVertexList[vid[j]-1][2] ); 
				}
			}
			glEnd();
		}

		glPopAttrib(); 
		drawEdgeLoop( view, status );
	} else { 
		drawEdgeLoop( view, status );
	}

	view.endGL(); 
}

bool stereoConvergePlane::isTransparent( ) const
{
	MObject thisNode = thisMObject(); 
	MPlug plug( thisNode, aEnableTransparencySort ); 
	bool value; 
	plug.getValue( value ); 
	return value; 
}

bool stereoConvergePlane::drawLast() const
{
    MObject thisNode = thisMObject();
    MPlug plug( thisNode, aEnableDrawLast );
    bool value;
    plug.getValue( value );
    return value;
}

bool stereoConvergePlane::isBounded() const
{ 
	return false;
}

MBoundingBox stereoConvergePlane::boundingBox() const
{   
	MBoundingBox bbox; 
	
	unsigned int i;
	for ( i = 0; i < fsVertexListSize; i ++ ) { 
		double *pt = fsVertexList[i]; 
		bbox.expand( MPoint( pt[0], pt[1], pt[2] ) ); 
	}
	return bbox; 
}

void* stereoConvergePlane::creator()
{
	return new stereoConvergePlane();
}

MStatus stereoConvergePlane::initialize()
{ 
	MStatus stat;

	MFnNumericAttribute nAttr;
	
	// transparency
	aTransparency = nAttr.create( "transparency", "t", MFnNumericData::kFloat );
	nAttr.setDefault( 0.5 );
	nAttr.setMin( 0 );
	nAttr.setMax( 1 );
	nAttr.setKeyable( true );
	stat = addAttribute( aTransparency );
	PERRORfail( stat, "addAttribute transparency" );

	// transparencySort
	aEnableTransparencySort = nAttr.create( "transparencySort", "ts", MFnNumericData::kBoolean ); 
	nAttr.setDefault( true );   
	stat = addAttribute( aEnableTransparencySort );
	PERRORfail( stat, "addAttribute transparencySort" );

	// drawLast
    aEnableDrawLast = nAttr.create( "drawLast", "dL", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	stat = addAttribute( aEnableDrawLast );
	PERRORfail( stat, "addAttribute drawLast" );

	//aSize
	aSize = nAttr.create( "size", "s", MFnNumericData::kFloat, 1);
	stat = addAttribute( aSize );
	nAttr.setKeyable( true );
	PERRORfail( stat, "addAttribute size" );

	// hide plane
    aHidePlane = nAttr.create( "hidePlane", "hP", MFnNumericData::kBoolean );
    nAttr.setDefault( false );
	nAttr.setKeyable( true );
	stat = addAttribute( aHidePlane );
	PERRORfail( stat, "addAttribute hidePlane" );

	// focalLength
	aFocalLength = nAttr.create( "focalLength", "fl", 
						  MFnNumericData::kFloat, 35 );
	stat = addAttribute( aFocalLength );
	PERRORfail( stat, "addAttribute focalLength" );

	// filmAperture
	MObject filmAH = nAttr.create("horizontalFilmAperture", "hfa", MFnNumericData::kFloat, 1.417);
	MObject filmAV = nAttr.create("verticalFilmAperture", "vfa", MFnNumericData::kFloat, 0.945);
	aFilmAperture = nAttr.create( "filmAperture", "fa", filmAH, filmAV);
	stat = addAttribute( aFilmAperture );
	PERRORfail( stat, "addAttribute filmAperture" );

	// translateZ
	aTranslateZ = nAttr.create( "translateZ", "tz", 
						  MFnNumericData::kFloat, 0 );
	stat = addAttribute( aTranslateZ );
	PERRORfail( stat, "addAttribute translateZ" );

	//output 
	aZeroParallax = nAttr.create( "zeroParallax", "zp", MFnNumericData::kFloat, 0 );
	nAttr.setReadable( true );
	nAttr.setWritable( false );
	stat = addAttribute( aZeroParallax );
	PERRORfail( stat, "addAttribute zeroParallax");

	attributeAffects( aTranslateZ, aZeroParallax );

	return MS::kSuccess;
}


MStatus initializePlugin( MObject obj )
{ 
	MStatus   status;
	MFnPlugin plugin( obj, "CrystalCG", "6.0", "Any");

	status = plugin.registerNode( "stereoSafePlane", stereoSafePlane::id, 
						 &stereoSafePlane::creator, &stereoSafePlane::initialize,
						 MPxNode::kLocatorNode );
	if (!status) {
		status.perror("registerNode");
		return status;
	}

	status = plugin.registerNode( "stereoConvergePlane", stereoConvergePlane::id,
						&stereoConvergePlane::creator, &stereoConvergePlane::initialize,
						MPxNode::kLocatorNode );
	if (!status) {
		status.perror("registerNode");
		return status;
	}

	return status;
}

MStatus uninitializePlugin( MObject obj)
{
	MStatus   status;
	MFnPlugin plugin( obj );

	status = plugin.deregisterNode( stereoSafePlane::id );
	if (!status) {
		status.perror("deregisterNode");
		return status;
	}

	status = plugin.deregisterNode( stereoConvergePlane::id );
	if (!status) {
		status.perror("deregisterNode");
		return status;
	}

	return status;
}
