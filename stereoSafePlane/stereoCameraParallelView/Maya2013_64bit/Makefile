# Makefile for a Maya plugin.

##################################
# Platform specific build settings
##################################

ARCH          = $(shell uname -m)
C++           = g++
BUILDDIR      = Build/$(ARCH)

NO_TRANS_LINK =
CFLAGS        = -DLINUX -D_BOOL -DREQUIRE_IOSTREAM -DBits64_ -DLINUX_64 -fPIC

C++FLAGS      = $(CFLAGS) -Wno-deprecated -fno-gnu-keywords

LD            = $(C++) $(NO_TRANS_LINK) $(C++FLAGS) -Wl,-Bsymbolic -shared

INCLUDES      = -I. -I$(MAYA_LOCATION)/include -I/opt/X11/include
LIBS          = -L$(MAYA_LOCATION)/lib

debug: stereoCameraParallelView.o stereoCameraParallelView.so
opt: stereoCameraParallelView.o stereoCameraParallelView.so

debug: BUILDDIR = Build/$(ARCH)-debug
debug: CFLAGS += -g -gstabs+

opt: BUILDDIR = Build/$(ARCH)-opt
opt: CFLAGS += -O3

.cpp.o:
	-mkdir -p $(BUILDDIR)
	$(C++) -c $(INCLUDES) $(C++FLAGS) -o $(BUILDDIR)/$@ $<

plugins: \
    stereoCameraParallelView.so

clean:
	-rm -f Build/*/*.o

Clean:
	-rm -rf Build

##################
# Specific Rules #
##################
stereoCameraParallelView.o : stereoCameraParallelView.h stereoCameraParallelView.cpp
stereoCameraParallelViewCmd.o : stereoCameraParallelViewCmd.h stereoCameraParallelViewCmd.cpp
stereoCameraParallelViewMain.o : stereoCameraParallelView.h stereoCameraParallelViewCmd.h stereoCameraParallelViewMain.cpp

stereoCameraParallelView.so: stereoCameraParallelView.o stereoCameraParallelViewCmd.o stereoCameraParallelViewMain.o
	-@mkdir -p $(BUILDDIR)
	-@rm -f $@
	$(LD) -o $(BUILDDIR)/$@ $(BUILDDIR)/stereoCameraParallelView.o $(BUILDDIR)/stereoCameraParallelViewCmd.o $(BUILDDIR)/stereoCameraParallelViewMain.o $(LIBS) -lOpenMaya -lOpenMayaRender -lOpenMayaUI
	@echo ""
	@echo "###################################################"
	@echo successfully compiled $@ into $(BUILDDIR)
	@echo $(CURDIR)/$(BUILDDIR)/$@
	@echo ""

