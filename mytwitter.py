
import tweepy
import auth
import mylogger


class MyTwitter:

    def __init__(self):
        self.myAuth = auth.MyAuth()
        self.twitter_auth = tweepy.OAuthHandler(self.myAuth.get_twitter_consumer_key(), self.myAuth.get_twitter_consumer_secret())
        self.twitter_auth.set_access_token(self.myAuth.get_twitter_token(), self.myAuth.get_twitter_token_secret())
        self.twitter_client = tweepy.API(self.twitter_auth)
        self.logger = mylogger.MyLogger.setupLogger('mytwitter')

    def post_to_twitter(self, title, url, image):
        print("Post to twitter called")
        twitter_update = title[:100] + ' ' + url
        self.logger.debug("Twitter status update is --- {}".format(twitter_update))
        self.logger.debug("Attached image is --- {}".format(image))
        self.twitter_client.update_status(status=twitter_update)


