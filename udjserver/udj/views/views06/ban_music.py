import json

from udj.views.views06.decorators import NeedsJSON
from udj.views.views06.decorators import AcceptsMethods
from udj.views.views06.decorators import PlayerExists
from udj.views.views06.decorators import HasNZParams
from udj.views.views06.authdecorators import NeedsAuth
from udj.views.views06.authdecorators import IsOwnerOrAdmin
from udj.models import LibraryEntry, Player, ActivePlaylistEntry
from udj.headers import MISSING_RESOURCE_HEADER
from udj.views.views06.helpers import HttpJSONResponse, removeIfOnPlaylist, getNonExistantLibIds

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist



@csrf_exempt
@NeedsAuth
@AcceptsMethods(['PUT', 'DELETE'])
@PlayerExists
@IsOwnerOrAdmin
def modifyBanList(request, player_id, lib_id, player):
  try:
    libEntry = LibraryEntry.objects.get(player=player, player_lib_song_id=lib_id)
    libEntry.is_banned=True if request.method == 'PUT' else False
    libEntry.save()
    if request.method == 'DELETE':
      removeIfOnPlaylist(libEntry)
    return HttpResponse()
  except ObjectDoesNotExist:
    toReturn = HttpResponseNotFound()
    toReturn[MISSING_RESOURCE_HEADER] = 'song'
    return toReturn


@csrf_exempt
@NeedsAuth
@AcceptsMethods(['POST'])
@PlayerExists
@IsOwnerOrAdmin
@HasNZParams(['to_ban', 'to_unban'])
def multiBan(request, player_id, player):
  try:
    toBan = json.loads(request.POST['to_ban'])
    toUnban = json.loads(request.POST['to_unban'])
  except ValueError:
    return HttpResponseBadRequest("Bad JSON. Couldn't even parse. \n" +
      "to add data: " + request.POST['to_add'] + "\n" +
      "to delete data: " + request.POST['to_delete'])

  nonExistentIds = getNonExistantLibIds(toBan, player)
  nonExistentIds += getNonExistantLibIds(toUnban, player)
  if len(nonExistentIds) > 0:
    toReturn = HttpJSONResponse(json.dumps(nonExistentIds), status=404)
    toReturn[MISSING_RESOURCE_HEADER] = 'song'
    return toReturn

  def setSongBanStatus(songid, banStatus):
    songToBan = LibraryEntry.objects.get(player=player, player_lib_song_id=songid)
    songToBan.is_banned = banStatus
    songToBan.save()

  map(lambda songid: setSongBanStatus(songid, True), toBan)
  map(lambda songid: setSongBanStatus(songid, False), toUnban)

  return HttpResponse()


