from diffviewer.models import ReviewFile, FileDiff, DiffSet, DiffComment
from django.forms import ModelForm, Textarea
from django.contrib import admin

class ReviewFileForm(ModelForm):
  class Meta:
    model = ReviewFile
    fields = ('filename', 'revision', 'file_data')
    widgets = {
      'file_data' : Textarea(attrs={'cols': 200, 'rows': 20}),
    }

class ReviewFileAdmin(admin.ModelAdmin):
  form = ReviewFileForm

class FileDiffAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {
      'fields': ['status',
                'old_file_id',
                'new_file_id',
                'diff_set_id']
      }),
  ]
  #list_display = ('old_file', 'revision', 'new_file')
  #list_filter = ['old_file']
  #search_fields = ['old_file']

class DiffSetAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {
      'fields': ['name', 'desc', 'status', 'approval_status',
                 'author_id', 'reviewer_ids', 'problem', 'solution']
    }),
  ]

class DiffCommentAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {
      'fields': ['user_id', 'file_id', 'comment', 'line_number', 'reply_to_id']
    }),
  ]

admin.site.register(FileDiff, FileDiffAdmin)
admin.site.register(DiffSet, DiffSetAdmin)
admin.site.register(DiffComment, DiffCommentAdmin)
admin.site.register(ReviewFile, ReviewFileAdmin)
