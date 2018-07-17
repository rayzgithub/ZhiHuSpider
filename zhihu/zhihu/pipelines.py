# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from scrapy.utils.project import get_project_settings


class ZhihuPipeline(object):

    def __init__(self):

        self.settings = get_project_settings()
        self.connect = pymysql.connect(
            host=self.settings['MYSQL_HOST'],
            db=self.settings['MYSQL_DBNAME'],
            user=self.settings['MYSQL_USER'],
            passwd=self.settings['MYSQL_PASSWD'],
            charset=self.settings['MYSQL_CHARSET'],
            use_unicode=True
        )
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):

        if item.__class__.__name__ == 'ZhihuQuestionItem':
            sql = 'insert into wordpress.zhihu_question(name,url,keywords,answer_count,' \
                  'flower_count,comment_count,date_created,question_id) values (%s,%s,%s,%s,%s,%s,%s,%s)'
            self.cursor.execute(sql, (item['name'], item['url'], item['keywords'], item['answer_count'],
                                      item['flower_count'], item['comment_count'], item['date_created'], item['question_id']))
        else:
            if item['upvote_count'] > self.settings['MIN_UPVOTE_COUNT']:
                sql = 'insert into wordpress.zhihu_answer(question_id,answer_id,author,ans_url,upvote_count,comment_count,excerpt,content)'\
                      'values (%s,%s,%s,%s,%s,%s,%s,%s)'
                self.cursor.execute(sql, (item['question_id'],item['answer_id'],item['author'], item['ans_url'], item['upvote_count'],
                                          item['comment_count'], item['excerpt'],item['content']))
        self.connect.commit()
