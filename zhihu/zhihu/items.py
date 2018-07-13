# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ZhihuItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()


class ZhihuQuestionItem(scrapy.Item):

    name = scrapy.Field()
    url = scrapy.Field()
    keywords = scrapy.Field()
    answer_count = scrapy.Field()
    comment_count = scrapy.Field()
    flower_count = scrapy.Field()
    date_created = scrapy.Field()
    question_id = scrapy.Field()


class ZhihuAnswerItem(scrapy.Item):

    question_id = scrapy.Field()
    answer_id = scrapy.Field()
    author = scrapy.Field()
    ans_url = scrapy.Field()
    comment_count = scrapy.Field()
    upvote_count = scrapy.Field()
    excerpt = scrapy.Field()
    content = scrapy.Field()
