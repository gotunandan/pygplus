
import argparse
import json
import signal
import sys
import logging
import mylogger
import mygplus
import mytwitter
import myfb
from apscheduler.schedulers.blocking import BlockingScheduler


logging.basicConfig()
LAST_POST_ID = ''
FB_EXTENDED_TOKEN = ''
FB_EXTENDED_TOKEN_TIME = 0


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('conf')
    args = parser.parse_args()
    return args


def fetch_and_post(gplus_user_id):
    '''Fetching google plus posts
    and posting them to twitter and facebook
    '''

    global LAST_POST_ID
    global FB_EXTENDED_TOKEN
    global FB_EXTENDED_TOKEN_TIME
    my_logger = mylogger.MyLogger.setupLogger('fetch_and_post')
    print("LAST_POST_ID is - {}".format(LAST_POST_ID))

    try:
        my_gplus = mygplus.MyGPlus(gplus_user_id)
        my_activites = my_gplus.get_gplus_posts(LAST_POST_ID)
    except Exception as errObj:
        print("Error fetching posts from Google+")
        print(errObj)

    print("Got my_activites - {}".format(len(my_activites)))

    if LAST_POST_ID == my_activites[-1]['id']:
        print("LAST_POST_ID is the same as before - {}".format(LAST_POST_ID))
        print("Not posting again till new posts arrive\n")
        return
    else:
        LAST_POST_ID = my_activites[-1]['id']
        print("Last post id updated to - {}".format(LAST_POST_ID))

    my_twitter = mytwitter.MyTwitter()
    print("Extended token is --- {}".format(FB_EXTENDED_TOKEN))
    print("Extended time is --- {}".format(FB_EXTENDED_TOKEN_TIME))
    my_fb = myfb.MyFB(FB_EXTENDED_TOKEN, FB_EXTENDED_TOKEN_TIME)

    for activity in my_activites:
        print("\n--------STARTING --------")
        title = activity['title']
        url = activity['url']
        created_time = activity['published']
        updated_time = activity['updated']
        my_logger.debug("attachments[0] --- {}".format(activity['object']['attachments'][0].get('fullImage', 'NOIMAGE')))

        if activity['object'].get('attachments', '') == '':
            print("No attachments found !")
            url_image = ''
        else:
            print("Attachments, found, trying to get fullImage...")
            if activity['object']['attachments'][0].get('fullImage', '') == '':
                url_image = ''
                print("Attached image NOT found, using empty url")
            else:
                url_image = activity['object']['attachments'][0]['fullImage']['url']
                print("Attached image found")
                my_logger.debug("Attached image is - {}".format(url_image))

        print(title)
        print(url)
        print(url_image)
        try:
            my_twitter.post_to_twitter(title, url, url_image)
        except Exception as errObj:
            print("Error posting to Twitter")
            print(errObj)

        try:
            my_fb.post_to_fb(title, url, url_image, created_time, updated_time)
        except Exception as errObj:
            print("Error posting to Facebook")
            print(errObj)

        print("--------ENDING --------\n")

    FB_EXTENDED_TOKEN, FB_EXTENDED_TOKEN_TIME = my_fb.get_extended_token()


def main():
    '''main method'''
    args = parseArgs()
    config_file = args.conf

    global LAST_POST_ID
    global FB_EXTENDED_TOKEN
    global FB_EXTENDED_TOKEN_TIME

    with open(config_file) as json_file:
        json_data = json.load(json_file)

    FB_EXTENDED_TOKEN = json_data['facebook_extended_token']
    FB_EXTENDED_TOKEN_TIME = json_data['facebook_extended_token_time']
    LAST_POST_ID = json_data['last_post_id']
    time_interval = int(json_data['interval'])
    gplus_user_id = json_data['gplus_user_id']


    main_logger = mylogger.MyLogger.setupLogger('mainclient')
    print("Last post id from args is - {}".format(LAST_POST_ID))
    my_scheduler = BlockingScheduler(timezone='UTC')
    my_scheduler.add_job(
        fetch_and_post,
        'interval',
        minutes=time_interval,
        args=[gplus_user_id],
        id='posts'
    )
    my_scheduler.start()

def signal_handler(signal, frame):
    args = parseArgs()
    config_file = args.conf
    print("\nWriting last_post_id - {} to {}".format(LAST_POST_ID, config_file))
    with open(config_file) as json_file:
        json_data = json.load(json_file)
    json_data['last_post_id'] = LAST_POST_ID
    json_data['facebook_extended_token'] = FB_EXTENDED_TOKEN
    json_data['facebook_extended_token_time'] = FB_EXTENDED_TOKEN_TIME
    with open(config_file, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    print("\nCaught signal - {} and frame - {}".format(signal, frame))
    print("Quitting...")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
