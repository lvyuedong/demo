
#include <math.h>
#include <maya/MFnPlugin.h>
#include <maya/MArgList.h>
#include <maya/MGlobal.h>
#include <maya/MPxCommand.h>
#include <maya/MString.h>
#include <maya/MStringArray.h>
#include <maya/MMatrix.h>
#include <maya/MSyntax.h>
#include <maya/MTypes.h>
#include <maya/MArgParser.h>
#include <maya/MArgDatabase.h>
#include <maya/MDagPath.h> 
#include <maya/MDagPathArray.h> 
#include <maya/MSelectionList.h>
#include <maya/MItSelectionList.h>
#include <maya/MDrawTraversal.h> 
#include <maya/MObject.h>
#include <maya/MFnDagNode.h>
#include <maya/MTime.h> 
#include <maya/MAnimControl.h>

#define kViewportWidth		"-vw"
#define kViewportWidthLong	"-viewportWidth"
#define kViewportHeight		"-vh"
#define kViewportHeightLong	"-viewportHeight"
#define kStartFrame			"-sf"
#define kStartFrameLong		"-startFrame"
#define kEndFrame			"-ef"
#define kEndFrameLong		"-endFrame"
#define kUseTimeSlider		"-uts"
#define kUseTimeSliderLong	"-useTimeSlider"
#define kInvert				"-i"			// invert selection
#define kInvertLong			"-invert"
#define kOrthoLeft			"-ol"
#define kOrthoLeftLong		"-orthoLeft"
#define kOrthoRight			"-or"
#define kOrthoRightLong		"-orthoRight"
#define kOrthoBottom		"-ob"
#define kOrthoBottomLong	"-orthoBottom"
#define kOrthoTop			"-ot"
#define kOrthoTopLong		"-orthoTop"
#define	kOrthoNear			"-on"
#define kOrthoNearLong		"-orthoNear"
#define kOrthoFar			"-of"
#define kOrthoFarLong		"-orthoFar"
#define kOrthoZ				"-oz"
#define kOrthoZLong			"-orthoZ"


class frustumSelection : public MPxCommand
{
public:
    static MSyntax createSyntax();

                 frustumSelection();
    virtual      ~frustumSelection();

	MStatus		 parseArgs( const MArgList& args );

	void		 traverseObjects( MSelectionList& list, MDagPathArray& cam);
	void		 traverseAll( MSelectionList& list );

    MStatus      doIt(const MArgList&);
    bool         isUndoable() const;

    static void* creator();

private:
	unsigned int		width;
	unsigned int		height;
	double				start_frame;
	double				end_frame;
	bool				isFrameSet;
	bool				use_time_slider;
	bool				invert;
	double				o_l;
	double				o_r;
	double				o_b;
	double				o_t;
	double				o_n;
	double				o_f;
	double				o_z;
};

void* frustumSelection::creator()
{
    return new frustumSelection();
}

frustumSelection::frustumSelection()
{
}


frustumSelection::~frustumSelection()
{
}

bool frustumSelection::isUndoable() const
{
    return true;
}


MSyntax frustumSelection::createSyntax()
{
    MSyntax   syntax;

	syntax.addFlag( kViewportWidth, kViewportWidthLong, MSyntax::kDouble );
	syntax.addFlag( kViewportHeight, kViewportHeightLong, MSyntax::kDouble );
	syntax.addFlag( kStartFrame, kStartFrameLong, MSyntax::kDouble );
	syntax.addFlag( kEndFrame, kEndFrameLong, MSyntax::kDouble );
	syntax.addFlag( kUseTimeSlider, kUseTimeSliderLong, MSyntax::kBoolean );
	syntax.addFlag( kInvert, kInvertLong, MSyntax::kBoolean );
	syntax.addFlag( kOrthoLeft, kOrthoLeftLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoRight, kOrthoRightLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoBottom, kOrthoBottomLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoTop, kOrthoTopLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoNear, kOrthoNearLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoFar, kOrthoFarLong, MSyntax::kDouble );
	syntax.addFlag( kOrthoZ, kOrthoZLong, MSyntax::kDouble );
    syntax.enableQuery(false);
    syntax.enableEdit(false);

    return syntax;
}


MStatus frustumSelection::parseArgs( const MArgList& args ){
	MStatus         stat;
	MArgDatabase	argData(syntax(), args);

	if(argData.isFlagSet( kViewportWidth )){
		double tmp;
		stat = argData.getFlagArgument( kViewportWidth, 0, tmp );
		if(!stat){
			stat.perror("viewportWidth flag parsing failed");
			return stat;
		}
		width = (unsigned int)tmp;
	}else width = 2048;

	if(argData.isFlagSet( kViewportHeight )){
		double tmp;
		stat = argData.getFlagArgument( kViewportHeight, 0, tmp );
		if(!stat){
			stat.perror("viewportHeight flag parsing failed");
			return stat;
		}
		height = (unsigned int)tmp;
	}else height = 871;

	if(argData.isFlagSet( kStartFrame )){
		double tmp;
		stat = argData.getFlagArgument( kStartFrame, 0, tmp );
		if(!stat){
			stat.perror("startFrame flag parsing failed");
			return stat;
		}
		start_frame = tmp;
		isFrameSet = true;
	}else isFrameSet = false;

	if(argData.isFlagSet( kEndFrame )){
		double tmp;
		stat = argData.getFlagArgument( kEndFrame, 0, tmp );
		if(!stat){
			stat.perror("endFrame flag parsing failed");
			return stat;
		}
		end_frame = tmp;
		isFrameSet = true;
	}else isFrameSet = false;

	if(argData.isFlagSet( kUseTimeSlider )){
		bool tmp;
		stat = argData.getFlagArgument( kUseTimeSlider, 0, tmp );
		if(!stat){
			stat.perror("useTimeSlider flag parsing failed");
			return stat;
		}
		use_time_slider = tmp;
	}else use_time_slider = false;

	if( use_time_slider ) isFrameSet = false;

	if(isFrameSet){
		if( start_frame>=end_frame ) isFrameSet = false;
	}

	if(argData.isFlagSet( kInvert )){
		bool tmp;
		stat = argData.getFlagArgument( kInvert, 0, tmp );
		if(!stat){
			stat.perror("invert flag parsing failed");
			return stat;
		}
		invert = tmp;
	}else invert = false;

	if(argData.isFlagSet( kOrthoLeft )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoLeft, 0, tmp );
		if(!stat){
			stat.perror("orthoLeft flag parsing failed");
			return stat;
		}
		o_l = tmp;
	}else o_l = -99999999;

	if(argData.isFlagSet( kOrthoRight )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoRight, 0, tmp );
		if(!stat){
			stat.perror("orthoRight flag parsing failed");
			return stat;
		}
		o_r = tmp;
	}else o_r = 99999999;

	if(argData.isFlagSet( kOrthoBottom )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoBottom, 0, tmp );
		if(!stat){
			stat.perror("orthoBottom flag parsing failed");
			return stat;
		}
		o_b = tmp;
	}else o_b = -99999999;

	if(argData.isFlagSet( kOrthoTop )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoTop, 0, tmp );
		if(!stat){
			stat.perror("orthoTop flag parsing failed");
			return stat;
		}
		o_t = tmp;
	}else o_t = 99999999;

	if(argData.isFlagSet( kOrthoNear )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoNear, 0, tmp );
		if(!stat){
			stat.perror("orthoNear flag parsing failed");
			return stat;
		}
		o_n = tmp;
	}else o_n = -99999999;

	if(argData.isFlagSet( kOrthoFar )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoFar, 0, tmp );
		if(!stat){
			stat.perror("orthoFar flag parsing failed");
			return stat;
		}
		o_f = tmp;
	}else o_f = 99999999;

	if(argData.isFlagSet( kOrthoZ )){
		double tmp;
		stat = argData.getFlagArgument( kOrthoZ, 0, tmp );
		if(!stat){
			stat.perror("orthoZ flag parsing failed");
			return stat;
		}
		o_z = tmp;
	}else o_z = 0;
    
	return MS::kSuccess;
}

void frustumSelection::traverseObjects( MSelectionList& list, MDagPathArray& cam)
{
	unsigned int cam_i;
	unsigned int cam_num = cam.length();
	for( cam_i=0; cam_i<cam_num; cam_i++ ){
		MDrawTraversal *trav = new MDrawTraversal;
		trav->enableFiltering( false );
		if(!trav){
			MGlobal::displayWarning("frustumSelection : failed to create a traversal class !\n");
			continue;
		}
		trav->setFrustum( cam[cam_i], width, height );

		if(!trav->frustumValid()){
			MGlobal::displayWarning("frustumSelection : Frustum is invalid !\n");
			continue;
		}

		trav->traverse();
		
		unsigned int numItems = trav->numberOfItems();
		unsigned int i;
		for (i=0; i<numItems; i++)
		{
			MDagPath path;
			trav->itemPath(i, path);
			if( path.isValid() && (path.hasFn(MFn::kMesh) || path.hasFn(MFn::kNurbsSurface) || path.hasFn(MFn::kSubdiv) || path.hasFn(MFn::kPluginShape)) ){
				list.add( path.transform() );
			}
		}
		if(trav) delete trav;
	}
}

void frustumSelection::traverseAll( MSelectionList& list )
{
	MDrawTraversal *trav = new MDrawTraversal;
	trav->enableFiltering( false );
	if(!trav){
		MGlobal::displayWarning("frustumSelection : failed to create a traversal class !\n");
		return;
	}

	MMatrix worldXform;
	worldXform.setToIdentity();
	worldXform.matrix[3][2] = o_z;
	trav->setOrthoFrustum( o_l, o_r, o_b, o_t, o_n, o_f, worldXform);

	if(!trav->frustumValid()){
		MGlobal::displayWarning("frustumSelection : Ortho Frustum is invalid !\n");
		return;
	}

	trav->traverse();
	
	unsigned int numItems = trav->numberOfItems();
	unsigned int i;
	for (i=0; i<numItems; i++)
	{
		MDagPath path;
		trav->itemPath(i, path);
		if( path.isValid() && (path.hasFn(MFn::kMesh) || path.hasFn(MFn::kNurbsSurface) || path.hasFn(MFn::kSubdiv) || path.hasFn(MFn::kPluginShape)) ){
			list.add( path.transform() );
		}
	}
	if(trav) delete trav;
}

MStatus frustumSelection::doIt(const MArgList& args)
{
	MStatus status = parseArgs( args );
	if(MS::kSuccess != status) return status;

	MSelectionList activeList;
	MGlobal::getActiveSelectionList( activeList );
	MItSelectionList iter( activeList, MFn::kCamera );

	MDagPathArray cameras;
	for ( ; !iter.isDone(); iter.next() )
    {
        MDagPath camera;
        iter.getDagPath( camera );
		cameras.append( camera );
	}

	if(cameras.length()<=0){
		MGlobal::displayWarning("frustumSelection : select camera(s) please !\n");
		return MS::kFailure;
	}

	MSelectionList	collection;
	
	MTime current_time = MAnimControl::currentTime();

	if( use_time_slider ){
		double startT = MAnimControl::minTime().value();
		double endT = MAnimControl::maxTime().value();
		double t;
		for( t=startT; t<=endT; t++ ){
			MAnimControl::setCurrentTime( MTime(t) );
			traverseObjects( collection, cameras );
		}
		MAnimControl::setCurrentTime( current_time );
	}else if(isFrameSet){
		double t;
		for( t=start_frame; t<=end_frame; t++ ){
			MAnimControl::setCurrentTime( MTime(t) );
			traverseObjects( collection, cameras );
		}
		MAnimControl::setCurrentTime( current_time );
	}else traverseObjects( collection, cameras );

	MSelectionList	allGeometry;

	if( invert ){
		traverseAll( allGeometry );
		allGeometry.merge( collection, MSelectionList::kRemoveFromList );
	}else allGeometry = collection;

	MStringArray foundObj;

	unsigned int sel_i;
	unsigned int sel_num = allGeometry.length();
	for( sel_i=0; sel_i<sel_num; sel_i++ ){
		MObject item;
		allGeometry.getDependNode( sel_i, item );
		MFnDagNode dagFn( item );
		foundObj.append( dagFn.partialPathName() );
	}
	
	clearResult();
	setResult( foundObj );

	return MS::kSuccess;
}

MStatus initializePlugin(MObject obj)
{ 
    MStatus   status;
    MFnPlugin plugin(obj, "Alex Lv", "1.0", "Any");

    status = plugin.registerCommand(
                "frustumSelection",
                frustumSelection::creator,
                frustumSelection::createSyntax
            );

    if (!status) 
    {
        status.perror("registering frustumSelection command");
        return status;
    }

    return status;
}


MStatus uninitializePlugin(MObject obj)
{
    MStatus   status;
    MFnPlugin plugin(obj);

    status = plugin.deregisterCommand("frustumSelection");

    if (!status)
    {
        status.perror("deregistering frustumSelection command");
        return status;
    }

    return status;
}