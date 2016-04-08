import os
import sys
import json
import pprint
import datetime

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy import API
from tweepy.streaming import StreamListener

from chazzer_token import *
from models.logger import Logger
from models.user import User
from models.game import *
from models.tweet import Tweet

import Chessnut 
from Chessnut.game import InvalidMove
import chessboard_renderer_unicode as renderer

pp = pprint.PrettyPrinter(indent=4)

#
# typicall errors are:
#
WRONG_GAME_ID = "wrong game id."
NOT_YOUR_MOVE = "not your move. "


class tweetchazzer(StreamListener):
    '''
        the game class itself.
        listens to the twitter stream and handles the requests.

    '''
    def __init__( self, api=None ):
        self.tweetCount = 0
        self.logger = Logger()
        self.log = self.logger.log
        self.api = api
        #print(str(self.log))

    def on_connect( self ):
        #print("Connection established.")
        self.log("Connection established.")

    def on_disconnect( self, notice ):
        print("Connection lost.")
        self.log( "...Connection lost " +  str(notice), level="ERROR")

    def on_data( self, status ):
        """ 
            handle all twwets, replys and direct messages
        """
        self.log(str(status), level="TWEET")
        tw = Tweet(status)
        print("...Tweet sender::: " + str(tw.sender))
        if tw.sender and tw.sender != "tweetchazzer":
            self.parse_tweet(tw)
        else:
            print("... skipping tweet due to sender == None or self")
    

    def on_direct_message( self, status ):
        print("on_direct_message")
        try:
            #print(str(status))
            self.log(str(status), level="DM")
            tw = Tweet(status)
            print("...DM sender::: " + tw.sender)
            if tw.sender and tw.sender != "tweetchazzer":
                self.parse_tweet(tw)
            else:
                print("... skipping tweet due to sender == None or self")
        except BaseException as e:
            print("Failed on_direct_message()", str(e))
            self.log(str(e), level="ERROR_DM")

    def on_error( self, status_code ):
        #print(status)
        self.log(str(status), level="ERROR")
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

    def get_parameter(self, text, tag):
        '''
            given a text returns the string following the 
            give tag or None if tag is not found.

            Example: text => text.strip().split() => ["a", "#b" , "c", "d" ]
            get_paramter("a #b c d", "#b") => returns c
        '''
        textlist = text.strip().split()
        try:
            return textlist[textlist.index(tag)+1]
        except (ValueError, IndexError) as e:
            # tag not found or no parameter after tag
            return None
        except:
            # something else (most p)
            return None

    def parse_tweet(self, tweet):
        '''
            parses the dm acording to one of the following inputs 
            1. GAME_REQUEST     => #iwanttoplay         
                    => parse for #iwanttoplay
            1.1 GAME_REQUEST     => #iwanttoplay  #oneonone       
                    => parse for #iwanttoplay #oneonone

            2. GAME_INVITATION  => #play vs|versus @opponent [#fen fen]   
                    => parse #play 
                    => extract @opponent [#fen fen]
            3. MOVE             => #GAME_ID #move ab-xy         
                    => parse #move 
                    => extract #GAME_ID, ab-xy
            4. GIVE-UP          => #GAME_ID #giveup
                    => parse #giveup
                    => extract #GAME_ID

        '''
        if "oneonone" and "iwanttoplay" in tweet.hashtags:
            print("... #oneonone")
            self.start_oneonone(tweet)

        elif "iwanttoplay" in tweet.hashtags:
            # GAME_REQUEST => Waitqueue 
            print ("... #iwanttoplay => wait queue")
            # add player with strength to waitqueue
            self.iwanttoplay(tweet)
        
        elif "move" in tweet.hashtags:
            print("... #move")
            self.move(tweet)

        elif "resign" or "concede" in tweet.hashtags:
            print("... resign")
            self.resign(tweet)

    def tweet_error(self, msg, receipient, image=None):
        self.log(msg, level="ERROR")
        if image:
            api.update_with_media()
        else:
            api.update( "@{} ".format(receipient.strip()) + msg)
    
    def move(self, tweet):
        '''
            make a move in a running game.
            # 1. check if game_id exists
            # 2. check if it was the senders turn (or if he is one of the players at all)
            # 3. check if move is valid
            # 4. apply move
            # update game (moves, last_move, whos_turn, status [maybe winner ?])
            # 5. render board with new fen
            # tweet to player whos turn it is now.
        '''
        print("... moving ...")
        #
        # check if gameid exists
        #
        g = Game()
        gameid = self.get_parameter(tweet.text, "#game_id")
        print("... game_ID::: " + str(gameid))
        if not gameid:
            # error => wrong or no gameid
            self.log("No gameid::: " + tweet, level="ERROR")
            self.tweet_error(WRONG_GAME_ID, get_username(tweet))
            return 
        game = g.find_one(where("id") == gameid)
        if game:
            # check if its the users game AND turn
            if (tweet.sender == game.twitter_name or tweet.sender == game.opponent_name) and (tweet.sender == game.whos_turn):
                #
                # OK, senders turn => Now check the move
                #
                move = self.get_parameter(tweet.text, "#move")
                chessnut_game = Chessnut.Game(fen=game.current_fen)
                print(chessnut_game)
                try:
                    #
                    # Move OK.
                    #
                    res = chessnut_game.apply_move(move)
                    print(chessnut_game)

                    image_file = renderer.generate_board(game.id, game.current_fen)

                except:
                    print("... InvalidMove: " + move)
                    msg = "Your move is invalid for this position. Valid moves are e.g.:"
                    msg += ", ".join(chessnut_game.get_moves())
                    image_file = renderer.generate_board(game.id, game.current_fen)
                    self.tweet_error(msg, tweet.sender)
            
            else:
                self.tweet_error("Sorry, it's not your turn. Please recheck your last game tweet.", tweet.sender)
                #todo: add time for opponent to move
        else:
            self.tweet_error("No such gameid. Please recheck your last game tweet.", tweet.sender)
            return


    def start_oneonone(self, tweet):
        ''' 
            start one on one game
        '''
        # GAME_REQUEST_ONEONONE => play
        print("... start oneonone ...")
        game = Game()
        game.type = TYPE_ONEONONE
        game.runstate = RUNSTATE_RUNNING
        game.starter = tweet.sender
        game.twitter_name = game.starter
        game.opponent_name = game.starter
        game.last_req_time = str(datetime.datetime.now())
        game.status = STATE_NORMAL
        game.whos_turn = game.opponent_name
        if "fen" in tweet.hashtags:
            fen = get_parameter(text, "#fen")
            game.start_fen = fen
            game.current_fen = fen
        try:
            image_file = renderer.generate_board(game.id, game.start_fen)
        except:
            # Error
            print("error creating board")
            return
        status = "@" + game.opponent_name + " it's your move."
        status += " Reply with: #move ab-xy #GAME_ID " + str(game.id)
        game.create()
        self.api.update_with_media(image_file, status)
        print(status)

    def resign(self, tweet):
        print("nothing yet ...")



def main():

    try:
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.secure = True
        auth.set_access_token(access_token, access_token_secret)

        api = API(auth)

        # If the authentication was successful, you should
        # see the name of the account print out
        #print(api.me().name)

        stream = Stream(auth, tweetchazzer(api))

        s = stream.userstream()
        #while True:
        #    s = stream.filter(track=['tweetchazzer'])
        #print(str(s))

    except BaseException as e:
        print("Error in main()" +str(e))


if __name__ == '__main__':
    main()
    
