from django.contrib.auth.models import User
from diffviewer.models import DiffComment, FileDiff, ReviewFile

def analyze(fileID):
  try:
    filediff = FileDiff.objects.get(pk=fileID)
  except:
    return

  length_limit = 80

  if filediff.deleted:
    return

  stylebot = User.objects.get(username='stylebot')

  for index, line in enumerate(filediff.get_new_file().file_data.split('\n')):
    if len(line) > length_limit:
      comment = DiffComment(
                  user_id=stylebot,
                  file_id=filediff,
                  comment="Exceeds %d characters" % length_limit,
                  line_number=index+1)
      comment.save()

from django.http import HttpResponseRedirect

def test(request, fileid):
  analyze(fileid)
  return HttpResponseRedirect('/r/new')
