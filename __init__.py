import sys
from os.path import dirname, abspath, basename
import subprocess

from mycroft.skills.core import MycroftSkill
from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message

import time
import feedparser

import os
from os.path import dirname
from mycroft.util.log import getLogger

from nltk import pos_tag

sys.path.append(abspath(dirname(__file__)))

logger = getLogger(abspath(__file__).split('/')[-2])
__author__ = 'forslund'


def replace_specials(string):
    string = string.replace('&', 'and')
    return string


def get_interesting_words(s):
    interesting_tags = ['NN', 'NNS', 'NNP', 'VBP', 'VB', 'VBP', 'JJ']
    return [w[0] for w in pos_tag(s.split(' ')) if w[1] in interesting_tags]


def calc_rating(words, utterance):
    rating = 0
    for w in words:
        if w.lower() in utterance.lower():
            rating += 1
    return rating

import re

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class RssSkill(MycroftSkill):
    def __init__(self):
        super(RssSkill, self).__init__('RssSkill')
        self.feeds = {}

    def initialize(self):
        urls = []
        if self.config:
            urls = self.config.get('feeds', [])
        else:
            logger.warning("No config for " + self.name + "exists")
        if len(urls) == 0:
            logger.warning('No feeds loaded')

        for url in urls:
            if type(url) == list:
                title = url[0]
                url = url[1]
            else:
                feed = feedparser.parse(url)
                title = feed['channel']['title']
            title = replace_specials(title)
            self.feeds[title] = url
            logger.info(title)
            self.register_vocabulary(title, 'TitleKeyword')

        intent = IntentBuilder('rssIntent')\
                 .require('RssKeyword')\
                 .require('TitleKeyword') \
                 .build()
        self.register_intent(intent, self.titles)
        

        intent = IntentBuilder('readArticleIntent')\
                 .require('ReadKeyword')\
                 .build()
        self.register_intent(intent, self.read)

    def titles(self, message):
        feed = feedparser.parse(self.feeds[message.data['TitleKeyword']])
        items = feed.get('items', [])
        if len(items) > 3:
            items = items[:3]
        self.speak('Here\'s the latest headlines from ' + message.data['TitleKeyword'])
        for i in items:
            self.speak(i['title'])
            time.sleep(5)

    def read(self, message):
        utterance = message.data.get('utterance', '')
        items = []
        for f in self.feeds:
            feed = feedparser.parse(self.feeds[f])
            feed_items = feed.get('items', [])
            items += feed_items[:5]
        item_rating_list = []
        for i in items:
            title = i.get('title', '')
            words = get_interesting_words(title)
            item_rating_list.append((calc_rating(words, utterance), i))
        best_match = sorted(item_rating_list)[-1]
        logger.debug("Reading " + best_match[1]['title'])
        if best_match[0] != 0:
            self.speak(clean_html(best_match[1]['summary']))


def create_skill():
    return RssSkill()
