from django.utils import unittest
from diffviewer.models import ReviewFile

class ReviewFileModelTest(unittest.TestCase):
  def test_create_model_and_save(self):
    rf = ReviewFile(filename='test.cc',
                    revision=1,
                    file_data="Test file data")
    rf.save()

    all_rf = ReviewFile.objects.all()
    self.assertEquals(len(all_rf), 1)
    only_rf = all_rf[0]
    self.assertEquals(only_rf, rf)

    self.assertEquals(only_rf.filename, "test.cc")
    self.assertEquals(only_rf.revision, 1)
    self.assertIn(only_rf.file_data, "Test file data")

  def test_poll_objects_are_named_after_their_question(self):
    rf = ReviewFile(filename='test.cc', revision=4)
    self.assertEquals(unicode(rf), 'test.cc (4)')
