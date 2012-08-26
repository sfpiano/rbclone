from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class AdminTest(LiveServerTestCase):
  fixtures = ['admin_user.json']

  def setUp(self):
    self.browser = webdriver.Firefox()

  def tearDown(self):
    self.browser.quit()

  def test_can_create_reviewfile_from_admin(self):
    # Gertrude opens her web browser, and goes to the admin page
    self.browser.get(self.live_server_url + '/admin/')

    # She sees the familiar 'Django administration' heading
    body = self.browser.find_element_by_tag_name('body')
    self.assertIn('Test administration', body.text)

    username_field = self.browser.find_element_by_name('username')
    username_field.send_keys('sfiorell')

    password_field = self.browser.find_element_by_name('password')
    password_field.send_keys('foobar')
    password_field.send_keys(Keys.RETURN)

    body = self.browser.find_element_by_tag_name('body')
    self.assertIn('Site administration', body.text)

    rf_links = self.browser.find_elements_by_link_text('Review files')
    self.assertEqual(len(rf_links), 1)

    rf_links[0].click()

    new_rf_link = self.browser.find_element_by_link_text('Add review file')
    new_rf_link.click()

    body = self.browser.find_element_by_tag_name('body')
    self.assertIn('Filename:', body.text)
    self.assertIn('Revision:', body.text)
    self.assertIn('File data:', body.text)

    filename_data = 'Test filename'
    revision_data = '2'

    filename_field = self.browser.find_element_by_name('filename')
    filename_field.send_keys(filename_data)
    revision_field = self.browser.find_element_by_name('revision')
    revision_field.send_keys(revision_data)
    file_data_field = self.browser.find_element_by_name('file_data')
    file_data_field.send_keys("Test file data")

    save_button = self.browser.find_element_by_css_selector("input[value='Save']")
    save_button.click()

    new_rf_links = self.browser.find_elements_by_link_text(
      '%s (%s)' % (filename_data, revision_data))
    self.assertEquals(len(new_rf_links), 1)
