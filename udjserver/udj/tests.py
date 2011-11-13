"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from udj.models import Ticket
from udj.models import LibraryEntry
import json

def authTestUser(testObject):
    response = testObject.client.post('/udj/auth/', {'username': 'test1', 'password' : 'onetest'})
    testObject.ticket_hash = response.__getitem__('udj_ticket_hash')
    testObject.user_id = response.__getitem__('user_id')




class AuthTestCase(TestCase):
  fixtures = ['test_fixture.json']


  def testAuth(self):
    client = Client()
    response = client.post('/udj/auth/', {'username': 'test1', 'password' : 'onetest'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.has_header('udj_ticket_hash'))
    self.assertTrue(response.has_header('user_id'))
    testUser = User.objects.filter(username='test1')
    self.assertEqual(int(response.__getitem__('user_id')), testUser[0].id)
    ticket = Ticket.objects.filter(user=testUser)
    self.assertEqual(response.__getitem__('udj_ticket_hash'), ticket[0].ticket_hash)


class NeedsAuthTestCase(TestCase):
  fixtures = ['test_fixture.json']
  client = Client()
  def setUp(self):
    authTestUser(self)

class DoesServerOpsTestCase(NeedsAuthTestCase):

  def doJSONPut(self, url, payload):
    return self.client.put(
      url,
      data=payload, content_type='text/json', 
      **{'udj_ticket_hash' : self.ticket_hash})
   
  def doDelete(self, url):
    return self.client.delete(url, **{'udj_ticket_hash' : self.ticket_hash})
   
class LibSingleAddTestCase(DoesServerOpsTestCase):
  def testLibAdd(self):

    lib_id = 1
    song = 'Roulette Dares'
    artist = 'The Mars Volta'
    album = 'Deloused in the Comatorium'
    payload = '{ "to_add" : [{"host_lib_song_id" : ' + str(lib_id) + \
      ', "song" : "' + song + '", "artist" : "' + artist + '" , "album" : "' + \
      album +'"}], "id_maps" : [ {"server_id" : -1, "client_id" : ' + \
     str(lib_id) +  '}]}'

    response = self.doJSONPut('/udj/users/' + self.user_id + '/library/songs', payload)
    self.assertEqual(response.status_code, 201)


    matchedEntries = LibraryEntry.objects.filter(host_lib_song_id=lib_id, 
      owning_user=self.user_id)
    self.assertEqual(len(matchedEntries), 1, msg="Couldn't find inserted song.")
    insertedLibEntry = matchedEntries[0]
    self.assertEqual(insertedLibEntry.song, song)
    self.assertEqual(insertedLibEntry.artist, artist)
    self.assertEqual(insertedLibEntry.album, album)

    responseObject = json.loads(response.content)[0]
    self.assertEqual( \
      responseObject['server_id'], insertedLibEntry.server_lib_song_id)
    self.assertEqual(responseObject['client_id'], lib_id)


class LibMultiAddTestCase(DoesServerOpsTestCase):
  def testLibAdd(self):

    lib_id1 = '1'
    song1 = 'Roulette Dares'
    artist1 = 'The Mars Volta'
    album1 = 'Deloused in the Comatorium'

    lib_id2 = '2'
    song2 = 'Ilyena'
    artist2 = 'The Mars Volta'
    album2 = 'The Bedlam in Goliath'

    payload = '{ "to_add" : ' + \
      ' [{"song" : "' + song1 + '", "artist" : "' + artist1 + \
      '" , "album" : "' + album1 +'"}, ' + \
      '{"song" : "' + song2 + '", "artist" : "' + artist2 + \
      '" , "album" : "' + album2 +'"}],' + \
      '"id_maps" : [ {"server_id" : -1, "client_id" : 1}, ' + \
      '{"server_id" : -1, "client_id" : 2}]}'

    response = self.doJSONPut(
      '/udj/users/' + self.user_id + '/library/songs', payload)

    self.assertEqual(response.status_code, 201, msg=response.content)
    matchedEntries1 = LibraryEntry.objects.filter(host_lib_song_id=lib_id, \
      owning_user=self.user_id)
    self.assertEqual(len(matchedEntries1), 1, msg="Couldn't find inserted song.")
    insertedLibEntry1 = matchedEntries1[0]
    self.assertEqual(insertedLibEntry1.song, song)
    self.assertEqual(insertedLibEntry1.artist, artist)
    self.assertEqual(insertedLibEntry1.album, album)

    added1 = json.loads(response.content)[0]
    self.assertEqual(
      responseObject['server_id'], insertedLibEntry1.server_lib_song_id)
    self.assertEqual1(
      responseObject['client_id'], lib_id1)


class LibRemoveTestCase(DoesServerOpsTestCase):
  def testLibSongDelete(self):
    response = self.doDelete('/udj/users/' + self.user_id + '/library/2')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(
      len(LibraryEntry.objects.filter(server_lib_song_id=2)),
      0
    )


class LibFullDeleteTest(DoesServerOpsTestCase):
  def testFullDelete(self):
    response = self.doDelete('/udj/users/'+self.user_id+'/library')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(
      len(LibraryEntry.objects.filter(owning_user__id=2)),
      0
    )