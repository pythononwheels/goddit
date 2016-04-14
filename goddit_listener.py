import os
import sys
import json
import pprint
import datetime

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy import API
from tweepy.streaming import StreamListener

from goddit_app_token import *
from models.tweet import Tweet

pp = pprint.PrettyPrinter(indent=4)
import logging

class goddit_listener(StreamListener):
    '''
        listens to the twitter stream and handles the requests.

    '''
    def __init__( self, api=None, logger=None):
        self.tweetCount = 0
        self.api = api
        self.logger = logger or logging.getLogger(__name__)
        #print(str(self.log))

    def on_connect( self ):
        #print("Connection established.")
        self.logger.info("Connection established.")

    def on_disconnect( self, notice ):
        print("Connection lost.")
        self.logger.info( "..disconnected " +  str(notice), level="ERROR")

    def on_data( self, status ):
        """
            handle all twwets, replys and direct messages
        """
        self.logger.info("DATA:: "+str(status))


    def on_direct_message( self, status ):
        self.logger.info("DM:: " + str(status))

    def on_error( self, status_code ):
        """
            twitter stream on error handler
        """
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
        pass

    def tweet_error(self, msg, receipient, image=None):
        """
            send an error message as tweet to receipient
        """
        self.logger.error(msg)
        api.update( "@{} ".format(receipient.strip()) + msg)





def main():

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create a file handler

    handler = logging.FileHandler('goddit.log')
    handler.setLevel(logging.INFO)

    # create a logging format

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger

    logger.addHandler(handler)

    try:
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.secure = True
        auth.set_access_token(access_token, access_token_secret)

        api = API(auth)

        # If the authentication was successful, you should
        # see the name of the account print out
        #print(api.me().name)

        stream = Stream(auth, tweetchazzer(api=api, logger=logger))

        s = stream.userstream()
        #while True:
        #    s = stream.filter(track=['tweetchazzer'])
        #print(str(s))

    except BaseException as e:
        print("Error in main()" +str(e))


if __name__ == '__main__':
    main()
