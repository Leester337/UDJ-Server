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
package org.klnusbaum.udj;

import android.content.ContentProvider;
import android.net.Uri;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteQueryBuilder;
import android.content.Context;
import android.util.Log;
import android.database.SQLException;
import android.content.ContentUris;

import java.util.ArrayList;

/**
 * Content provider used to maintain the content asociated
 * with the current party the user is logged into.
 */
public class UDJPartyProvider extends ContentProvider{
  
	/** Name of the database */
  private static final String DATABASE_NAME = "partydb.db";
	/** Database version number */
  private static final int DATABASE_VERSION = 1;
	/** Name of the playlist table. */
  private static final String PLAYLIST_TABLE_NAME = "playlist";
  /** Name of the partiers table. */
  private static final String PARTIERS_TABLE_NAME = "partiers";

  /** URI for the playlist */
  public static final Uri PLAYLIST_URI = 
    Uri.parse("content://org.klnusbaum.udj/playlist");

  /** URI for list of partiers */
  public static final Uri PARTIERS_URI =
    Uri.parse("content://org.klnusbaum.udj/partiers");

  /** PLAYLIST TABLE */

  /** The various states a playlist record can be in */
  public static final String SYNCED_MARK="synced";
  public static final String UPDATEING_MARK ="updating"; 
  public static final String NEEDS_UP_VOTE ="needs_up_vote"; 
  public static final String NEEDS_DOWN_VOTE ="needs_down_vote"; 
  public static final String NEEDS_INSERT_MARK ="needs_insert"; 

  /** The various states of a playlist record's vote status */
  public static final String HASNT_VOTED="hasnt_voted";
  public static final String VOTED_UP="votedup";
  public static final String VOTED_DOWN="voteddown";
  
	/** Constants used for various Playlist column names */
  public static final String PLAYLIST_ID_COLUMN = "_id";
  public static final String SYNC_STATE_COLUMN = "sync_state";
  public static final String SONG_ID_COLUMN ="song_id";
  public static final String TIME_ADDED_COLUMN ="time_added";
  public static final String VOTE_STATUS_COLUMN ="vote_status";
  public static final String SONG_COLUMN = "song";
  public static final String ARTIST_COLUMN = "artist";
  public static final String ALBUM_COLUMN = "album";
  public static final String SONG_LENGTH_COLUMN = "length";

	/** SQL statement for creating the playlist table. */
  private static final String PLAYLIST_TABLE_CREATE = 
    "CREATE TABLE " + PLAYLIST_TABLE_NAME + "("+
		PLAYLIST_ID_COLUMN + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
    VOTE_STATUS_COLUMN + " TEXT NOT NULL DEFAULT '" + HASNT_VOTED +"', " +
    SYNC_STATE_COLUMN + " TEXT NOT NULL DEFAULT '" + SYNCED_MARK + "', " +
    SONG_ID_COLUMN + " INTEGER, "+
    TIME_ADDED_COLUMN + " TEXT DEFAULT CURRENT_TIMESTAMP, " +
    SONG_COLUMN + " TEXT NOT NULL DEFAULT \"\", " +
    ARTIST_COLUMN + " TEXT NOT NULL DEFAULT \"\", " +
    ALBUM_COLUMN + " TEXT NOT NULL DEFAULT \"\", "+
    SONG_LENGTH_COLUMN + " INTEGER NOT NULL DEFAULT 0);";

	/** Helper for opening up the actual database. */
  private PartyDBHelper dbOpenHelper;

	/**
	 * A class for helping open a HostsDB.
	 */
  private class PartyDBHelper extends SQLiteOpenHelper{

		/**
		 * Constructs a new HostsDBOpenHelper object.
		 *
	 	 * @param context The context in which the HostsDBOpenHelper is used.
	 	 */
    PartyDBHelper(Context context){
      super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db){
      db.execSQL(PLAYLIST_TABLE_CREATE);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion){

    }
  }

  @Override
  public boolean onCreate(){
    dbOpenHelper = new PartyDBHelper(getContext());
    return true;
  }

  @Override
  public String getType(Uri uri){
    return "none";
  }

  @Override
  public int delete(Uri uri, String where, String[] whereArgs){
    return 0;
  }

  @Override
  public Uri insert(Uri uri, ContentValues initialValues){
    SQLiteDatabase db = dbOpenHelper.getWritableDatabase();
    if(uri.equals(PLAYLIST_URI)){
      long rowId = db.insert(PLAYLIST_TABLE_NAME, null, initialValues);
      if(rowId > 0){
        getContext().getContentResolver().notifyChange(
          PLAYLIST_URI, null, true);
        return ContentUris.withAppendedId(PLAYLIST_URI, rowId); 
      }
      else{
        throw new SQLException("Failed to insert " + uri);
      }
    }
    else{
      throw new IllegalArgumentException("Unknown URI " + uri);
    }
  }
  
  @Override
  public Cursor query(Uri uri, String[] projection, 
    String selection, String[] selectionArgs, String sortOrder)
  {
    SQLiteQueryBuilder qb = new SQLiteQueryBuilder();
    if(!uri.getAuthority().equals(getContext().getString(R.string.authority))){
      throw new IllegalArgumentException("Unknown URI " + uri);
    }

    if(uri.getPath().equals(PLAYLIST_URI.getPath())){
      qb.setTables(PLAYLIST_VIEW_NAME); 
    }
    else if(uri.getPath().equals(LIBRARY_URI.getPath())){
      qb.setTables(LIBRARY_TABLE_NAME); 
    }
    else{
      throw new IllegalArgumentException("Unknown URI " + uri);
    }

    SQLiteDatabase db = dbOpenHelper.getReadableDatabase();
    Cursor toReturn = 
      qb.query(db, projection, selection, selectionArgs, null, null, sortOrder);
    toReturn.setNotificationUri(getContext().getContentResolver(), uri);
    return toReturn;
  }

  @Override
  public int update(Uri uri, ContentValues values, String where, 
    String[] whereArgs)
  {
    SQLiteDatabase db = dbOpenHelper.getWritableDatabase();
    if(uri.equals(PLAYLIST_URI)){
      int numRowsChanged = 
        db.update(PLAYLIST_TABLE_NAME, values, where, whereArgs);
      getContext().getContentResolver().notifyChange(PLAYLIST_URI, null, true);
      return numRowsChanged;
    }
    return 0;
  }
}
