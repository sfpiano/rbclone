from django import forms

class CommentForm(forms.Form):
  line_number = forms.IntegerField()
  message = forms.CharField()
  #reply_to = forms.IntegerField(initial=-1, widget=forms.widgets.HiddenInput())
