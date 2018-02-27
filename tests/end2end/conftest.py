import gcreds
import pytest

import gsuites

@pytest.fixture(scope='module')
def creds():
  creds_json = gcreds.get('gmail/tly1980')
  return gsuites.credentials_from_json(creds_json)
