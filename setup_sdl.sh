#! /bin/bash
export OS_TYPE=QNX
export ARCH_TYPE=armv7
SRCPATH=$PWD
cd ../
mkdir build_sdl
cd build_sdl
cmake $SRCPATH -DCMAKE_TOOLCHAIN_FILE=$SRCPATH/qnx_6.5.0_linux_x86.cmake -DCMAKE_SYSTEM_NAME=QNX -G "Eclipse CDT4 - Unix Makefiles"
make && make install
