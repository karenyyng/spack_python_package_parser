#!/usr/bin/env python
"""
Script to crawl the Python Package Index (PyPI)
and get the tar.gz file url for use with Spack

Supply a text file as argument to this script with content in format of:
package_name_1@version
package_name_2@version
...
see `spack_py_package_list.txt` for an example.

What works:
parsing package info from the web

Work in progress:
The corresponding package.py files will be written out in the appropriate
directory under `spack`

Prerequisite:
    * working version of `spack`
    * environmental variable `SPACK_ROOT` to be set correctly

Author: Karen Ng <karenyng@ucdavis.edu>
license: BSD
"""

from __future__ import print_function
import sys
import urllib2
import json
import os


def get_PyPI_download_URL_and_md5(package):
    if len(package) == 1:
        package_URL = "http://pypi.python.org/pypi/{0}/json".format(package[0])
        version = None
        print ("No version of the package {} was specified.".format(package[0]))

    elif len(package) == 2:
        version = package[1].strip()
        package_URL = \
            "http://pypi.python.org/pypi/{0}/{1}/json".format(*package)

    try:
        print ("Querying {}".format(package_URL))
        response = urllib2.urlopen(package_URL)

    except urllib2.HTTPError:
        print ("HTTPError: cannot find {} ".format('@'.join(package)) +
               "from http://pypi.python.org"
               )
        response = None

    if response is not None:
        package_info = json.load(response)

        if version not in package_info["releases"]:
            stable_ver = package_info["info"]["version"]
            print ("version specified {0} does not match release ".format(version) +
                " versions.".format(stable_ver))
            print ("Latest stable release version is " +
                "{}\n".format(stable_ver))
            use_stable_ver = raw_input("Use version {}? ".format(stable_ver) +
                                "(1 for True, 0 for False): ")
            use_stable_var = int(use_stable_ver)

            if use_stable_ver == 1:
                version = stable_ver
            else:
                retry = 0
                while(version not in package_info["releases"]):
                    print ("Choose from the list of release version: ")
                    map(print, package_info["releases"].keys())
                    version = \
                        raw_input(
                            "Try no: {}. \n".format(retry) +
                            "Type in one of the version numbers printed above: ")
                    retry += 1
                print ("version chosen is {}".format(version))
                if len(package_info["releases"][version]) == 0:
                    raise ValueError(
                        "No suitable tar.gz was found " +
                        "for {0}@{1}".format(package[0], version))

    download_link = [[ver["url"], ver["md5_digest"]]
                    for ver in package_info["releases"][version]
                    if 'tar.gz' in ver["url"]]

    if len(download_link) == 1:
        md5_digest = download_link[0][1]
        download_link = download_link[0][0]
    else:
        raise ValueError(
            "No suitable tar.gz was found for {0}@{1}".format(package[0],
                                                              version))

    return_this = {"download_link": download_link,
                   "md5checksum": md5_digest}

    if "summary" in package_info['info']:
        return_this["summary"] = package_info['info']['summary']
    if "home_page" in package_info['info']:
        return_this["homepage"] = package_info['info']['home_page']

    return_this["name"] = package[0]
    return_this["version"] = version

    print ("Package download link is {}".format(download_link))
    print ("md5 checksum is: {}".format(md5_digest))
    print ("---------------------------------------------\n")

    return return_this


def parse_package_py_content(parsed_info):
    lines = [
        "from spack import *",
        "",
        "class Py{}(Package):".format(parsed_info["name"][0].upper() +
                                      parsed_info["name"][1:]
                                      ),
        '    """{}"""'.format(parsed_info["summary"]),
        '    homepage = "{}"'.format(parsed_info["homepage"]),
        '    version("{0}", "{1}",'.format(parsed_info["version"],
                                           parsed_info["md5checksum"]
                                           ),
        '            url="{}")'.format(parsed_info["download_link"]),
        '',
        '    extends("python")',
        "",
        '    def install(self, spec, prefix):',
        '        python("setup.py", "install", "--prefix=%s" % prefix)'
        ]

    lines = [l + "\n" for l in lines]
    return lines


def write_package_file(parsed_info):
    SPACK_PATH = os.environ["SPACK_ROOT"]
    filedir = SPACK_PATH + "/var/spack/packages/py-" + \
        parsed_info["name"].strip()

    if os.path.exists(filedir + "/package.py"):
        f = open(filedir + "/package.py", "r")
        lines = f.readlines()
        f.close()
        f = open(filedir + "/package.py", "w")
        line_no_w_version = [line_no for line_no, line in enumerate(lines)
                             if 'version' in line][0]

        for line_no, line in enumerate(lines):
            if line_no != line_no_w_version:
                f.write(line)
            else:
                append_line = \
                    "    " + \
                    "version('{0}',".format(parsed_info["version"]) + \
                    "'{0}',\n".format(parsed_info["md5checksum"]) + \
                    "           " + \
                    "url='{0}')".format(parsed_info["download_link"])
                f.write(append_line + "\n")
                f.write(line)

    else:
        f = open(filedir + "/package.py", "w")
        lines = parse_package_py_content(parsed_info)
        f.writelines(lines)
        f.close()


if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     raise ValueError("Require argument for the text file with packages.")

    if len(sys.argv) < 2:
        raise ValueError("Require argument for the package name.")

    elif len(sys.argv) == 2:
        package = sys.argv[1]
        package = package.split('@')

    parsed_info = get_PyPI_download_URL_and_md5(package)
    write_package_file(parsed_info)


