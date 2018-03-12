# Makefile for a Maya plugin.

##################################
# Platform specific build settings
##################################

ARCH          = $(shell uname -m)
C++           = g++
BUILDDIR      = Build/$(ARCH)

CFLAGS = -DBits64_ -m64 -DUNIX -D_BOOL -DLINUX -DFUNCPROTO -D_GNU_SOURCE \
         -DLINUX_64 -fPIC \
         -fno-strict-aliasing -DREQUIRE_IOSTREAM -O3 -Wall \
         -Wno-multichar -Wno-comment -Wno-sign-compare -funsigned-char \
         -pthread

C++FLAGS = $(CFLAGS) $(WARNFLAGS) -Wno-deprecated -Wno-reorder \
		-ftemplate-depth-25 -fno-gnu-keywords

LFLAGS            = $(C++FLAGS) -Wl,-Bsymbolic -shared
LFLAGS 	+= -Wl,--version-script=./linux_plugin.map

LD            = $(C++)

INCLUDES      = -I. -I/mnt/public/home/lvyuedong/Documents/Projects/mayaAPI/frustumSelection/linux/2015_x64/include -I/usr/X11R6/include
LIBS          = -L/mnt/public/home/lvyuedong/Documents/Projects/mayaAPI/frustumSelection/linux/2015_x64/lib
EXT           = so

MDFLAGS = -Y

debug: frustumSelection.o frustumSelection.so
release: frustumSelection.o frustumSelection.so

debug: BUILDDIR = Build/$(ARCH)-debug
debug: CFLAGS += -g -gstabs+

release: BUILDDIR = Build/$(ARCH)-release
release: CFLAGS += -O3

.cpp.o:
	-mkdir -p $(BUILDDIR)
	$(C++) -c $(INCLUDES) $(C++FLAGS) -o $(BUILDDIR)/$@ $<

plugins: \
    frustumSelection.so

clean:
	-rm -f Build/*/*.o

Clean:
	-rm -rf Build

##################
# Specific Rules #
##################
frustumSelection.o : frustumSelection.h frustumSelection.cpp

frustumSelection.so: frustumSelection.o
	-@mkdir -p $(BUILDDIR)
	-@rm -f $@
	$(LD) $(LFLAGS) -o $(BUILDDIR)/$@ $(BUILDDIR)/frustumSelection.o $(LIBS) -lOpenMaya -lOpenMayaUI -lOpenMayaAnim -lFoundation
	@echo ""
	@echo "###################################################"
	@echo successfully compiled $@ into $(BUILDDIR)
	@echo $(CURDIR)/$(BUILDDIR)/$@
	@echo ""

