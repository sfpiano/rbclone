from diffviewer.models import DiffComment, DiffSet, FileDiff
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from repotools.dimensions import Dimensions
from reviews.forms import NewReviewForm
from util.decorators import profile
from util.modelcache import ModelCache

import subprocess

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
@login_required
def showreviews(request):
  view = request.GET.get('view', None)
  data = []

  if view is None:
    for review in DiffSet.objects.all():
      try:
        data.append(review)
      except IndexError:
        pass
  elif view == "assigned":
    user = User.objects.get(pk=request.user.id)
    for review in DiffSet.objects.all():
      if review.is_reviewer(user):
        try:
          data.append(review)
        except IndexError:
          pass
  elif view == "authored":
    user = User.objects.get(pk=request.user.id)
    for review in DiffSet.objects.filter(author_id=user):
      try:
        data.append(review)
      except IndexError:
        pass

  context = {
      'reviews' : data
    }

  return render_to_response(
    "reviews/reviews.html",
    RequestContext(request, context))

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
def handleReviewUpload(ID):
  p = subprocess.Popen(['/home/sfiorell/code/test1/mysite/dimdiff.py',
                        '/tmp/diffs',
                        ID])

  failure = p.wait()
  if failure:
    print "Failed to upload review"
    return HttpResponseRedirect('/reviews/new')
  
  context = {
    'form' : NewReviewForm()
  }

  # TODO - Create a review from the upload and sent the user to that page
  return render_to_response(
    "reviews/upload_form.html",
    RequestContext(request, context))

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
@login_required
def createReview(request):
  from django.contrib.auth.models import User, Group
  if request.method == 'POST':
    form = NewReviewForm(request.POST)

    if form.is_valid():
      cd = form.cleaned_data
      repo = Dimensions()
      data = {
        'user' : request.user,
        'solution' : cd['Solution'],
        'assignees' : cd['Assignees'],
        'groups' : cd['Reviewgroups']
      }
      newid = repo.import_diffset(cd['ID'], data)
      if newid != False:
        return HttpResponseRedirect('/r/%d/overview/' % int(newid))
      else:
        return HttpResponseRedirect('/r/new')
  else:
    form = NewReviewForm()

  return HttpResponseRedirect('/r/new')

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
@login_required
def newreview(request):
  context = {
    'form' : NewReviewForm()
  }

  return render_to_response(
    "reviews/upload_form.html",
    RequestContext(request, context))

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
#@profile("diff.prof")
def diff(request, set_id, file_id):
  from diffviewer.views import get_chunks
  from diffviewer.forms import CommentForm

  request_file_object = get_object_or_404(FileDiff, pk=file_id)

  if request_file_object.diff_set_id.id != int(set_id):
    raise Http404

  request_set_object = get_object_or_404(DiffSet, pk=set_id)

  try:
    user = User.objects.get(pk=request.user.id)
    is_reviewer = request_set_object.is_reviewer(user) and \
                  not request_set_object.has_reviewed(user.id)
  except:
    is_reviewer = False

  context = {
    'chunks': get_chunks(request_file_object),
    #'chunksDebug': get_chunks(request_file_object),
    'diffset' : request_set_object,
    'is_reviewer' : is_reviewer,
    'set_id' : set_id,
    'file_id' : file_id,
    'allfiles' : FileDiff.objects.filter(diff_set_id=set_id),
    'form' : CommentForm()
  }

  #response = render_to_response("diff/diff.html",
  #    RequestContext(request, context))
  #return response

  from djangomako.shortcuts import render_to_response
  return render_to_response("mako/diff.html",
                       context,
                       context_instance=RequestContext(request))

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
def print_user(data):
  user_cache = ModelCache(User)
  user = user_cache(Q(pk=data[0]))

  return "%s: %s - %s" % (user.username, data[1], data[2])

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
def comments(request, set_id):
  request_set_object = get_object_or_404(DiffSet, pk=set_id)

  files = FileDiff.objects.filter(diff_set_id=set_id)

  comments = {}
  for afile in files:
    result = map(print_user,
            DiffComment.objects.
            filter(file_id=afile.id).
            order_by('file_id', 'line_number').
            values_list('user_id', 'line_number', 'comment'))

    if afile.id in comments:
      comments[str(afile.get_name())].append(result)
    else:
      comments[str(afile.get_name())] = (result)

  context = {
    'name' : request_set_object.name,
    'diffset' : request_set_object,
    'allfiles' : files,
    'comments' : comments
  }

  from djangomako.shortcuts import render_to_response
  return render_to_response("mako/comments.html",
                       context,
                       context_instance=RequestContext(request))

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
def overview(request, set_id):
  request_file_object = get_object_or_404(DiffSet, pk=set_id)

  gtg_status = []
  for user in request_file_object.reviewer_ids.all():
    gtg_status.append([user, request_file_object.has_reviewed(user.id)])
  print gtg_status

  context = {
    'name' : request_file_object.name,
    'diffset' : request_file_object,
    'gtg_status' : gtg_status,
    'allfiles' : FileDiff.objects.filter(diff_set_id=set_id),
  }

  from djangomako.shortcuts import render_to_response
  return render_to_response(
    "mako/overview.html",
    context,
    context_instance=RequestContext(request))
