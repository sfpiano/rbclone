#!/usr/bin/env python

import urllib
import random
import os
import errno
import shutil
from optparse import OptionParser

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno == errno.EEXIST:
      pass
    else: raise

def main():
  random.seed()

  parser = OptionParser()
  #parser.add_option("-i", "--id", dest="reviewId", help="LCR ID")
  parser.add_option("-o", "--output", dest="output_file", help="Output file")
  (opts, args) = parser.parse_args()

  """
  0 = Output dir
  1 = LCR ID
  """

  if len(args) < 2:
    print "Missing args"
    quit(-1)

  # Add a random number on the end to minimize naming conflicts
  reviewId = args[1] + '_' + str(random.randint(0,10000))
  dirbase = os.path.join(args[0], reviewId)
  dirnew = os.path.join(dirbase, 'DimDiffNew')
  dirold = os.path.join(dirbase, 'DimDiffOld')

  mkdir_p(dirold)
  mkdir_p(dirnew)

  shutil.copy2('models.py', dirold)
  shutil.copy2('diffviewer/models.py', dirnew)
  shutil.copy2('views.py', dirold)
  shutil.copy2('diffviewer/views.py', dirnew)
  shutil.copy2('../data/old/ovlyMgr.cpp', dirold)
  shutil.copy2('../data/new/ovlyMgr.cpp', dirnew)

  if opts.output_file != None:
    with open(opts.output_file, 'w') as f:
      print>>f, 'A LCR Title'
      print>>f, 'A Problem Description'
      print>>f, '%s/ovlyMgr.cpp,3,%s/ovlyMgr.cpp,4' % (dirold, dirnew)
      print>>f, '%s/models.py,3,%s/models.py,4' % (dirold, dirnew)
      print>>f, '%s/views.py,3,%s/views.py,4' % (dirold, dirnew)

if __name__ == "__main__":
  main()
