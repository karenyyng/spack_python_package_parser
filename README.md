# What this is :
simple script that crawls PyPI indices API for download info for a Python package 
* package tar.gz url
* md5 checksum object
* one line summary of what the package is 
* package homepage 

# example usage:

## grep download info for single package
```
$ ./crawl_pypi_index.py ipython@4.0.0
Detected single package name is supplied.
Querying http://pypi.python.org/pypi/ipython/4.0.0/json
Package download link is
https://pypi.python.org/packages/source/i/ipython/ipython-4.0.0.tar.gz
md5 checksum is: c2fecbcf1c0fbdc82625c77a50733dd6
---------------------------------------------

Use `spack edit py-ipython@4.0.0` to inspect parsed file.
or `spack install py-ipython@4.0.0` to install package.
```

## grep info for a bunch of files 
```
$ ./crawl_pypi_index.py spack_py_package_list.txt
A text file containing multiple package names is supplied.
Querying http://pypi.python.org/pypi/Cython/0.21.2/json
Package download link is
https://pypi.python.org/packages/source/C/Cython/Cython-0.21.2.tar.gz
md5 checksum is: d21adb870c75680dc857cd05d41046a4
---------------------------------------------
....
<OUTPUT OMITTED >

A list of modified package names has been written to
./parsed_file_2015_09_27_12_31.txt
Use `$ cat ./parsed_file_2015_09_27_12_31.txt | xargs spack install` to install
```

# known issues 

* SSL CERTIFICATION ERROR from urllib2 - unresolved for certain python versions
* package without `tar.gz` download format cannot be installed - `Spack` currently doesn't
    support installation of other formats 
* python executables installed with `Spack` may have a Shebang that is too long. See this [Github
    issue](https://github.com/scalability-llnl/spack/issues/104)
