import json

from udj.headers import MISSING_RESOURCE_HEADER
from udj.models import Vote
from udj.models import Player
from udj.models import Participant
from udj.models import LibraryEntry
from udj.models import ActivePlaylistEntry
from udj.models import PlaylistEntryTimePlayed
from udj.decorators import AcceptsMethods
from udj.decorators import ActivePlayerExists
from udj.decorators import UpdatePlayerActivity
from udj.decorators import HasNZParams
from udj.authdecorators import NeedsAuth
from udj.authdecorators import TicketUserMatch
from udj.authdecorators import IsOwnerOrParticipates
from udj.JSONCodecs import UDJEncoder

from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from settings import sortActivePlaylist

@NeedsAuth
@AcceptsMethods(['GET'])
@ActivePlayerExists
@IsOwnerOrParticipates
@UpdatePlayerActivity
def getActivePlaylist(request, user, player_id, activePlayer):
  queuedEntries = ActivePlaylistEntry.objects.filter(song__player=activePlayer, state='QE')
  queuedEntries = sortActivePlaylist(queuedEntries)
  playlist={'active_playlist' : queuedEntries}

  try:
    currentPlaying = ActivePlaylistEntry.objects.get(song__player=activePlayer, state='PL')
    playlist['current_song'] = currentPlaying
  except ObjectDoesNotExist:
    playlist['current_song'] = {}

  return HttpResponse(json.dumps(playlist, cls=UDJEncoder))

@NeedsAuth
@AcceptsMethods(['PUT', 'DELETE'])
@ActivePlayerExists
@IsOwnerOrParticipates
@UpdatePlayerActivity
def modActivePlaylist(request, user, player_id, lib_id, activePlayer):
  if request.method == 'PUT':
    return add2ActivePlaylist(user, lib_id, activePlayer)
  elif request.method == 'DELETE':
    return removeFromActivePlaylist(user, lib_id, activePlayer)

@transaction.commit_on_success
def add2ActivePlaylist(user, lib_id, activePlayer):
  try:
    libEntry = LibraryEntry.objects.get(player=activePlayer, player_lib_song_id=lib_id,
      is_deleted=False, is_banned=False)
  except ObjectDoesNotExist:
    toReturn = HttpResponseNotFound()
    toReturn[MISSING_RESOURCE_HEADER] = 'song'
    return toReturn

  if ActivePlaylistEntry.objects.filter(song=libEntry)\
      .exclude(state='RM').exclude(state='FN').exists():
    return HttpResponse(status=409)

  addedEntry = ActivePlaylistEntry(song=libEntry, adder=user)
  addedEntry.save()

  Vote(playlist_entry=addedEntry, user=user, weight=1).save()

  return HttpResponse(status=201)

def removeFromActivePlaylist(user, lib_id, activePlayer):
  try:
    playlistEntry = ActivePlaylistEntry.objects.get(
        song__player=activePlayer,
        song__player_lib_song_id=lib_id,
        state='QE')
  except ObjectDoesNotExist:
    toReturn = HttpResponseNotFound()
    toReturn[MISSING_RESOURCE_HEADER] = 'song'
    return toReturn

  if user!=activePlayer.owning_user and user!=playlistEntry.adder:
    return HttpResponseForbidden()

  playlistEntry.state='RM'
  playlistEntry.save()
  return HttpResponse()




"""
import json
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from udj.decorators import IsEventHostOrAdder
from udj.decorators import IsEventHost
from udj.decorators import AcceptsMethods
from udj.decorators import NeedsJSON
from udj.decorators import NeedsAuth
from udj.decorators import InParty
from udj.decorators import TicketUserMatch
from django.db.models import Count
from django.db.models import Sum
from udj.models import ActivePlaylistEntry
from udj.models import PlaylistEntryTimePlayed
from udj.models import LibraryEntry
from udj.models import Event
from udj.models import Vote
from udj.models import AvailableSong
from udj.JSONCodecs import getActivePlaylistArray
from udj.JSONCodecs import getActivePlaylistEntryDictionary
from udj.headers import getGoneResourceHeader
from udj.auth import getUserForTicket
from udj.utils import getJSONResponse

@NeedsAuth
@InParty
@AcceptsMethods('GET')
def getActivePlaylist(request, event_id):
  playlistEntries = ActivePlaylistEntry.objects.filter(
    event__id=event_id, state=u'QE').annotate(
      totalvotes=Sum('vote__weight')).order_by('-totalvotes','time_added')

  activePlaylist = getActivePlaylistArray(playlistEntries)
  currentSongDict = {}
  try:
    currentSong = ActivePlaylistEntry.objects.get(
      event__id=event_id, state=u'PL')
    currentSongDict = getActivePlaylistEntryDictionary(currentSong)
    currentSongDict['time_played'] = \
      PlaylistEntryTimePlayed.objects.get(playlist_entry=currentSong).time_played.replace(microsecond=0).isoformat()
  except ObjectDoesNotExist:
    pass

  return getJSONResponse(json.dumps(
    {
      "current_song" : currentSongDict,
      "active_playlist" : activePlaylist
    }
  ))

def addSong2ActivePlaylist(song_request, event_id, adding_user):
  event = Event.objects.get(pk=event_id)
  #songToAdd = LibraryEntry.objects.get(
  #    host_lib_song_id=song_request['lib_id'], owning_user=event.host)
  songToAdd = get_object_or_404(AvailableSong, song__host_lib_song_id=song_request['lib_id'],
      event__id=event_id)

  entryDefaults = {'song': songToAdd.song}

  if songToAdd.state == u'RM':
    entryDefaults['state'] = u'RM'

  added , created = ActivePlaylistEntry.objects.get_or_create(
    adder=adding_user,
    event=event,
    client_request_id=song_request['client_request_id'],
    defaults=entryDefaults)
  if created:
    Vote(user=adding_user, playlist_entry=added, weight=1).save()

#TODO Need to add a check to make sure that they aren't trying to add
#a song  that's not in the available music.
@NeedsAuth
@InParty
@AcceptsMethods('PUT')
@NeedsJSON
def addToPlaylist(request, event_id):
  user = getUserForTicket(request)
  songsToAdd = json.loads(request.raw_post_data)
  for song_request in songsToAdd:
    addSong2ActivePlaylist(song_request, event_id, user)

  return HttpResponse(status = 201)

@csrf_exempt
@NeedsAuth
@InParty
@AcceptsMethods('POST')
def voteSongDown(request, event_id, playlist_id, user_id):
  return voteSong(event_id, playlist_id, user_id, -1)

@csrf_exempt
@NeedsAuth
@InParty
@AcceptsMethods('POST')
def voteSongUp(request, event_id, playlist_id, user_id):
  return voteSong(event_id, playlist_id, user_id, 1)

def voteSong(event_id, playlist_id, user_id, voteWeigth):
  votingUser = User.objects.get(pk=user_id)
  entryToVote = get_object_or_404(ActivePlaylistEntry, pk=playlist_id)

  #Check to see if the song is still in the queue
  if entryToVote.state != u'QE':
    response = HttpResponse(status=410)
    response[getGoneResourceHeader()] = "song"
    return response

  #Check to see if a previous vote exists. If it does, change the weight
  #to the weight given in the arguments. If it doesn't, create a new one
  #with the specified weight
  try:
    previousVote = Vote.objects.get(
      user=votingUser, playlist_entry=entryToVote)
    previousVote.weight = voteWeigth
    previousVote.save()
  except ObjectDoesNotExist:
    Vote(user=votingUser, playlist_entry=entryToVote, weight=voteWeigth).save()
 
  return HttpResponse()

@NeedsAuth
@IsEventHostOrAdder
@AcceptsMethods('DELETE')
def removeSongFromActivePlaylist(request, event_id, playlist_id):
  toRemove = get_object_or_404(
    ActivePlaylistEntry, event__id=event_id, id=playlist_id)
  toRemove.state=u'RM'
  toRemove.save()
  return HttpResponse()

@NeedsAuth
@InParty
@TicketUserMatch
@AcceptsMethods('GET')
def getAddRequests(request, event_id, user_id):
  addRequests = ActivePlaylistEntry.objects.filter(
    event__id=event_id, adder__id=user_id).only(
    'client_request_id', 
    'song__host_lib_song_id')
      
  requestIds = [
   {'client_request_id' : add_request.client_request_id,
   'lib_id' : add_request.song.host_lib_song_id}
   for add_request in addRequests]
  return getJSONResponse(json.dumps(requestIds))

@NeedsAuth
@InParty
@TicketUserMatch
@AcceptsMethods('GET')
def getVotes(request, event_id, user_id):
  votes = Vote.objects.filter(
    playlist_entry__event__id=event_id,
    user__id=user_id, playlist_entry__state=u'QE')
  upvoteIds = [vote.playlist_entry.id for vote in votes if vote.weight==1]
  downvoteIds = [vote.playlist_entry.id for vote in votes if vote.weight==-1]
  return getJSONResponse(json.dumps(
    {'up_vote_ids' : upvoteIds, 'down_vote_ids' : downvoteIds}))
""" 
