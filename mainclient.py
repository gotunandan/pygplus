
import argparse
import json
import signal
import sys
import logging
import mygplus
import mytwitter
import myfb
from apscheduler.schedulers.blocking import BlockingScheduler


logging.basicConfig()
LAST_POST_ID = ''
FB_EXTENDED_TOKEN = ''
FB_EXTENDED_TOKEN_TIME = 0
FB_EXTENDED_TOKEN_FLAG = 0


def parseArgs():
    '''parse the args'''

    parser = argparse.ArgumentParser()
    parser.add_argument('conf')
    args = parser.parse_args()
    return args

def parse_gplus_data(one_activity):
    '''parse gplus data to get image'''

    title = one_activity['title']
    url = one_activity['url']
    url_image = ''
    created_time = one_activity['published']
    updated_time = one_activity['updated']

    object_type = one_activity['object'].get('objectType', 'NULL')
    print("Object type is --- {}".format(object_type))
    if object_type == 'activity':
        if one_activity.get('annotation', '') == '':
            print('No annotation found, doing nothing')
        else:
            title = ' '.join([one_activity['annotation'], '-', title])
            print('Annotation found, adding as prefix to title')

    if one_activity['object'].get('attachments', '') == '':
        print("No attachments found !")
        url_image = ''
    else:
        attachment_type = one_activity['object']['attachments'][0].get('objectType', 'NULL')
        print("Attachment type is --- {}".format(attachment_type))
        print("Attachments, found, trying to get an image...")
        type_of_post = {
            "article":[
                one_activity['object']['attachments'][0].get('fullImage',''),
            ],
            "video": [
                one_activity['object']['attachments'][0].get('image',''),
            ],
            "photo": [
                one_activity['object']['attachments'][0].get('fullImage',''),
            ],
            "album": [
                one_activity['object']['attachments'][0].get('thumbnails',''),
            ],
        }

        if one_activity['object']['attachments'][0].get('url', '') == '':
            print("No url found to add to title")
        else:
            print("URL found, appending to title")
            title = ' '.join([title, one_activity['object']['attachments'][0].get('url', '')])

        post_type = type_of_post[attachment_type]
        if post_type == '':
            url_image = ''
            print("Attached image NOT found, using empty url")
        else:
            print("Attached image found")
            if attachment_type == 'video':
                url_image = one_activity['object']['attachments'][0]['image']['url']
            elif attachment_type == 'album':
                url_image = one_activity['object']['attachments'][0]['thumbnails'][0]['image']['url']
            else:
                ### else includes attachment_type for article/photo and everything else
                if one_activity['object']['attachments'][0].get('fullImage','') == '':
                    url_image = ''
                    print("full image not found")
                else:
                    url_image = one_activity['object']['attachments'][0]['fullImage']['url']
                    print("full image found")

    return [title, url, url_image, created_time, updated_time]


def fetch_and_post(gplus_user_id):
    '''Fetching google plus posts
    and posting them to twitter and facebook
    '''

    global LAST_POST_ID
    global FB_EXTENDED_TOKEN
    global FB_EXTENDED_TOKEN_TIME
    global FB_EXTENDED_TOKEN_FLAG
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
    print("Extended FLAG is --- {}".format(FB_EXTENDED_TOKEN_FLAG))
    my_fb = myfb.MyFB(FB_EXTENDED_TOKEN, FB_EXTENDED_TOKEN_TIME, FB_EXTENDED_TOKEN_FLAG)

    for activity in my_activites:
        print("\n--------STARTING --------")
        title, url, url_image, created_time, updated_time = parse_gplus_data(activity)

        print(title)
        print(url)
        print(url_image)
        try:
            my_twitter.post_to_twitter(title, url, url_image)
            print("Twitter post done")
        except Exception as errObj:
            print("Error posting to Twitter")
            print(errObj)

        try:
            my_fb.post_to_fb(title, url, url_image, created_time, updated_time)
            print("facebook post done")
        except Exception as errObj:
            print("Error posting to Facebook")
            print(errObj)
            print(sys.exc_info())
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            exc_info = sys.exc_info()
        finally:
            print("finally done")
            # Display the *original* exception
            # traceback.print_exception(*exc_info)
            # del exc_info

        print("--------ENDING --------\n")

    FB_EXTENDED_TOKEN, FB_EXTENDED_TOKEN_TIME, FB_EXTENDED_TOKEN_FLAG = my_fb.get_extended_token()


def main():
    '''main method'''
    args = parseArgs()
    config_file = args.conf

    global LAST_POST_ID
    global FB_EXTENDED_TOKEN
    global FB_EXTENDED_TOKEN_TIME
    global FB_EXTENDED_TOKEN_FLAG

    with open(config_file) as json_file:
        json_data = json.load(json_file)

    FB_EXTENDED_TOKEN = json_data['facebook_extended_token']
    FB_EXTENDED_TOKEN_TIME = json_data['facebook_extended_token_time']
    FB_EXTENDED_TOKEN_FLAG = json_data['facebook_extended_token_flag']
    LAST_POST_ID = json_data['last_post_id']
    time_interval = int(json_data['interval'])
    gplus_user_id = json_data['gplus_user_id']

    print("Last post id from args is - {}".format(LAST_POST_ID))
    fetch_and_post(gplus_user_id)
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
