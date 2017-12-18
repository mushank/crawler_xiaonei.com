# -*- coding: utf-8 -*-

import os
import re
import ConfigParser
import requests
from lxml import html

def get_config():
    config = ConfigParser.RawConfigParser()
    config.read('config.ini')

    return config

#  prefix album url address for specific user
def get_url(config):
    person_dict = {}

    url_prefix = 'http://photo.renren.com/photo/'
    rid_list = config.options('person')
    for rid in rid_list:
        person_dict[rid] = url_prefix + rid.strip() + '/albumlist/v7'

    return person_dict
            
# package http headers
def get_headers(config):
    headers = {
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding' : 'gzip, deflate, sdch',
        'Accept-Language' : 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ru;q=0.2,fr;q=0.2,ja;q=0.2',
        'Cache-Control' : 'max-age=0',
        'Connection' : 'keep-alive',
        'Host' : 'www.renren.com',
        'RA-Sid' : 'DAF1BC22-20140915-034057-065a39-2cb2b1',

        'RA-Ver' : '2.10.4',
        'Referer' : 'http://www.renren.com/SysHome.do',
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
    }

    # fetch cookie from config file
    headers['Cookie'] = config.get('cookie', 'cookie')
    
    return headers

def request(url, headers):
    response = requests.get(url, headers=headers)
    return response

def get_albums(response):
    parsed_body = html.fromstring(response.text)
    js = parsed_body.xpath('//script/text()')
    js = map(lambda x : x.encode('utf-8'), js)
    
    album_js = js[3]
    album_raw = re.findall(r"'albumList':\s*(\[.*?\]),", album_js)[0]
    album_list = eval(album_raw)
    
    album_url_dict = {}
    for album in album_list: 
        if album['sourceControl'] == 99:  # If authorized
            album_url = 'http://photo.renren.com/photo/'
            album_url = album_url + str(album['ownerId']) + '/'
            album_url = album_url + 'album-' + album['albumId'] + '/v7'

            album_url_dict[album['albumId']] = {}
            album_url_dict[album['albumId']]['album_url'] = album_url
            album_url_dict[album['albumId']]['photo_count'] = album['photoCount']
            album_url_dict[album['albumId']]['album_name'] = album['albumName']

    return album_url_dict

def get_imgs(album_url_dict, headers):
    img_dict = {}

    for key, val in album_url_dict.iteritems():
        album_url = val['album_url']
        response = request(album_url, headers)
        parsed_body = html.fromstring(response.text)
        js = parsed_body.xpath('//script/text()')
        text = js[3].encode('utf-8')
        image_list = re.findall(r'"url":"(.*?)"', text)
        img_dict[key] = image_list

    return img_dict

def download_img(img_dict, album_url_dict, start_dir):
    for album_id, image_list in img_dict.iteritems():
        cur_dir = start_dir + album_url_dict[album_id]['album_name'].replace(' ', '_')
        
        if not os.path.exists(cur_dir):
            os.makedirs(cur_dir)

        image_list = map(lambda x: x.replace('\\', ''), image_list)

        for url in image_list:
            print(url + "  start!")
            response = requests.get(url, headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36'})
            print(response.status_code)

            with open(cur_dir + '/' + url.split('/')[-1], 'wb') as f:
                f.write(response.content)

    
# main function
def main():
    config = get_config()
    headers = get_headers(config)
    url_dict = get_url(config)
    
    for rid, url in url_dict.iteritems():
        name = config.get('person', rid)
        print('start downloading' + ' ' + name + '\'s albums!')
        print('----------------------------------------')
        start_dir = config.get('dir', 'start_dir') + name + '/'
        response = request(url, headers)
        album_url_dict = get_albums(response)
        img_dict = get_imgs(album_url_dict, headers)
        download_img(img_dict, album_url_dict, start_dir)
        print('----------------------------------------')
        print('end downloading!')
        print 

# program entrance
if __name__ == '__main__':
    main()


