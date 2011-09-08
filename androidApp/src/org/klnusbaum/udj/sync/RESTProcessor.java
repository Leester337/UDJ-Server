/**
 * Copyright 2011 Kurtis L. Nusbaum
 * 
 * This file is part of UDJ.
 * 
 * UDJ is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 * 
 * UDJ is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with UDJ.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.klnusbaum.udj.sync;

import java.util.List;
import java.util.ArrayList;
import android.content.Context;
import android.content.ContentResolver;
import android.content.ContentProviderOperation;
import android.content.OperationApplicationException;
import android.database.Cursor;
import android.os.RemoteException;

import org.klnusbaum.udj.R;
import org.klnusbaum.udj.UDJPartyProvider;
import org.klnusbaum.udj.containers.PlaylistEntry;
import org.klnusbaum.udj.containers.LibraryEntry;

public class RESTProcessor{

  public static void processPlaylistEntries(
    List<PlaylistEntry> newEntries, String account, Context context)
    throws RemoteException, OperationApplicationException
  {
    final ContentResolver resolver = context.getContentResolver();
    ArrayList<ContentProviderOperation> batchOps = 
      new ArrayList<ContentProviderOperation>();
    for(PlaylistEntry pe: newEntries){
      if(pe.getSyncState() != UDJPartyProvider.NEEDS_INSERT_MARK){
        if(pe.getIsDeleted()){
          deletePlaylistEntry(pe, batchOps);
        }
        else{
          updatePlaylistEntry(pe, batchOps);
        }
      }
      else{
        insertPlaylistEntry(pe, batchOps);
      }

      if(batchOps.size() >= 50){
        resolver.applyBatch(context.getString(R.string.authority), batchOps);
        batchOps.clear();
      }
    }  
  }

  private static void insertPlaylistEntry(
    PlaylistEntry pe,
    ArrayList<ContentProviderOperation> batchOps)
  {
    final ContentProviderOperation.Builder insertOp = 
      ContentProviderOperation.newInsert(UDJPartyProvider.PLAYLIST_URI)
      .withValue(UDJPartyProvider.SONG_ID, pe.getSongId())
      .withValue(UDJPartyProvider.TIME_ADDED_COLUMN, pe.getTimeAdded())
      .withValue(UDJPartyProvider.SONG_COLUMN, pe.getSong())
      .withValue(UDJPartyProvider.ARTIST_COLUMN, pe.getArtist())
      .withValue(UDJPartyProvider.ALBUM_COLUMN, pe.getAlbum())
      .withValue(UDJPartyProvider.SONG_LENGTH, pe.getSongLength())
      .withValue(
        UDJPartyProvider.SYNC_STATE_COLUMN, UDJPartyProvider.SYNCED_MARK);
    batchOps.add(insertOp.build());
  }

  private static void deletePlaylistEntry(
    PlaylistEntry pe,
    ArrayList<ContentProviderOperation> batchOps)
  {
    String[] selectionArgs = new String[] {String.valueOf(pe.getPlId())};
    final ContentProviderOperation.Builder deleteOp = 
      ContentProviderOperation.newDelete(UDJPartyProvider.PLAYLIST_URI)
      .withSelection("WHERE " + UDJPartyProvider.SONG_ID_COLUMN + "=?", 
        selectionArgs);
    batchOps.add(deleteOp.build());
  }
    
  private static void updatePlaylistEntry(
    PlaylistEntry pe, 
    ArrayList<ContentProviderOperation> batchOps)
  {
    String[] selectionArgs = new String[] {String.valueOf(pe.getSongId())};
    final ContentProviderOperation.Builder updateBuilder = 
      ContentProviderOperation.newUpdate(UDJPartyProvider.PLAYLIST_URI)
      .withSelection("WHERE " + UDJPartyProvider.PLAYLIST_ID_COLUMN + "=?", 
        selectionArgs)
      .withValue(UDJPartyProvider.SYNC_STATE_COLUMN, 
        UDJPartyProvider.SYNCED_MARK)
    batchOps.add(updateBuilder.build());
  } 

  private static boolean haveSongId(int songId, ContentResolver resolver)
    throws OperationApplicationException
  {
    Cursor c = resolver.query(
      UDJPartyProvider.PLAYLIST_URI, 
      new String[] {"COUNT("+ UDJPartyProvider.SONG_ID_COLUMN+ ")"},
      "WHERE " + UDJPartyProvider.SONG_ID_COLUMN+ "=?",
      new String[] {String.valueOf(songId)},
      null);
    return c.getCount() > 0;
  }
}
