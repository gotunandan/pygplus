

import facepy
import auth
import requests
from datetime import datetime, timedelta


class MyFB:

    def __init__(self, extended_token, extended_token_time, extended_token_flag):
        self.unix_time = datetime(1970, 1, 1)
        self.myAuth = auth.MyAuth()
        self.extended_token_flag = extended_token_flag
        self.extended_token = extended_token
        self.extended_token_time = self.unix_time + timedelta(seconds=extended_token_time)
        self.machine_id = self.myAuth.get_facebook_machine_id()

    def get_extended_token(self):
        expiry_time = int((self.extended_token_time - self.unix_time).total_seconds())
        return [self.extended_token, expiry_time, self.extended_token_flag]

    def generate_extended_token(self):
        link1 = "https://graph.facebook.com/oauth/client_code?" +\
            "access_token=" + self.extended_token +\
            "&client_secret=" + self.myAuth.get_facebook_app_secret() +\
            "&redirect_uri=" + self.myAuth.get_facebook_redirect_uri() +\
            "&client_id=" + self.myAuth.get_facebook_app_id()
        my_session = requests.Session()
        requested_data = my_session.get(link1).content
        print("Requested data is --- {}".format(requested_data))
        my_code = requested_data['code']

        link2 ="https://graph.facebook.com/oauth/access_token?" +\
            "code=" + my_code +\
            "&client_id=" + self.myAuth.get_facebook_app_id() +\
            "&redirect_uri=" + self.myAuth.get_facebook_redirect_uri() +\
            "&machine_id=" + self.machine_id
        my_session = requests.Session()
        requested_data = my_session.get(link2).content

        self.machine_id = requested_data['machine_id']
        self.extended_token = requested_data['access_token']
        self.extended_token_time = datetime.now() + timedelta(seconds=requested_data['expires_in'])
        self.extended_token_flag = 1

    def check_extended_token(self):
        time_now = datetime.now()
        days2_ahead = time_now + timedelta(days=10)
        print("datetime now is --- {}".format(time_now))
        print("datetime 2 days ahead is --- {}".format(days2_ahead))
        print("extended time is ---- {}".format(self.extended_token_time))
        if days2_ahead > self.extended_token_time:
            if self.extended_token_flag == 0:
                self.generate_extended_token()
            else:
                self.extended_token_flag = 0

    def post_to_fb(self, title, url, image_url, created_time, updated_time):
        print("Post to facebook called")
        self.check_extended_token()
        fb_graph = facepy.GraphAPI(self.extended_token)
        fb_update = title + '\n\n' + url
        fb_image = image_url
        fb_graph.post(
            'me/feed',
            message=fb_update,
            source=fb_image,
            created_time=created_time,
            updated_time=updated_time,
        )

