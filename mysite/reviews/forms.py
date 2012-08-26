from django import forms
from django.contrib.auth.models import Group, User

##------------------------------------------------------------------------------
##------------------------------------------------------------------------------
class NewReviewForm(forms.Form):
  ID = forms.CharField()
  Solution = forms.CharField()
  Assignees = forms.ModelMultipleChoiceField(queryset = User.objects.all())
  Reviewgroups = forms.ModelMultipleChoiceField(queryset = Group.objects.all())
