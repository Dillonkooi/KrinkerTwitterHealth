import config
import tweepy
import sqlalchemy
from models import Base, Follower
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime


class TwitterHealth(object):
    def __init__(self):
        # Connect to Twitter API
        auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_TOKEN_KEY, config.ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)

        # Get a DB session
        engine = sqlalchemy.create_engine(config.DB_URI)
        Base.metadata.create_all(engine)

        self.session = scoped_session(sessionmaker(bind=engine))

    def get_followers(self, screen_name):
        return self.api.followers_ids(screen_name)

    def get_friends(self, screen_name):
        return self.api.friends_ids(screen_name)

    def print_followers(self, screen_name):
        followers = self.get_followers(screen_name)
        for follower in followers:
            print self.api.get_user(follower).screen_name

    def check_followers_updates(self, screen_name):
        previous_followers = self.session.query(Follower).filter_by(is_following=True).all()
        previous_followers_ids = [follower.twitter_id for follower in previous_followers]
        current_followers = self.get_followers(screen_name)

        new_followers = []
        new_unfollowers = []

        for current_follower in current_followers:
            if current_follower not in previous_followers_ids:
                # New follower !
                new_followers.append(current_follower)
                follower = self.api.get_user(current_follower)
                print "[%s] Found a new follower : %s [%s] (#%d)" \
                      % (datetime.today().strftime('%d/%m %H:%M'), follower.name, follower.screen_name, follower.id)

                self.session.add(
                    Follower(
                        name=follower.name,
                        screen_name=follower.screen_name,
                        twitter_id=follower.id,
                        is_following=True,
                        last_following=datetime.now(),
                    )
                )

        # Discover the unfollowers
        for old_follower in previous_followers_ids:
            if old_follower not in current_followers:
                new_unfollowers.append(old_follower)
                # Unfollower!
                follower = self.api.get_user(current_follower)
                print "[%s] Found an unfollower : %s [%s] (#%d)" % \
                      (datetime.today().strftime('%d/%m %H:%M'), follower.name, follower.screen_name,
                       follower.id)
                old_follower.is_following = False

        # Close the session
        self.session.commit()
        self.session.close()

        if len(new_followers) == 0:
            print "no new followers"
        if len(new_unfollowers) == 0:
            print "no new unfollowers"

    def check_for_no_followbacks(self, screen_name):
        for f in self.get_friends(screen_name):
            if f not in self.get_followers(screen_name):
                print "Not follower backer {0}".format(self.api.get_user(f).screen_name)
                # print "Unfollow {0}?".format(self.api.get_user(f).screen_name)
                #if raw_input("Y/N?") == 'y' or 'Y':
                #    api.destroy_friendship(f)

if __name__ == '__main__':
    # TwitterHealth().check_followers_updates(config.SCREEN_NAME)
    TwitterHealth().check_for_no_followbacks(config.SCREEN_NAME)