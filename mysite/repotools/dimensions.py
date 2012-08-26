from repotools.repotool import RepoTool
import stylebot
from diffviewer.models import DiffSet, FileDiff, ReviewFile
import os
import subprocess
from tempfile import mkstemp

class Dimensions(RepoTool):

  def import_diffset(self, ID, data):
    fd, tmpfile = mkstemp()
    os.close(fd)

    outdir = '/tmp/diffs'

    p = subprocess.Popen(['/home/sfiorell/code/test1/mysite/dimdiff.py',
                          outdir,
                          ID,
                          '-o', tmpfile])

    failure = p.wait()
    if failure:
      print "Failed to upload review"
      return False

    with open(tmpfile) as f:
      contents = [line.strip() for line in f.readlines()]
    os.unlink(tmpfile)

    diffset = DiffSet(name=ID,
                      status=DiffSet.CREATED,
                      author_id=data['user'],
                      solution=data['solution'],
                      desc=contents[0],
                      problem=contents[1],
                      approval_status="")
    diffset.save()

    # Need to have a primary key already established before we can use the
    # many-to-many model, so we have to save it a second time afterwards
    for user in data['assignees']:
      diffset.reviewer_ids.add(user)
    for group in data['groups']:
      diffset.group_ids.add(group)
    diffset.save()

    for i in range(2,len(contents)):
      line = contents[i].split(',')
      if len(line) == 0:
        continue
      assert(len(line) >= 2)

      argCount = len(line)

      if argCount == 4 or int(line[1]) != 1:
        firstPath = 'DimDiffOld/'
      else:
        firstPath = 'DimDiffNew/'

      import_filename = os.path.join(outdir, line[0])
      rfOne = ReviewFile(filename=import_filename.split(firstPath)[1],
                         revision=int(line[1]))
      with open(import_filename) as f:
        rfOne.file_data = f.read()
      rfOne.save()

      if argCount == 4:
        import_filename = os.path.join(outdir, line[2])
        rfTwo = ReviewFile(filename=import_filename.split('DimDiffNew/')[1],
                           revision=int(line[3]))
        with open(import_filename) as f:
          rfTwo.file_data = f.read()
        rfTwo.save()

      file_diff = FileDiff(diff_set_id=diffset)
      if argCount == 2:
        if rfOne.revision == 1:
          file_diff.status = FileDiff.NEW
          file_diff.new_file_id = rfOne
        else:
          file_diff.status = FileDiff.DELETED
          file_diff.old_file_id = rfOne
      else:
        file_diff.status = FileDiff.MODIFIED
        file_diff.old_file_id = rfOne
        file_diff.new_file_id = rfTwo

      file_diff.save()

      stylebot.analyzer.analyze(file_diff.id)

    return diffset.id
