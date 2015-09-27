# What this is :
simple script that crawls PyPI indices API for download info for a Python package 
* package tar.gz url
* md5 checksum object
* one line summary of what the package is 
* package homepage 

# example usage:
```
$ ipython 
>>> %run ./crawl_pypi_index.py ipython@4.0.0
>>> parsed_info
{'download_link':
 u'https://pypi.python.org/packages/source/i/ipython/ipython-4.0.0.tar.gz',
 'homepage': u'http://ipython.org',
 'md5checksum': u'c2fecbcf1c0fbdc82625c77a50733dd6',
 'name': 'ipython',
 'summary': u'IPython: Productive Interactive Computing',
 'version': '4.0.0'}
```
