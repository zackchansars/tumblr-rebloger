import tumblpy
from config import oauth_config, my_blog, blogs_info_name
import time
import json
import sys


def blog_url(name):
    if name is None:
        return None
    if 'tumblr.com' not in name:
        return '{}.tumblr.com'.format(name)
    return name


def dd(content):
    print(type(content))
    print(content)
    exit(1)


class Reblog:
    def __init__(self, client, name, blog_setting):
        self.client = client
        self.name = name
        self.blog_url = blog_url(name)
        self.offset = 0
        self.current_end_id = 0
        self.end_id, self.start_id, self.end = blog_setting
        self.set_my_blog(my_blog)

    def reblog(self):

        print('{} Start from {}!'.format(self.name, self.end_id))

        while True:
            posts = self.get_posts()

            if len(posts) <= 0:
                print('No Posts! Finish ' + self.name)
                self.end = True
                raise StopIteration

            for post in posts:

                if post['id'] <= self.end_id:
                    if self.end:
                        print('To End! Finish ' + self.name)
                        raise StopIteration
                    if post['id'] >= self.start_id:
                        print('pass post {}'.format(post['id']))
                        continue

                self.reblog_post(post)

                if self.start_id == 0:
                    self.start_id = post['id']

                if post['id'] > self.current_end_id:
                    self.current_end_id = post['id']

                if post['id'] < self.start_id:
                    self.start_id = post['id']

            yield max(self.current_end_id, self.end_id), self.start_id, self.end

    def blog_setting(self):
        return max(self.current_end_id, self.end_id), self.start_id, self.end

    def get_posts(self):
        res = self.client.posts(self.blog_url, kwargs={'offset': self.offset, 'limit': 20})
        posts = res['posts']
        self.offset += len(posts)
        print('current offset {} with total {}'.format(self.offset, res['blog']['total_posts']))
        return posts

    def reblog_post(self, post):
        if post['type'] in ['photo', 'video', 'audio', 'text']:
            res = self.client.post('post/reblog', self.my_blog,
                                   params={'reblog_key': post['reblog_key'], 'id': post['id']})
            print('reblog post {}'.format(post['id']))
        else:
            print('pass post {}'.format(post['id']))

    def get_blog_info(self):
        res = self.client.get('info', self.blog_url)
        return res['blog']

    def set_my_blog(self, my_blog):
        self.my_blog = my_blog


def reblog(blogs, reblog_to_blog):
    client = init_client()

    for blog_name in blogs.keys():
        reblog_a_blog(client, blogs, blog_name, reblog_to_blog)


def reblog_a_blog(client, blogs, blog_name, reblog_to_blog):
    try:
        blog_setting = blogs.get(blog_name)
        reblog = Reblog(client, blog_name, blog_setting)
        reblog.set_my_blog(reblog_to_blog)
        new_blog_setting = blog_setting
        try:
            while True:
                new_blog_setting = next(reblog.reblog())
                blogs.update(blog_name, new_blog_setting)
        except StopIteration:
            blogs.update(blog_name, reblog.blog_setting())
            # 163527529174, 162006355094, True
        print("Update for {}".format(blog_name))
    except tumblpy.exceptions.TumblpyError as e:
        if ('your daily post limit' in str(e)):
            blogs.update(blog_name, reblog.blog_setting())
            print(e)
            exit(1)
        else:
            print(e)


def init_client():
    client = tumblpy.Tumblpy(oauth_config['YOUR_CONSUMER_KEY'], oauth_config['YOUR_CONSUMER_SECRET'],
                             oauth_config['OAUTH_TOKEN'], oauth_config['OAUTH_TOKEN_SECRET'])
    return client


def delete_posts(total=10):
    counter = 0
    client = init_client()
    while counter < total:
        res = client.posts(my_blog, kwargs={'offset': counter, 'limit': 10})
        for post in res['posts']:
            res = client.post('post/delete', my_blog, params={'id': post['id']})
            print('deleted post {}'.format(res['id']))
            counter += 1
    print('deleted {}'.format(total))


class Blogs:
    def __init__(self, source='reblog_blogs_info.json'):
        self.source = source
        with open(source, 'r') as f:
            self.data = json.loads(f.read())

    def items(self):
        return [(blog_name, blog_setting) for blog_name, blog_setting in self.data.items()]

    def save(self):
        print('save blog info')
        with open(self.source, 'w') as f:
            f.write(json.dumps(self.data))

    def update(self, blog_name, value):
        print('update blog {} to {}'.format(blog_name, value))
        self.data[blog_name] = value
        self.save()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return self.data.get(item)

    def get(self, item):
        return self.data.get(item, [0, 0, False])


def format_info(source='reblog_blogs_info.json'):
    source = source
    with open(source, 'r') as f:
        blogs_info = json.loads(f.read())
        for blog_name, blog_info in blogs_info.items():
            if isinstance(blog_info, int):
                blogs_info[blog_name] = [blog_info, 0, False]
            elif isinstance(blog_info, list):
                blogs_info[blog_name] = [blog_info[0], blog_info[1], False]

    with open(source, 'w') as f:
        f.write(json.dumps(blogs_info))


def get_list_value(l, index):
    if len(l) > index:
        return l[index]
    return None


def dd_blog(blog_name):
    res = init_client().posts(blog_url(blog_name))
    print(res['blog']['total_posts'])
    print([(post['id'], post['slug']) for post in res['posts']])
    exit(1)


if __name__ == '__main__':

    blogs = Blogs(blogs_info_name)

    argv = sys.argv
    blog_name = get_list_value(argv, 1)

    if blog_name is not None:
        reblog_a_blog(init_client(), Blogs(), blog_name, my_blog)
    else:
        reblog(blogs, my_blog)

        # reblog('blog_info.json')
        # reblog('reblog_blog_info.json')
        # res = init_client().posts(my_blog, kwargs={'offset': 0, 'limit': 20})
        # dd(set([post['id'] for post in res['posts']]))
        # dd(set([post['trail'][0]['post']['id'] for post in res['posts']]))


        #
        # res = init_client().posts('zackchansars.tumblr.com')
        # dd(res['blog']['total_posts'])
        # dd([(post['slug'], post['type']) for post in res['posts']])

        # format_info()
