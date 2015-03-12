from xbmcswift2 import xbmcgui
from YogaGloCore import YogaGloCore
from BeautifulSoup import BeautifulSoup
import urlparse


class YogaGloApi(YogaGloCore):

    yg_urls = {
        'domain': 'www.yogaglo.com',
        'login': 'https://www.yogaglo.com/login',
        'mypractice': 'https://www.yogaglo.com/mypractice',
        'cloud_images': 'https://d23upc69c85y6r.cloudfront.net/300/',
        'cloud_thumbs': 'https://d3sywv2955jo7z.cloudfront.net/',
        'teacher_avatars': 'https://s3.amazonaws.com/yg-app-prod-assets/1.2.6/img/teachers/'
    }

    def __init__(self, plugin):
        YogaGloCore.__init__(self, plugin)
        self.logged_in = False
        self.dialog = xbmcgui.Dialog()
        self._login()
        self.headers = {
            'Referer': 'https://www.yogaglo.com',
            'X-Requested-With': 'XMLHttpRequest', 'Host': 'www.yogaglo.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:36.0) Gecko/20100101 Firefox/36.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X_AUTHENTICATION_TOKEN': self.x_auth_token,
            'Connection': 'keep-alive'
        }

    def myqueue(self, url):
        response = self.session.get(url, headers=self.headers)

        videos = [vids['video'] for vids in response.json()['queue']]
        return [self._playable_list_item(video) for video in videos]

    def myhistory(self, url):
        payload = {'start': '0', 'limit': '24'}
        response = self.session.get(url, headers=self.headers, params=payload)

        videos = [vids['video'] for vids in response.json()['history']]
        return [self._playable_list_item(video) for video in videos]

    def teachers_followed(self, url):
        payload = {'method': 'my_teachers'}
        response = self.session.get(url, headers=self.headers, params=payload)
        items = []
        for t in response.json()['followupteacher']:
            item = {
                'label': ' '.join([t[key] for key in ['first_name',
                                                      'last_name']]),
                'path': t['idteacher'],
                'icon': urlparse.urljoin(self.yg_urls['teacher_avatars'],
                                         t['idteacher'] + '-avatar.jpg')
            }
            items.append(item)

        return items

    def following_videos(self, url):
        payload = {'method': 'get_videos', 'start': '0', 'limit': '24'}
        response = self.session.get(url, headers=self.headers, params=payload)

        videos = [vids['video'] for vids in response.json()['followupteacher']]
        return [self._playable_list_item(video) for video in videos]

    def teacher_videos(self, url, teacher_id):
        payload = {'method': 'getVideos', 'teacher': teacher_id,
                   'start': '0', 'limit': '12'}
        response = self.session.get(url, headers=self.headers, params=payload)

        return [self._playable_list_item(video) for video in response.json()['video']]

    def _playable_list_item(self, video):
        return {
            'label': video['title'],
            'label2': ' '.join([video[key] for key in ["style", "level"]]),
            'path': video['video_url']['1200p'],  # actual video
            'is_playable': True,
            'icon': urlparse.urljoin(self.yg_urls['cloud_images'],
                                     video['preview_images'][0]),
            'thumbnail': urlparse.urljoin(self.yg_urls['cloud_thumbs'],
                                          video['thumbnail_image']),
            'info_type': 'video',
            'info': {
                'title': video['title'],
                'plot': video['description'],
                'plotoutline': video['short_description'],
                'duration': video['durationMin'],
                'tagline': ' '.join(
                    [video['teacher'][key] for key in ["first_name",
                                                       "last_name"]]),
                'genre': 'Yoga'},
            'stream_info': {'video': {'duration': video['durationSeconds']}}}

    def _login(self):
        if not self.cookie_expired:  # still logged on -- no expiration
            self.logged_in = True
            return

        email = self.plugin._addon.getSetting('email')
        password = self.plugin._addon.getSetting('password')
        self.plugin.log.debug("yogaglo -> logging on with email '%s' and password '%s'" % (email, password))

        if not email or not password:
            self.plugin.log.debug("yogaglo -> credentials look empty!")
            self.dialog.notification('Yogaglo', 'Credentials appear empty!',
                                     xbmcgui.NOTIFICATION_INFO, 5000, True)
            return

        # login process commences
        payload = {'email': email, 'password': password}
        response = self.session.post(self.yg_urls['login'],
                                     params=payload)

        # successful if redirected to new url muypractice
        if response.url == self.yg_urls['mypractice']:
            self.logged_in = True
            self.session.cookies.save()
            soup = BeautifulSoup(response.text)
            x_auth_token = soup.find(id='user')['data-access_token']
            self._save_x_authenicaiton_token(x_auth_token)
            self.plugin.log.debug("yogaglo -> successful login!")
        else:
            self.plugin.log.debug("yogaglo -> couldn't login, bad credentials!")
            self.dialog.notification(
                'Yogaglo', 'Could not log in due to incorrect credentials!',
                xbmcgui.NOTIFICATION_INFO, 5000, True)
