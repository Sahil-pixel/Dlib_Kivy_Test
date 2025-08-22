# Author : Sk Sahil 
# https://github.com/Sahil-pixel
# Date : (22/Aug/2025)
from pythonforandroid.recipe import Recipe
import os, subprocess, shutil

class DlibPythonRecipe(Recipe):
    version = "master"
    url = "https://github.com/Sahil-pixel/dlib/archive/refs/heads/master.tar.gz"

    site_packages_name = "dlib"
    depends = ["python3", "numpy", "cmake","pybind11"]

    # pybind11 needed only at build time
    hostpython_prerequisites = ['pybind11']

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch)
        os.makedirs(build_dir, exist_ok=True)

        tar_dir = "dlib"
        dlib_dir = os.path.join(build_dir, tar_dir)
        install_dir = os.path.join(build_dir, "build")
        toolchain_file = os.path.join(self.ctx.ndk_dir, "build", "cmake", "android.toolchain.cmake")

        # ----------------------------
        # Step 1: build C++ core
        # ----------------------------
        cmake_args = [
            dlib_dir,
            f"-DCMAKE_INSTALL_PREFIX={install_dir}",
            "-DDLIB_NO_GUI_SUPPORT=ON",
            "-DDLIB_USE_CUDA=OFF",
            "-DDLIB_USE_BLAS=OFF",
            "-DDLIB_USE_LAPACK=OFF",
            "-DDLIB_USE_FFMPEG=OFF",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file}",
            f"-DANDROID_ABI={arch.arch}",
            f"-DANDROID_PLATFORM=android-{self.ctx.ndk_api}",
            "-DANDROID_STL=c++_shared",
        ]
        subprocess.check_call(["cmake"] + cmake_args, cwd=build_dir)
        subprocess.check_call(["cmake", "--build", ".", "--target", "install"], cwd=build_dir)

        #copying include 
        shutil.copytree(dlib_dir, os.path.join(install_dir, "include", "dlib"), dirs_exist_ok=True)
        
        # ----------------------------
        # Step 2: build Python bindings
        # ----------------------------
        python_dir = os.path.join(build_dir, "tools", "python")
        build_python_dir = os.path.join(python_dir, "build")
        os.makedirs(build_python_dir, exist_ok=True)

        python_recipe = self.get_recipe('python3', self.ctx)
        python_include = os.path.join(python_recipe.get_build_dir(arch.arch), "Include")
        python_lib_dir = python_recipe.link_root(arch.arch)
        python_link_version = self.ctx.python_recipe.link_version
        python_library = os.path.join(python_lib_dir, f"libpython{python_link_version}.so")

        # pybind11 include from hostpython site-packages
        hostpython_recipe = self.get_recipe('hostpython3', self.ctx)
        hostpython_build = hostpython_recipe.get_build_dir(arch.arch)

        hostpython_site_packages = os.path.join(hostpython_build,"native-build","Lib","site-packages")

        pybind11_inc = os.path.join(hostpython_site_packages, "pybind11", "include")


        env = super().get_recipe_env(arch)

        env["PYTHON_INCLUDE_DIR"] = python_include
        env["PYTHON_LIBRARY"] = python_library
        env["PYTHON_EXECUTABLE"] = self.ctx.hostpython
        env["PYBIND11_INCLUDE_DIR"] = pybind11_inc

        #env['CPPFLAGS'] = f'-I{python_include} -I{pybind11_inc}'
        #env['CXXFLAGS'] += f' -I{pybind11_inc}'
        #env['LDFLAGS'] = f'-L{python_lib_dir} -lpython3.11 -llog -landroid -ldl -lm'

        subprocess.check_call([
            "cmake",
            "-S", python_dir,
            "-B", build_python_dir,
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file}",
            "-DBUILD_SHARED_LIBS=ON",
            f"-DANDROID_ABI={arch.arch}",
            f"-DANDROID_PLATFORM=android-{self.ctx.ndk_api}",
            "-DPYBIND11_FINDPYTHON=OFF",
            f"-DPYTHON_EXECUTABLE={self.ctx.hostpython}",
            "-DCMAKE_SYSTEM_NAME=Android",
            f"-DPYTHON_INCLUDE_DIR={python_include}",
            f"-DPYTHON_LIBRARY={python_library}",
        ], env=env)

        subprocess.check_call([
            "cmake", "--build", build_python_dir, "--target", "_dlib_pybind11",
        ], env=env)

        # ----------------------------
        # Step 3: copy built .so
        # ----------------------------
        site_packages = self.ctx.get_python_install_dir(arch.arch)
        dlib_pkg_dir = os.path.join(site_packages, "dlib")
        os.makedirs(dlib_pkg_dir, exist_ok=True)

        for fname in os.listdir(build_python_dir):
            if fname.startswith(("dlib", "lib_dlib_pybind11")) and fname.endswith(".so"):
                shutil.copy(
                    os.path.join(build_python_dir, fname),
                    os.path.join(dlib_pkg_dir, "_dlib_pybind11.so")
                )
                break

        with open(os.path.join(dlib_pkg_dir, "__init__.py"), "w") as f:
            f.write("from ._dlib_pybind11 import *\n")
            f.write("from ._dlib_pybind11 import __version__, __time_compiled__\n")


recipe = DlibPythonRecipe()