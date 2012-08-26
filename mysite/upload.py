#!/usr/bin/python

from sys import argv
import sys
import urllib
import urllib2

if len(argv) > 1:
  try:
    file_data = open(argv[1])
  except:
    print "Failed to open: %s" % argv[1]
    quit()
  
  data = urllib.urlencode((('file_data', file_data.read()), ('filename', argv[1]), ('revision', 1)))

  request = urllib2.Request('http://localhost:8000/api/',
                            data=data,
                            headers={'Content-Type':'application/x-www-form-urlencoded'})

  try:
    response = urllib2.urlopen(request)
    if response.getcode() != 201:
      print "Error: %d" % response.getcode()
  except urllib2.URLError as reason:
    print "Failed to connect on url: {0}".format(reason)
else:
  print "Missing file argument"
