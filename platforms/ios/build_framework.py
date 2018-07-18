#!/usr/bin/env python
"""
The script builds OpenCV.framework for iOS.
The built framework is universal, it can be used to build app and run it on either iOS simulator or real device.

Usage:
    ./build_framework.py <outputdir>

By cmake conventions (and especially if you work with OpenCV repository),
the output dir should not be a subdirectory of OpenCV source tree.

Script will create <outputdir>, if it's missing, and a few its subdirectories:

    <outputdir>
        build/
            iPhoneOS-*/
               [cmake-generated build tree for an iOS device target]
            iPhoneSimulator/
               [cmake-generated build tree for iOS simulator]
        opencv2.framework/
            [the framework content]

The script should handle minor OpenCV updates efficiently
- it does not recompile the library from scratch each time.
However, opencv2.framework directory is erased and recreated on each run.
"""

import glob, re, os, os.path, shutil, string, sys

def build_opencv(srcroot, buildroot, target, arch, cmake_options):
    "builds OpenCV for device or simulator"

    builddir = os.path.join(buildroot, target + '-' + arch)
    if not os.path.isdir(builddir):
        os.makedirs(builddir)
    currdir = os.getcwd()
    os.chdir(builddir)
    # for some reason, if you do not specify CMAKE_BUILD_TYPE, it puts libs to "RELEASE" rather than "Release"
    cmakeargs = ("-GXcode " +
                cmake_options +
                "-DCMAKE_BUILD_TYPE=Release " +
                "-DCMAKE_TOOLCHAIN_FILE=%s/platforms/ios/cmake/Toolchains/Toolchain-%s_Xcode.cmake " +
                "-DCMAKE_INSTALL_PREFIX=install") % (srcroot, target)
    # if cmake cache exists, just rerun cmake to update OpenCV.xproj if necessary
    if os.path.isfile(os.path.join(builddir, "CMakeCache.txt")):
        os.system("cmake %s ." % (cmakeargs,))
    else:
        os.system("cmake %s %s" % (cmakeargs, srcroot))

    for wlib in [builddir + "/modules/world/UninstalledProducts/libopencv_world.a",
                 builddir + "/lib/Release/libopencv_world.a"]:
        if os.path.isfile(wlib):
            os.remove(wlib)

    os.system("xcodebuild IPHONEOS_DEPLOYMENT_TARGET=6.0 -parallelizeTargets ARCHS=%s -jobs 8 -sdk %s -configuration Release -target ALL_BUILD" % (arch, target.lower()))
    os.system("xcodebuild IPHONEOS_DEPLOYMENT_TARGET=6.0 ARCHS=%s -sdk %s -configuration Release -target install install" % (arch, target.lower()))
    os.chdir(currdir)

def put_framework_together(srcroot, dstroot):
    "constructs the framework directory after all the targets are built"

    # find the list of targets (basically, ["iPhoneOS", "iPhoneSimulator"])
    targetlist = glob.glob(os.path.join(dstroot, "build", "*"))
    targetlist = [os.path.basename(t) for t in targetlist]

    # set the current dir to the dst root
    currdir = os.getcwd()
    framework_dir = dstroot + "/opencv2.framework"
    if os.path.isdir(framework_dir):
        shutil.rmtree(framework_dir)
    os.makedirs(framework_dir)
    os.chdir(framework_dir)

    # form the directory tree
    dstdir = "Versions/A"
    os.makedirs(dstdir + "/Resources")

    tdir0 = "../build/" + targetlist[0]
    # copy headers
    shutil.copytree(tdir0 + "/install/include/opencv2", dstdir + "/Headers")

    # make universal static lib
    wlist = " ".join(["../build/" + t + "/lib/Release/libopencv_world.a" for t in targetlist])
    os.system("lipo -create " + wlist + " -o " + dstdir + "/opencv2")

    # copy Info.plist
    shutil.copyfile(tdir0 + "/ios/Info.plist", dstdir + "/Resources/Info.plist")

    # make symbolic links
    os.symlink("A", "Versions/Current")
    os.symlink("Versions/Current/Headers", "Headers")
    os.symlink("Versions/Current/Resources", "Resources")
    os.symlink("Versions/Current/opencv2", "opencv2")


def build_framework(srcroot, dstroot, cmake_options):
    "main function to do all the work"

    targets = ["iPhoneOS", "iPhoneOS", "iPhoneOS", "iPhoneSimulator", "iPhoneSimulator"]
    archs = ["armv7", "armv7s", "arm64", "i386", "x86_64"]
    for i in range(len(targets)):
        build_opencv(srcroot, os.path.join(dstroot, "build"), targets[i], archs[i], cmake_options)

    put_framework_together(srcroot, dstroot)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage:\n\t./build_framework.py <outputdir> <path_to_eigen_third_party>\n\n"
        sys.exit(0)

    cmake_options = (
        "-DBUILD_opencv_world=ON " +
        "-DAPPLE_FRAMEWORK=ON " +
        "-DBUILD_EXAMPLES=NO " +
        "-DBUILD_TESTS=NO " +
        "-DBUILD_NEW_PYTHON_SUPPORT=NO " +
        "-DBUILD_PERF_TESTS=NO " +
        "-DBUILD_SHARED_LIBS=NO " +
        "-DBUILD_JPEG=NO " +
        "-DBUILD_OPENEXR=NO " +
        "-DBUILD_PNG=NO " +
        "-DBUILD_TIFF=NO " +
        "-DBUILD_JASPER=NO " +
        "-DBUILD_TBB=NO " +
        "-DBUILD_opencv_gpu=NO " +
        "-DBUILD_opencv_java=NO " +
        "-DBUILD_opencv_androidcamera=NO " +
        "-DWITH_OPENNI=OFF " +
        "-DWITH_OPENGL=OFF " +
        "-DWITH_IMAGEIO=ON " +
        "-DWITH_NVCUVID=OFF " +
        "-DWITH_CUFFT=OFF " +
        "-DWITH_CUBLAS=OFF " +
        "-DWITH_CUDA=OFF " +
        "-DWITH_HALIDE=OFF " +
        "-DWITH_OPENCL=OFF " +
        "-DWITH_OPENEXR=OFF " +
        "-DWITH_JPEG=OFF " +
        "-DWITH_PNG=OFF " +
        "-DWITH_CAROTENE=OFF " +
        "-DWITH_WEBP=OFF " +
        "-DWITH_TIFF=OFF " +
        "-DWITH_JASPER=OFF " +
        "-DWITH_IPP=OFF " +
        "-DWITH_ITT=OFF " +
        "-DWITH_TBB=OFF " +
        "-DWITH_EIGEN=YES " +
        "-DWITH_AVFOUNDATION=OFF " +
        "-DENABLE_DYNAMIC_CUDA=OFF " +
        "-DCUDA_HOST_COMPILATION_CPP=OFF " +
        "-DEIGEN_INCLUDE_PATH="+sys.argv[2] +" " +
        "-DCMAKE_C_FLAGS=\"-Wno-implicit-function-declaration -Wno-error -Wno-tautological-pointer-compare -Wno-tautological-compare -Wno-pointer-bool-conversion\"  " +
        "-DCMAKE_CXX_FLAGS=\"-fvisibility=hidden -fvisibility-inlines-hidden -Wno-error -Wno-tautological-pointer-compare -Wno-tautological-compare -Wno-pointer-bool-conversion -Os\"  " +
        "-DCMAKE_SHARED_LINKER_FLAGS=\"-Wl,--gc-sections\"  ")

    build_framework(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "../..")), os.path.abspath(sys.argv[1]), cmake_options)
