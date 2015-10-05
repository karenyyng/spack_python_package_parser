#!/usr/bin/env python
"""
Script to crawl the Python Package Index (PyPI)
and get the tar.gz file url for use with Spack

Supply a text file as argument to this script with content in format of:
package_name_1@version
package_name_2@version
...
see `spack_py_package_list.txt` for an example.

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


def get_PyPI_download_URL_and_md5(package, cert=None):
    if len(package) == 1:
        package_URL = "http://pypi.python.org/pypi/{0}/json".format(package[0])
        version = None

    elif len(package) == 2:
        version = package[1].strip()
        package_URL = \
            "http://pypi.python.org/pypi/{0}/{1}/json".format(*package)

    print ("Querying {}".format(package_URL))
    if cert is None:
        try:
            response = urllib2.urlopen(package_URL)
        except urllib2.URLError:
            raise urllib2.URLError(
                "SSL CERTIFICATE_VERIFY_FAILED. \n"
                "You can choose to supply a valid SSL certificate " +
                "by downloading: cacert.pem from " + 
                "http://curl.haxx.se/docs/caextract.html, then "
                "rerun this code with: \n $ ./crawl_pypi_index.py " + 
                "PACKAGE_NAME PATH_TO/cacert.pem\n"
            )
    else:
        response = urllib2.urlopen(package_URL, cafile=cert)

    package_info = json.load(response)

    if version not in package_info["releases"]:
        stable_ver = package_info["info"]["version"]
        print ("Specified version was {0},".format(version) +
               ' which does not match any version on PyPI.'
               )
        print ("Latest stable release version is " +
               "{}\n".format(stable_ver))
        use_stable_ver = raw_input("Use version {}? ".format(stable_ver) +
                                   "(1 for True, 0 for False): ")
        use_stable_ver = int(use_stable_ver)

        if use_stable_ver == 1:
            version = stable_ver
        else:
            while(version not in package_info["releases"]):
                print ("Choose from the list of release version: ")
                map(print, package_info["releases"].keys())
                version = \
                    raw_input(
                        "Type in one of the version numbers printed above: ")
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
        return_this["summary"] = package_info['info']['summary'].strip()
    if "home_page" in package_info['info']:
        return_this["homepage"] = package_info['info']['home_page'].strip()

    # make sure that the package name is all in lower case
    return_this["name"] = package[0].strip().lower()
    return_this["version"] = version.strip()

    print ("Package download link is {}".format(download_link))
    print ("md5 checksum is: {}".format(md5_digest))
    print ("---------------------------------------------\n")

    return return_this


def parse_package_py_content(parsed_info):
    import re
    package_name = \
        parsed_info["name"][0].upper() + parsed_info["name"][1:].lower()
    package_name = re.split("[^0-9a-zA-Z]", package_name)
    package_name = [name[0].upper() + name[1:] for name in package_name]
    package_name = ''.join(package_name)

    lines = [
        "from spack import *",
        "",
        "class Py{}(Package):".format(package_name),
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


def check_if_version_exists(line_no_w_version, lines, version):
    # assume that people writing this package.py file
    # use 4 spaces as indentation.
    # if not, use autopep8 to clean up syntax
    version_lines = [lines[no][12:]
                     .split(',')[0]  # leave only the version info
                     .replace("'", '')  # remove single quotes
                     .replace('"', '')  # remove double quotes
                     .strip()
                     for no in line_no_w_version]

    for exist_ver in version_lines:
        if exist_ver == version.strip():
            print ("Version info exists for this package, " +
                   "nothing needs to be done.")
            return True


def write_package_file(parsed_info):
    SPACK_PATH = os.environ["SPACK_ROOT"]
    filedir = SPACK_PATH + "/var/spack/packages/py-" + \
        parsed_info["name"].strip()

    if os.path.exists(filedir + "/package.py"):
        f = open(filedir + "/package.py", "r")
        lines = f.readlines()
        f.close()
        line_no_w_version = [line_no for line_no, line in enumerate(lines)
                             if 'version' in line]

        version_exists = check_if_version_exists(line_no_w_version, lines,
                                                 parsed_info["version"])
        line_no_w_version = line_no_w_version[0]

        if not version_exists:
            print ("Appending new version {0} of {1}".format(
                parsed_info["version"], parsed_info["name"]) +
                " to {}/package.py".format(filedir)
            )
            f = open(filedir + "/package.py", "w")
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
        print ("Writing parsed info to {}/package.py".format(filedir))
        os.system('mkdir {}'.format(filedir))
        f = open(filedir + "/package.py", "w")
        lines = parse_package_py_content(parsed_info)
        f.writelines(lines)
        f.close()
    return


def parse_single_package(package, cert=None):
    parsed_info = get_PyPI_download_URL_and_md5(package, cert=cert)
    write_package_file(parsed_info)
    return "py-" + parsed_info["name"] + '@' + parsed_info['version']


if __name__ == "__main__":
    from datetime import datetime
    import os

    if len(sys.argv) < 2:
        raise ValueError("Require argument for the package name. e.g.\n" +
                         "$ ./crawl_pypi_index.py ipython@4.0.0\n"
                         )

    elif len(sys.argv) >= 2:
        package = sys.argv[1]
        if len(sys.argv) == 3:
            cert = sys.argv[2]
            if not os.path.isfile(cert):
                raise ValueError(
                    "Certificate path {} is not valid.".format(cert))
        else:
            cert = None
        if ".txt" not in package:
            print ("Detected single package name is supplied.")
            if cert is None:
                print ("No SSL certificate is supplied.")
            else:
                print ("SSL certificate is supplied: {}".format(cert))

            package = package.split('@')
            spack_name = parse_single_package(package, cert=cert)
            print (
                "Use `spack edit {}` to inspect the parsed build recipe.".format(
                    spack_name.split('@')[0]))
            print (
                "or `spack install {}` to install package.".format(spack_name))
        else:
            now = datetime.now().strftime("%Y_%m_%d_%H_%M")
            output_file1 = "./parsed_file_{}.txt".format(now)
            # output_file2 = "./install_parsed_packages_{}.sh".format(now)

            print ("A text file containing multiple package names is supplied.")

            input_fs = open(package, 'r')
            packages = input_fs.readlines()
            packages = [p.strip().split('@') for p in packages
                        if p and p != '\n']
            spack_names = map(lambda p: parse_single_package(p, cert=cert),
                              packages)
            spack_names = [name + '\n' for name in spack_names]

            print ("A list of modified package names " +
                   "has been written to \n{0} ".format(output_file1))
            print ("Use `$ cat {0} | xargs spack ".format(output_file1) +
                   "install` to install")

            f1 = open(output_file1, mode='w')
            edit_names = spack_names
            f1.writelines(edit_names)
            f1.close()
