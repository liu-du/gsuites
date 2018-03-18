import datetime
import mimetypes
import os
import logging

from apiclient import discovery
from oauth2client.client import OAuth2Credentials
from googleapiclient.http import MediaFileUpload
import httplib2


GMAIL_API_VERSION = 'v1'
CALENDAR_API_VERSION = 'v3'
DRIVE_API_VERSION = 'v3'


def credentials_from_json(json_str):
  return OAuth2Credentials.from_json(json_str)


class Drive(object):
  def __init__(self, credential):
    http = credential.authorize(httplib2.Http())
    self.service = discovery.build('drive', DRIVE_API_VERSION, http=http)
    self.logger = logging.getLogger(self.__class__.__name__)

  def list_files(self, q, fields=['id', 'name']):
    fields_stmt = "nextPageToken, files({})".format(','.join(fields))
    page_token = None
    while True:
      response = self.service.files().list(
          q=q, spaces='drive', fields=fields_stmt, pageToken=page_token
      ).execute()
      for file in response.get('files', []):
        yield file
      page_token = response.get('nextPageToken', None)
      if page_token is None:
        break

  def find_folder(self, name):
    q = ("mimeType='application/vnd.google-apps.folder' "
         "and name = '{}' "
         "and trashed = false").format(name)
    return self.list_files(q)

  def _make_dir(self, name, parent_id='root'):
    q_tpl = (
        "mimeType='application/vnd.google-apps.folder' "
        "and trashed = false"
        "and name = '{name}' "
        "and '{parent}' in parents "
    )

    q = q_tpl.format(name=name, parent=parent_id)
    result = list(self.list_files(q))

    if result:
      return result[0]

    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    return self.service.files().create(body=file_metadata, fields='id').execute()

  def upload_file(self, localfile, remotefile):
    mtype, encoding = mimetypes.guess_type(localfile)
    fname = os.path.basename(remotefile)
    folder_name = os.path.dirname(remotefile)
    folder_node = self.make_dirs(folder_name)

    assert folder_node != None

    q_tpl = (
      "mimeType='{mtype}' "
      "and trashed = false"
      "and name = '{name}' "
      "and '{parent}' in parents "
    )
    q = q_tpl.format(name=fname, parent=folder_node['id'], mtype=mtype)

    media_body = MediaFileUpload(localfile, mimetype=mtype, resumable=True)

    file_metadata = {
        'mimeType': mtype,
        'name': fname,
        'parents': [folder_node['id']]
    }
    results = list(self.list_files(q))

    op = None
    if results:
      file_node = results[0]
      file_metadata = {
        'modifiedTime': datetime.datetime.utcnow().isoformat() + 'Z'
      }
      self.logger.info('updating exiting file: {}'.format(remotefile))
      op = self.service.files().update(
          fileId=file_node['id'], body=file_metadata,
          media_body=media_body)

    else:
      self.logger.info('creating new file: {}'.format(remotefile))
      op = self.service.files().create(
          media_body=media_body, body=file_metadata)

    return op.execute()

  def make_dirs(self, name):
    folders = name.split('/')
    if not folders[0]:
      folders.pop(0)

    parent_id = 'root'
    for fname in folders:
      node = self._make_dir(fname, parent_id)
      parent_id = node['id']

    return node


class Gmail(object):

  def __init__(self, creds, userId='me'):
    self.creds = creds
    self.http = self.creds.authorize(httplib2.Http())
    self.service = discovery.build('gmail', GMAIL_API_VERSION, http=self.http)
    self.userId = userId

  def search(self, query, **kwargs):
    page_token = None

    while True:
      ret = self.service.users().messages().list(
          userId=self.userId, q=query, pageToken=page_token, **kwargs).execute()
      messages = ret.get('messages')
      if messages:
        for m in messages:
          yield m

      page_token = ret.get('nextPageToken')

      if not page_token:
        break

  def get_message(self, message_id, **kwargs):
    return self.service.users().messages().get(
        userId=self.userId, id=message_id, **kwargs).execute()

  def get_messages(self, messages_ids, **kwargs):
    ret = []
    for msg_id in messages_ids:
      ret.append(
          self.service.users().messages().get(
              userId=self.userId, id=msg_id, **kwargs).execute()
      )
    return ret

  def get_labels(self):
    resp = self.service.users().labels().list(userId=self.userId).execute()
    return resp.get('labels', [])

  def add_label_to_mail(self, mail_id, label_name):
    lable_id = None
    for l in self.get_labels():
      if l.get('name') == label_name:
        lable_id = l.get('id')
        break
    if not lable_id:
      raise Exception('Label:%s is not found' % label_name)
    body= {"addLabelIds": [lable_id] }
    return self.service.users().messages().modify(
        userId=self.userId, id=mail_id, body=body).execute()


class Calendar(object):
  def __init__(self, creds):
    self.creds = creds
    self.http = self.creds.authorize(httplib2.Http())
    self.service = discovery.build(
        'calendar', CALENDAR_API_VERSION, http=self.http)

  def find_calendar(self, summary):
    page_token = None
    while True:
      calendar_list = self.service.calendarList().list(
          pageToken=page_token).execute()
      for cal in calendar_list['items']:
        if cal['summary'] == summary:
          return cal
      page_token = calendar_list.get('nextPageToken')
      if not page_token:
        break
    return None

  def add_event(self, calendarId, event):
    return self.service.events().insert(
        calendarId=calendarId, body=event).execute()

  def update_event(self, calendarId, eventId, event):
    return self.service.events().update(
        calendarId=calendarId, eventId=eventId, body=event).execute()

  def del_event(self, calendarId, eventId):
    return self.service.events().delete(
        calendarId=calendarId, eventId=eventId).execute()

  def find_events(self, calendarId, qry):
    page_token = None

    while True:
      events = self.service.events().list(
          pageToken=page_token, calendarId=calendarId, q=qry).execute()

      for e in events['items']:
        yield e

      page_token = events.get('nextPageToken')
      if not page_token:
        break
