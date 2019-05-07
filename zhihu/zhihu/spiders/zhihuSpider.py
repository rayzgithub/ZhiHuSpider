# -*- coding: utf-8 -*-
import scrapy
import re
from zhihu.items import ZhihuQuestionItem, ZhihuAnswerItem
import json
from scrapy.utils.project import get_project_settings
from scrapy.http.cookies import CookieJar
import base64
import urllib
from urllib import parse
import random
import time
import os
from xml.sax.saxutils import unescape,escape
from pyquery import PyQuery as pq
import uuid
import execjs
import hmac

class ZhiHuSpider(scrapy.Spider):

    name = "zhihu"
    start_urls = ['https://zhihu.com']
    allowed_domains = ['www.zhihu.com']

    setting = get_project_settings()
    headers = setting['DEFAULT_REQUEST_HEADERS']
    post_data = setting['POST_DATA']
    question_count = setting['QUESTION_COUNT']
    answer_count = setting['ANSWER_COUNT_PER_QUESTION']
    answer_offset = setting['ANSWER_OFFSET']
    img_dir = setting['IMG_DIR']
    show_img_path = setting['SHOW_IMG_PATH']

    username = setting['ACCOUNT_USERNAME']
    password = setting['ACCOUNT_PASSWORD']

    login_header = {
        "content-type": "application/x-www-form-urlencoded",
        "x-zse-83" : "3_1.1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Referer': 'https://www.zhihu.com',
        'HOST': 'www.zhihu.com',
        ':authority': 'www.zhihu.com'
    }

    cookie_dict = {}

    # 验证码的文字位置都是固定的
    capacha_index = [
        [12.95, 14.969999999999998],
        [36.1, 16.009999999999998],
        [57.16, 24.44],
        [84.52, 19.17],
        [108.72, 28.64],
        [132.95, 24.44],
        [151.89, 23.380000000000002]
    ]

    # 翻页请求问题相关
    next_page = 'https://www.zhihu.com/api/v3/feed/topstory?action_feed=True&limit=10&' \
                'session_token={0}&action=down&after_id={1}&desktop=true'
    session_token = ''

    # 点击查看更多答案触发的url
    more_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data[*].is_normal,admin_closed_comment' \
                      ',reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_' \
                      'sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_conte' \
                      'nt,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,' \
                      'review_info,relevant_info,question,excerpt,relationship.is_authorized,is_author,v' \
                      'oting,is_thanked,is_nothelp;data[*].mark_infos[*].url;data[*].author.follower_cou' \
                      'nt,badge[?(type=best_answerer)].topics&offset={1}&limit={2}&sort_by=default'

    def start_requests(self):
        yield scrapy.Request('https://www.zhihu.com/signin?next=%2F', callback=self.login_zhihu)

    def login_zhihu(self, response):
        cookie_jar = CookieJar()
        cookie_jar.extract_cookies(response, response.request)
        for k, v in cookie_jar._cookies.items():
            for i, j in v.items():
                for m, n in j.items():
                    self.cookie_dict[m] = n.value
        """ 获取xsrf及验证码图片 """
        xsrf = self.cookie_dict['_xsrf']
        self.headers['X-Xsrftoken'] = xsrf
        self.post_data['_xsrf'] = xsrf

        # #是否填写验证码
        show_captcha_url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        yield scrapy.Request(show_captcha_url, callback=self.show_captcha)

    def show_captcha(self, response):
        "查看是否有验证图片"
        #转换json
        res_json = json.loads(response.body_as_unicode())
        is_show = res_json['show_captcha']
        if is_show:
            captcha_url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'

            yield scrapy.Request(url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn', method = 'PUT',headers = self.headers,callback = self.shi_bie)

        else:

            login_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'

            post_data = self.getEncryptData()

            yield scrapy.FormRequest(login_url, formdata=post_data, headers=self.login_header,callback=self.login_success)

    def shi_bie(self, response):
        try:
            img = json.loads(response.body)['img_base64']
        except Exception as e:
            print('获取img_base64的值失败，原因：%s' % e)
        else:
            print('成功获取加密后的图片地址')
            # 将加密后的图片进行解密，同时保存到本地
            img = img.encode('utf-8')
            img_data = base64.b64decode(img)
            with open('zhihu_captcha.GIF', 'wb') as f:
                f.write(img_data)

            captcha1,captcha2 = input('请输入倒立汉字的位置：').split(",")
            if int(captcha2) > 0:
                # 说明有两个倒立的汉字
                pass
                first_char = int(captcha1) - 1  # 第一个汉字对应列表中的索引
                second_char = int(captcha2) - 1  # 第二个汉字对应列表中的索引
                captcha = '{"img_size":[200,44],"input_points":[%s,%s]}' % (
                self.capacha_index[first_char], self.capacha_index[second_char])
            else:
                # 说明只有一个倒立的汉字
                pass
                first_char = int(captcha1) - 1
                captcha = '{"img_size":[200,44],"input_points":[%s]}' % (
                    self.capacha_index[first_char])

            data = {
                'input_text': captcha
            }
            yield scrapy.FormRequest(
                url='https://www.zhihu.com/api/v3/oauth/captcha?lang=cn',
                headers=self.headers,
                cookies=self.cookie_dict,
                formdata=data,
                callback=self.get_result
            )

    def get_result(self, response):
        try:
            yan_zheng_result = json.loads(response.body)['success']
        except Exception as e:
            print('关于验证码的POST请求响应失败，原因：{}'.format(e))
        else:
            if yan_zheng_result:
                print(u'验证成功')
                post_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
                post_data = self.getEncryptData()
                # 以上数据需要在抓包中获取
                yield scrapy.FormRequest(
                    url=post_url,
                    headers=self.headers,
                    formdata=post_data,
                    callback=self.index_page
                )
            else:
                print (u'是错误的验证码！')

    def login_success(self, response):
        if 'err' in response.text:
            print(response.text)
            print("error!!!!!!")
        else:
            print("successful!!!!!!")
            yield scrapy.Request('https://www.zhihu.com', headers=self.headers, dont_filter=True,encoding='utf-8')


    def getEncryptData(self):
        client_id = "c3cef7c66a1843f8b3a9e6a1e3160e20"
        grant_type = "password"
        timestamp = str(round(time.time() * 1000))
        source = "com.zhihu.web"
        #获取签名
        hash_key = "d1b964811afb40118a12068ff74a12f4"
        m = hmac.new(hash_key, digestmod="sha1")
        m = m.update(grant_type)
        m = m.update(client_id)
        m = m.update(source)
        m = m.update(timestamp)
        signature = m.hexdigest()

        username = self.username
        password = self.password
        captcha = ""
        lang = "cn"
        ref_source = "homepage"
        utm_source = ""
        # 读取js文件内容
        with open('F:\\pyscript\\ZhihuSpider\\zhihu\\zhihu\\js\\encrypt.js','r',errors='ignore') as f:
            jscode = f.read()

        ctx = execjs.compile(jscode)

        strs = "client_id=" + client_id + "&grant_type=" + grant_type + "&timestamp=" + timestamp + "&source=" + source + "&signature=" + signature + "&username=" + username + "&password=" + password + "&captcha=" + captcha + "&lang=" + lang + "&ref_source=" + ref_source + "&utm_source=" + utm_source
        # 调用js
        encrypt_data = ctx.call('b', strs)

        return encrypt_data


    def parse(self, response):
        """ 获取首页问题 """
        # /question/19618276/answer/267334062
        question_urls = response.xpath('//a[@data-za-detail-view-element_name="Title"]/@href').extract()

        question_urls = [parse.urljoin(response.url, url) for url in question_urls]
        print(question_urls)

        # # 翻页用到的session_token 和 authorization都可在首页源代码找到
        self.session_token = re.findall(r'session_token=([0-9,a-z]{32})', response.text)[0]
        # auto = re.findall(r'carCompose&quot;:&quot;(.*?)&quot', response.text)[0]
        # self.headers['authorization'] = 'Bearer ' + auto
        #
        # # 首页第一页问题
        for url in question_urls:
            question_detail = url
            yield scrapy.Request(question_detail, headers=self.headers, callback=self.parse_question)
        #
        # 获取指定数量问题
        n = len(question_urls)
        while n < self.question_count:
            yield scrapy.Request(self.next_page.format(self.session_token, n), headers=self.headers,
                                 callback=self.get_more_question)
            n += 10

    def saveimgs(self,img_url):
        """保存图片"""
        image_path = img_url.split('.')
        extension = image_path.pop()
        if extension in ['jpg','png','gif','jpeg']:
            if len(extension) > 3:
                extension = 'jpg'
            u = urllib.request.urlopen(img_url)
            data = u.read()
            # 上层目录 以日期命名
            parent_dir = str(time.strftime("%Y%m%d"))
            # 实际保存路径
            path = self.img_dir + parent_dir
            # 判断路径是否存在
            isExists = os.path.exists(path)
            if not isExists:
                os.makedirs(path)
            # 生成随机文件名
            # name = str(random.randint(1000000, 9999999))
            name = str(uuid.uuid4())
            file_name = path + '/' + name
            f = open(file_name + '.' + extension, 'wb')
            f.write(data)
            f.close()
            # 返回展示在网页的文件路径
            return self.show_img_path + parent_dir + '/' + name + '.' + extension
        else:
            return False

    def parse_question(self, response):
        """ 解析问题详情及获取指定范围答案 """
        item = ZhihuQuestionItem()

        item['name'] = response.xpath('//meta[@itemprop="name"]/@content').extract()[0]
        item['url'] = response.xpath('//meta[@itemprop="url"]/@content').extract()[0]
        item['keywords'] = response.xpath('//meta[@itemprop="keywords"]/@content').extract()[0]
        item['answer_count'] = response.xpath('//meta[@itemprop="answerCount"]/@content').extract()[0]
        item['comment_count'] = response.xpath('//meta[@itemprop="commentCount"]/@content').extract()[0]
        item['flower_count'] = response.xpath('//meta[@itemprop="zhihu:followerCount"]/@content').extract()[0]
        item['date_created'] = response.xpath('//meta[@itemprop="dateCreated"]/@content').extract()[0][0:19].replace('T',' ')

        count_answer = int(item['answer_count'])

        question_id = int(re.match(r'https://www.zhihu.com/question/(\d+)', response.url).group(1))

        item['question_id'] = question_id

        yield item



        # 从指定位置开始获取指定数量答案
        if count_answer > self.answer_count:
            count_answer = self.answer_count
        n = self.answer_offset
        while n + 20 <= count_answer:
            yield scrapy.Request(self.more_answer_url.format(question_id, n, n + 10), headers=self.headers,
                                 callback=self.parse_answer)
            n += 20

    def get_more_question(self, response):
        """ 获取更多首页问题 """
        question_url = 'https://www.zhihu.com/question/{0}'
        questions = json.loads(response.text)

        for que in questions['data']:
            question_id = re.findall(r'(\d+)', que['target']['question']['url'])[0]
            yield scrapy.Request(question_url.format(question_id), headers=self.headers,
                                 callback=self.parse_question)

    def parse_answer(self, response):
        """ 解析获取到的指定范围答案 """
        text = response.text
        answers = json.loads(text)

        for ans in answers['data']:
            item = ZhihuAnswerItem()
            item['answer_id'] = ans['id']
            item['question_id'] = ans['question']['id']
            item['author'] = ans['author']['name']
            # https://www.zhihu.com/question/266730428/answer/314851560
            item['ans_url'] = 'https://www.zhihu.com/question/' + str(item['question_id']) + '/answer/' + str(item['answer_id'])
            item['comment_count'] = ans['comment_count']
            item['upvote_count'] = ans['voteup_count']
            item['excerpt'] = ans['excerpt']
            if item['upvote_count'] > self.setting['MIN_UPVOTE_COUNT']:
                item['content'] = self.parse_content(ans['content'])
            item['content'] = ans['content']
            yield item

    def parse_content(self,content):
        # 反转义html
        content = unescape(content)
        # 使用pyquery解析html（类似js中jquery）
        # 知乎中所有图片被<figure></figure>标签嵌套而导致无法正常显示在页面
        d = pq(content)
        print(content)
        index = 0
        # 图片均由<figure></figure>此标签包裹
        for figure in d.items('figure'):
            # 获取figure中的img标签
            img = figure.find('noscript img')
            print(img)
            # 获取图片url
            src = pq(img).attr('src')
            # 获取保存后图片的本地url
            new_src = self.saveimgs(src)
            new_img = ''
            if new_src:
                    # 替换原来的图片链接
                    new_img = str(img).replace(src, new_src)
            print(new_img)
            content = content.replace(str(figure), new_img)
            index = index + 1
        # 返回值
        return content

    # def check_human(self,response):
    #     """解决知乎检测账号流量异常后的验证操作"""
    #     unhuman_captcha = response.xpath('//meta[@itemprop="name"]/@content').extract()
    #     #是否进入了 检测程序提交页面
    #     #https://www.zhihu.com/account/unhuman?type=unhuman&message=系统检测到您的帐号或IP存在异常流量，请进行验证用于确认这些请求不是自动程序发出的
    #     if len(unhuman_captcha) > 0 :
    #
    #
    #     else :
    #         # 否则返回true  接着爬
    #         return True





