
import apiclient
import auth


class MyGPlus:

    last_post_id = ''

    def __init__(self, user_id):
        self.myAuth = auth.MyAuth()
        self.api_key = self.myAuth.get_gplus_key()
        self.user_id = user_id
        self.gplus_service = apiclient.discovery.build('plus', 'v1', developerKey=self.api_key)

    def connect(self, maxResults=5, nextPageToken=''):
        activities_resource = self.gplus_service.activities()
        activities_request = activities_resource.list(
            userId=self.user_id,
            collection='public',
            maxResults=maxResults,
            pageToken=nextPageToken,
        )
        print("Fetching {} public posts from G+".format(maxResults))
        activities_document = activities_request.execute()
        return activities_document

    def get_gplus_posts(self, last_post_id):
        print("get posts from gplus called")
        last_id = last_post_id
        my_activities = []
        oldNextPageToken = ''
        activities_document = self.connect(maxResults=10, nextPageToken=oldNextPageToken)
        while activities_document['nextPageToken']:
            if 'items' in activities_document:
                activities = activities_document['items']
                for activity in activities:
                    if activity['id'] == last_id:
                        print("Reached last_post_id, returning my_activities")
                        print("Number of new posts - {}".format(len(my_activities)))
                        if len(my_activities) == 0:
                            my_activities.append(activity)
                        return my_activities[::-1]
                    else:
                        my_activities.append(activity)
            oldNextPageToken = activities_document['nextPageToken']
            activities_document = self.connect(maxResults=10, nextPageToken=oldNextPageToken)
