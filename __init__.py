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
import re


sys.path.append(abspath(dirname(__file__)))

logger = getLogger(abspath(__file__).split('/')[-2])
__author__ = 'forslund'


def replace_specials(string):
    """ Replace special characters in string. """
    string = string.replace('&', 'and')
    string = string.replace('!', ' ')
    string = string.replace('.', ' ')
    string = string.replace('!', '')
    return string


def get_interesting_words(s):
    """ Isolate vers and nouns from the string and return them as list. """
    interesting_tags = ['NN', 'NNS', 'NNP', 'VBP', 'VB', 'VBP', 'JJ']
    return [w[0] for w in pos_tag(s.split()) if w[1] in interesting_tags]


def calc_rating(words, utterance):
    """ Rate how good a title matches an utterance. """
    rating = 0
    for w in words:
        if w.lower() in utterance.lower():
            rating += 1
    return rating


def clean_html(raw_html):
    """ Remove html tags from string. """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def get_best_matching_title(items, utterance):
    """ Check the items against the utterance and see which matches best. """
    item_rating_list = []
    for i in items:
        title = i.get('title', '')
        words = get_interesting_words(title)
        item_rating_list.append((calc_rating(words, utterance), i))
    return sorted(item_rating_list)[-1]


class RssSkill(MycroftSkill):
    def __init__(self):
        super(RssSkill, self).__init__('RssSkill')
        self.feeds = {}
        self.cached_items = {}
        self.cache_time = {}

    def cache(self, title, items):
        """ Add items to cache and set a timestamp for the cache."""
        self.cached_items[title] = items
        self.cache_time[title] = time.time()

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
                items = feed.get('items', [])
                self.cache(title, items)

            title = replace_specials(title)
            self.feeds[title] = url
            logger.info(title)
            self.register_vocabulary(title, 'TitleKeyword')

        intent = IntentBuilder('rssIntent')\
            .require('RssKeyword')\
            .require('TitleKeyword') \
            .build()
        self.register_intent(intent, self.handle_headlines)

        intent = IntentBuilder('readArticleIntent')\
            .require('ReadKeyword')\
            .build()
        self.register_intent(intent, self.handle_read)
        logger.debug('Intialization done')

    def handle_headlines(self, message):
        """Speak the latest headlines from the selected feed."""
        title = message.data['TitleKeyword']
        feed = feedparser.parse(self.feeds[title])
        items = feed.get('items', [])

        if len(items) > 3:
            items = items[:3]
        self.cache(title, items)

        self.speak('Here\'s the latest headlines from ' +
                   message.data['TitleKeyword'])
        for i in items:
            logger.info('Headline: ' + i['title'])
            self.speak(i['title'])
            time.sleep(5)

    def get_items(self, name):
        """
            Get items from the named feed, if cache exists use cache otherwise
            fetch the feed and update.
        """
        cache_timeout = self.config.get('cache_timeout', 10) * 60
        cached_time = float(self.cache_time.get(name, 0))

        if name in self.cached_items \
                and (time.time() - cached_time) < cache_timeout:
            logger.debug('Using cached feed...')
            return self.cached_items[name]
        else:
            logger.debug('Fetching feed and updating cache')
            feed = feedparser.parse(self.feeds[name])
            feed_items = feed.get('items', [])
            self.cache(name, feed_items)

            if len(feed_items) > 5:
                return feed_items[:5]
            else:
                return feed_items

    def handle_read(self, message):
        """
            Find and read a feed item summary that best matches the
            utterance.
        """
        utterance = message.data.get('utterance', '')
        items = []
        for f in self.feeds:
            items += self.get_items(f)
        best_match = get_best_matching_title(items, utterance)

        logger.debug("Reading " + best_match[1]['title'])
        if best_match[0] != 0:
            self.speak(clean_html(best_match[1]['summary']))


def create_skill():
    return RssSkill()
