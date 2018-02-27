# -*- coding: utf-8 -*-
import gcreds

import gsuites


def test_gmail_search(creds):
  gmail = gsuites.Gmail(creds)
  # I have only one email containning this uniq stub
  q = 'D86F81AC-5F86-4360-ACEE-38010FBF3DE1'
  msgs = list(gmail.search(q))
  assert len(msgs) == 1


  q = 'label:unittest'
  msgs = list(gmail.search(q))
  assert len(msgs) == 2
  msg_ids = [m.get('id')for m in msgs]
  messages = gmail.get_messages(
      msg_ids, format='metadata', metadataHeaders=['Subject'])
  m1 = messages[1]
  assert len(messages) == 2
  assert u'unittest 你好，哈哈！' ==  m1['payload']['headers'][0]['value']
  assert u'Too young too naïve' in m1['snippet']

