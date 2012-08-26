# Create your views here.
from difflib import SequenceMatcher
from diffviewer.diffutils import opcodes_with_metadata
from diffviewer.forms import CommentForm
from diffviewer.models import FileDiff, DiffComment, DiffSet
from diffviewer.myersdiff import MyersDiffer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import RequestContext
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re

import pygments
from pygments.lexers import CppLexer
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

NEWLINES_RE = re.compile(r'\r?\n')

@login_required
def comment(request):
  if request.method == 'POST':
    form = CommentForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      return HttpResponseRedirect('/contact/thanks/')
  else:
    form = CommentForm()

  context = {}
  return render_to_response('diff/comment_form.html', {'form': form}, RequestContext(request, context))

class NoWrapperHtmlFormatter(HtmlFormatter):
    """An HTML Formatter for Pygments that don't wrap items in a div."""
    def __init__(self, *args, **kwargs):
        super(NoWrapperHtmlFormatter, self).__init__(*args, **kwargs)

    def _wrap_div(self, inner):
        """
        Method called by the formatter to wrap the contents of inner.
        Inner is a list of tuples containing formatted code. If the first item
        in the tuple is zero, then it's a wrapper, so we should ignore it.
        """
        for tup in inner:
            if tup[0]:
                yield tup

def get_line_changed_regions(oldline, newline):
    if oldline is None or newline is None:
        return (None, None)

    # Use the SequenceMatcher directly. It seems to give us better results
    # for this. We should investigate steps to move to the new differ.
    differ = SequenceMatcher(None, oldline, newline)

    # This thresholds our results -- we don't want to show inter-line diffs if
    # most of the line has changed, unless those lines are very short.

    # FIXME: just a plain, linear threshold is pretty crummy here.  Short
    # changes in a short line get lost.  I haven't yet thought of a fancy
    # nonlinear test.
    if differ.ratio() < 0.6:
        return (None, None)

    oldchanges = []
    newchanges = []
    back = (0, 0)

    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == "equal":
            if (i2 - i1 < 3) or (j2 - j1 < 3):
                back = (j2 - j1, i2 - i1)
            continue

        oldstart, oldend = i1 - back[0], i2
        newstart, newend = j1 - back[1], j2

        if oldchanges != [] and oldstart <= oldchanges[-1][1] < oldend:
            oldchanges[-1] = (oldchanges[-1][0], oldend)
        elif not oldline[oldstart:oldend].isspace():
            oldchanges.append((oldstart, oldend))

        if newchanges != [] and newstart <= newchanges[-1][1] < newend:
            newchanges[-1] = (newchanges[-1][0], newend)
        elif not newline[newstart:newend].isspace():
            newchanges.append((newstart, newend))

        back = (0, 0)

    return (oldchanges, newchanges)

#def get_chunks(diffset, filediff, interfilediff, force_interdiff,
#               enable_syntax_highlighting):
def get_chunks(request_file_object):
  def diff_line(vlinenum, oldlinenum, newlinenum, oldline, newline,
              oldmarkup, newmarkup):
    """
    A generator that yields chunks within a range of lines in the specified
    filediff/interfilediff.

    This is primarily intended for use with templates. It takes a
    RequestContext for looking up the user and for caching file lists,
    in order to improve performance and reduce lookup times for files that have
    already been fetched.

    Each returned chunk is a dictionary with the following fields:

      ============= ========================================================
      Variable      Description
      ============= ========================================================
      ``change``    The change type ("equal", "replace", "insert", "delete")
      ``numlines``  The number of lines in the chunk.
      ``lines``     The list of lines in the chunk.
      ``meta``      A dictionary containing metadata on the chunk
      ============= ========================================================

    Each line in the list of lines is an array with the following data:

      ======== =============================================================
      Index    Description
      ======== =============================================================
      0        Virtual line number (union of the original and patched files)
      1        Real line number in the original file
      2        HTML markup of the original file
      3        Changed regions of the original line (for "replace" chunks)
      4        Real line number in the patched file
      5        HTML markup of the patched file
      6        Changed regions of the patched line (for "replace" chunks)
      7        True if line consists of only whitespace changes
      8        Comments associated with the current line
      ======== =============================================================
    """
    # This function accesses the variable meta, defined in an outer context.
    if oldline and newline and oldline != newline:
      oldregion, newregion = get_line_changed_regions(oldline, newline)
    else:
      oldregion = newregion = []

    result = [vlinenum,
              oldlinenum or '', mark_safe(oldmarkup or ''), oldregion,
              newlinenum or '', mark_safe(newmarkup or ''), newregion,
              (oldlinenum, newlinenum) in meta['whitespace_lines']]

    try:
      # Get the top-level comment for this line
      # Need to handle multiple comments on the same line here
      comments = DiffComment.objects.filter(
        line_number=newlinenum,
        file_id=request_file_object.id)
    except ObjectDoesNotExist:
      comments = None
    result.append(comments)

    if oldlinenum and oldlinenum in meta.get('moved', {}):
      destination = meta["moved"][oldlinenum]
      result.append(destination)
    elif newlinenum and newlinenum in meta.get('moved', {}):
      destination = meta["moved"][newlinenum]
      result.append(destination)

    return result

  def new_chunk(lines, start, end, collapsable=False,
              tag='equal', meta=None):
    if not meta:
        meta = {}

    left_headers = list(get_interesting_headers(differ, lines,
                                                start, end - 1, False))
    right_headers = list(get_interesting_headers(differ, lines,
                                                 start, end - 1, True))

    meta['left_headers'] = left_headers
    meta['right_headers'] = right_headers

    if left_headers:
        last_header[0] = left_headers[-1][1]

    if right_headers:
        last_header[1] = right_headers[-1][1]

    if (collapsable and end < len(lines) and
        (last_header[0] or last_header[1])):
        meta['headers'] = [
            (last_header[0] or "").strip(),
            (last_header[1] or "").strip(),
        ]

    return {
        'lines': lines[start:end],
        'numlines': end - start,
        'change': tag,
        'collapsable': collapsable,
        'meta': meta
    }

  def get_interesting_headers(differ, lines, start, end, is_modified_file):
      """Returns all headers for a region of a diff.

      This scans for all headers that fall within the specified range
      of the specified lines on both the original and modified files.
      """
      possible_functions = differ.get_interesting_lines('header',
                                                        is_modified_file)

      if not possible_functions:
          raise StopIteration

      try:
          if is_modified_file:
              last_index = last_header_index[1]
              i1 = lines[start][4]
              i2 = lines[end - 1][4]
          else:
              last_index = last_header_index[0]
              i1 = lines[start][1]
              i2 = lines[end - 1][1]
      except IndexError:
          raise StopIteration

      for i in xrange(last_index, len(possible_functions)):
          linenum, line = possible_functions[i]
          linenum += 1

          if linenum > i2:
              break
          elif linenum >= i1:
              last_index = i
              yield (linenum, line)

      if is_modified_file:
          last_header_index[1] = last_index
      else:
          last_header_index[0] = last_index

  def apply_pygments(data, filename):
    # XXX Guessing is preferable but really slow, especially on XML
    #     files.
    #if filename.endswith(".xml"):

    try:
      lexer = get_lexer_for_filename(filename, stripnl=False, encoding='utf-8')
    except pygments.util.ClassNotFound:
      lexer = CppLexer()

    #try:
    #  # This is only available in 0.7 and higher
    #  lexer.add_filter('codetagify')
    #except AttributeError:
    #  pass

    return pygments.highlight(data, lexer, NoWrapperHtmlFormatter()).splitlines()

  """
  Config variables
  """
  contextLines = 3
  enableSyntaxHighlighting = False
  collapse_threshold = 2 * contextLines + 3

  old = request_file_object.get_old_file().get_data()
  new = request_file_object.get_new_file().get_data()

  linenum = 1
  last_header = (None, None)

  a = NEWLINES_RE.split(old or '')
  b = NEWLINES_RE.split(new or '')

  a_num_lines = len(a)
  b_num_lines = len(b)

  markup_a = markup_b = None

  if enableSyntaxHighlighting:
    markup_a = apply_pygments(old or '', request_file_object.old_file)
    markup_b = apply_pygments(new or '', request_file_object.new_file)

  if not markup_a:
    markup_a = NEWLINES_RE.split(escape(old))
  if not markup_b:
    markup_b = NEWLINES_RE.split(escape(new))

  differ = MyersDiffer(a, b, False)

  for tag, i1, i2, j1, j2, meta in opcodes_with_metadata(differ):
      oldlines = markup_a[i1:i2]
      newlines = markup_b[j1:j2]
      numlines = max(len(oldlines), len(newlines))

      lines = map(diff_line,
          xrange(linenum, linenum + numlines),
          xrange(i1 + 1, i2 + 1), xrange(j1 + 1, j2 + 1),
          a[i1:i2], b[j1:j2], oldlines, newlines)

      if tag == 'equal' and numlines > collapse_threshold:
        last_range_start = numlines - contextLines

        if linenum == 1:
          yield new_chunk(lines, 0, last_range_start, True)
          yield new_chunk(lines, last_range_start, numlines)
        else:
          yield new_chunk(lines, 0, contextLines)

          if i2 == a_num_lines and j2 == b_num_lines:
            yield new_chunk(lines, contextLines, numlines, True)
          else:
            yield new_chunk(lines, contextLines,
                            last_range_start, True)
            yield new_chunk(lines, last_range_start, numlines)
      else:
          yield new_chunk(lines, 0, numlines, False, tag, meta)

      linenum += numlines

#def diff(request, set_id, file_id):
#  request_file_object = get_object_or_404(FileDiff, pk=file_id)
#
#  diffset = DiffSet.objects.get(pk=set_id)
#
#  try:
#    user = User.objects.get(pk=request.user.id)
#    is_reviewer = not diffset.has_reviewed(user.id)
#  except:
#    is_reviewer = False
#
#  context = {
#    'chunks': get_chunks(request_file_object),
#    'chunksDebug': get_chunks(request_file_object),
#    'diffset' : diffset,
#    'is_reviewer' : is_reviewer,
#    'set_id' : set_id,
#    'file_id' : file_id,
#    'allfiles' : FileDiff.objects.filter(diff_set_id=set_id),
#    'form' : CommentForm()
#  }
#
#  response = render_to_response("diff/diff.html",
#      RequestContext(request, context))
#  return response

@login_required
def createComment(request, set_id, file_id):
  if request.method == 'POST':
    try:
      user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
      # TODO
      print "User not found"

    form = CommentForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data

      # This method handles comment creation and modification
      if int(request.POST['comment_id']) > 0:
        comment = DiffComment.objects.get(pk=request.POST['comment_id'])
        comment.comment = cd['message']
      else:
        comment = DiffComment(
          comment=cd['message'],
          line_number=cd['line_number'],
          user_id=user,
          file_id=FileDiff.objects.get(pk=file_id))
      comment.save()

  return HttpResponseRedirect(reverse('reviews.views.diff',
                              args=(set_id,file_id)))

@login_required
def deleteComment(request, comment_id):
  request_file_object = get_object_or_404(DiffComment, pk=comment_id)

  try:
    user = User.objects.get(pk=request.user.id)
  except User.DoesNotExist:
    # TODO
    print "User not found"

  if user == request_file_object.user_id:
    request_file_object.delete()

  file_id = request_file_object.file_id
  set_id = file_id.diff_set_id

  return HttpResponseRedirect(reverse('reviews.views.diff',
                              args=(set_id.id,file_id.id)))

@login_required
def handleGTG(request, set_id):
  diffset = get_object_or_404(DiffSet, pk=set_id)

  try:
    user = User.objects.get(pk=request.user.id)
  except User.DoesNotExist:
    # TODO
    print "User not found"

  if diffset.is_reviewer(user):
    diffset.approval_status += (",%d") % user.id
    diffset.save()

  return HttpResponseRedirect(reverse('reviews.views.overview',
                              args=(set_id)))

#def comments(request, set_id):
#  request_file_object = get_object_or_404(DiffSet, pk=set_id)
#
#  comments = DiffComment.objects.filter(
#    file_id=request_file_object.id)
#
#  context = {
#    'name' : request_file_object.name,
#    'diffset' : request_file_object,
#    'allfiles' : FileDiff.objects.filter(diff_set_id=set_id),
#    'comments' : sorted(comments, key=lambda DiffComment: DiffComment.line_number)
#  }
#
#  return render_to_response(
#    "diff/comments.html", RequestContext(request, context))
#
#def overview(request, set_id):
#  request_file_object = get_object_or_404(DiffSet, pk=set_id)
#
#  gtg_status = []
#  for user in request_file_object.reviewer_ids.all():
#    gtg_status.append([user, request_file_object.has_reviewed(user.id)])
#  print gtg_status
#
#  context = {
#    'name' : request_file_object.name,
#    'diffset' : request_file_object,
#    'gtg_status' : gtg_status,
#    'allfiles' : FileDiff.objects.filter(diff_set_id=set_id),
#  }
#
#  return render_to_response(
#    "diff/overview.html", RequestContext(request, context))
