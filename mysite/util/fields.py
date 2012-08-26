from django.db import models

class ClobField(models.Field):
  """
  Field used to store Character Large OBject data
  """

  description = "Clob"

  def db_type(self, connection):
    return 'clob'
