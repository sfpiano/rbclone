from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from util.fields import ClobField

class ReviewFile(models.Model):

  filename = models.CharField(_("filename"), max_length=512)

  revision = models.PositiveIntegerField(_("revision"), null=True)

  file_data = ClobField(_("file data"))

  def get_name(self):
    return self.filename

  def get_data(self):
    return self.file_data

  def __unicode__(self):
    return u"%s (%s)" % (self.filename, self.revision)

class FileDiff(models.Model):
  """
  A diff of a single file.
  
  This contains the patch and information needed to produce original and
  patched versions of a single file in a repository.
  """
  MODIFIED = 'M'
  DELETED = 'D'
  NEW = 'N'
  
  STATUSES = (
      (MODIFIED, _('Modified')),
      (DELETED, _('Deleted')),
      (NEW, _('New')),
  )

  old_file_id = models.ForeignKey('ReviewFile',
                                  null=True,
                                  related_name="old_file")
  new_file_id = models.ForeignKey('ReviewFile',
                                  null=True,
                                  related_name="new_file")
  diff_set_id = models.ForeignKey('DiffSet', null=False)

  status = models.CharField(_("status"), max_length=1, choices=STATUSES)

  @property
  def deleted(self):
    return self.status == 'D'

  def get_old_file(self):
    return self.old_file_id

  def get_new_file(self):
    return self.new_file_id

  def get_name(self):
    if self.old_file_id != None:
      return self.get_old_file().get_name()
    else:
      return self.get_new_file().get_name()

  def __unicode__(self):
    return u"%s" % 'Diff of todo'

class DiffSet(models.Model):
  CREATED = 'N'
  IN_REVIEW = 'R'
  PART_APPROV = 'P'
  CLOSED = 'C'
  
  STATUSES = (
      (CREATED, _('Created')),
      (IN_REVIEW, _('In Review')),
      (PART_APPROV, _('Partially Approved')),
      (CLOSED, _('Closed')),
  )

  author_id = models.ForeignKey('auth.User', related_name="review_author")
  reviewer_ids = models.ManyToManyField('auth.User',
                                        related_name="review_reviewers",
                                        blank=True)
  group_ids = models.ManyToManyField('auth.Group',
                                        related_name="review_groups",
                                        blank=True)

  status = models.CharField(_("status"), max_length=1, choices=STATUSES)

  approval_status = models.CommaSeparatedIntegerField(_("approvals"),
                                                      max_length=64)

  name = models.CharField(_("name"), max_length=64)
  desc = models.CharField(_("description"), max_length=128)

  problem = models.TextField(_("problem"), blank=True)
  solution = models.TextField(_("solution"), blank=True)

  def __unicode__(self):
    return u"%s %s" % (self.name, self.desc)

  def get_name(self):
    return "%s %s" % (self.name, self.desc)

  def is_reviewer(self, user):
    return self.reviewer_ids.filter(id=user.id).count() > 0

  def has_reviewed(self, user_id):
    return self.approval_status.find("{0}".format(user_id)) > -1

class DiffComment(models.Model):
  user_id = models.ForeignKey('auth.User')
  file_id = models.ForeignKey('FileDiff', blank=True, null=True)
  reply_to_id = models.ForeignKey('DiffComment', blank=True, null=True)

  comment = models.CharField(_("comment"), max_length=1024)
  line_number = models.PositiveIntegerField(_("line number"), null=True)

  def __unicode__(self):
    return u"%s: Line %d - %s" % (self.user_id, self.line_number, self.comment)
