from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Tool(models.Model):
    name = models.CharField(max_length=32, unique=True)
    class_name = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return self.name

    def get_scmtool_class(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Repository(models.Model):
    name = models.CharField(max_length=64)
    path = models.CharField(
        max_length=255,
        help_text=_("This should be the path to the repository. For most "
                    "version control systems, this will be a URI of some "
                    "form or another. For CVS, this should be a pserver "
                    "path. For Perforce, this should be a port name. For "
                    "local git, this should be the path to the .git directory "
                    "on the local disk. For remote git, this should be the "
                    "git URL that users clone. For Plastic, this should be a "
                    "repository spec in the form [repo]@[hostname]:[port]."
                    "In case of ClearCase enter absolute path to VOB."))
    mirror_path = models.CharField(max_length=255, blank=True)
    raw_file_url = models.CharField(
        _('Raw file URL mask'),
        max_length=255,
        blank=True,
        help_text=_("A URL mask used to check out a particular revision of a "
                    "file using HTTP. This is needed for repository types "
                    "that can't access remote files natively. "
                    "Use <tt>&lt;revision&gt;</tt> and "
                    "<tt>&lt;filename&gt;</tt> in the URL in place of the "
                    "revision and filename parts of the path."))
    username = models.CharField(max_length=32, blank=True)
    password = models.CharField(max_length=128, blank=True)
    tool = models.ForeignKey(Tool, related_name="repositories")
    bug_tracker = models.CharField(
        _('Bug tracker URL'),
        max_length=256,
        blank=True,
        help_text=_("This should be the full path to a bug in the bug tracker "
                    "for this repository, using '%s' in place of the bug ID."))
    encoding = models.CharField(
        max_length=32,
        blank=True,
        help_text=_("The encoding used for files in this repository. This is "
                    "an advanced setting and should only be used if you're "
                    "sure you need it."))
    visible = models.BooleanField(
        _('Show this repository'),
        default=True,
        help_text=_('Use this to control whether or not a repository is '
                    'shown when creating new review requests. Existing '
                    'review requests are unaffected.'))

    def get_scmtool(self):
        cls = self.tool.get_scmtool_class()
        return cls(self)

    def is_accessible_by(self, user):
        """Returns whether or not the user has access to the repository.

        The repository is accessibly by the user if it is public or
        the user has access to it (either by being explicitly on the allowed
        users list, or by being a member of a review group on that list).
        """
        return True

    def is_mutable_by(self, user):
        """Returns whether or not the user can modify or delete the repository.

        The repository is mutable by the user if the user is an administrator
        with proper permissions or the repository is part of a LocalSite and
        the user is in the admin list.
        """
        return True

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Repositories"
        unique_together = (('name', 'local_site'),
                           ('path', 'local_site'))
