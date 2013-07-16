#/usr/bin/python
#coding=utf8

import urllib2,urlparse
import os,sys,bs4,chardet,MySQLdb
import re 
from datetime import datetime
from HTMLParser import HTMLParser

class Crawl:
    """ Class Crawl crawl data from db.178.com """
    __data = ''
    __connect = ''
    __retryMax = 3

    def __init__(self):
        self.connect(c_host='localhost', c_user='root', c_passwd='root12')

    def request_url(self,url):
        try:
            request = urllib2.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) \ AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 ')
            return urllib2.urlopen(request)
        except CrawlError as e:
            return

    def write_file(self,file_name, content_list):
        file = open(file_name, 'w')
        for item in  content_list:
            file.write(item.prettify())
        file.close()

    def parse_web_page(self, cont, from_encoding='utf-8'):
        return bs4.BeautifulSoup(cont, from_encoding='utf-8')

    def connect(self, c_host, c_user, c_passwd):
        if not self.__connect:
            self.__connect = MySQLdb.connect(host=c_host, user=c_user, passwd=c_passwd)
            return self.__connect
        else:
            return self.__connect

    def output_log(self, msg):
        print "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "]\t" + msg

    def save_to_db(self, data):
        self.output_log("---\tsave to db...")
        self.__connect.select_db('weixin')
        cursor = self.__connect.cursor()
        cursor.execute("select id from wow_items where id = %s", data['id'])
        tmpResult = cursor.fetchall()

        if tmpResult:
            self.output_log("item " + data['id'] + " already exists! skip...")
            return
        insertData = [data['id'], data['name'], 0, 0, data['position'], data['attribute'], '']
        insertData += [data['quality'], data['qnumber'], data['img'], data['html']]
        cursor.execute("insert into wow_items values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", insertData)
        self.__connect.commit()
        del(cursor)
        self.output_log("---\tsave to db success!")
        return

    def crawl_item(self, url):
        self.__data = {}

        for i in range(1, self.__retryMax):
            self.output_log("crawling " + url + " ... retry:" + str(i))
            tmpCont = self.request_url(url)
            if not tmpCont :
                continue
            if tmpCont.readline() == 'no data':
                self.output_log("---\t no data")
                return

            tmpSoup = self.parse_web_page(tmpCont.read())
            bbCode = tmpSoup.find(id='bbcode_content')
            try :
                self.__data['img'] = re.compile(r'\[img\](.*)\[\/img\]').findall(bbCode.prettify())[0]
            except:
                self.__data['img'] =  ''
            try :
                self.__data['quality'] = re.compile(r'(\d)').findall(tmpSoup.find(id='item_detail').find('h2')['class'][0])[0]
            except:
                self.__data['quality'] =  ''
            try :
                self.__data['name'] = tmpSoup.find(id='item_detail').find('strong').text
            except:
                self.__data['name'] =  ''
            try :
                self.__data['id'] = re.compile(r'ID:([0-9]*)').findall(tmpSoup.find(id='item_detail').find('span').text)[0]
            except:
                self.__data['id'] =  ''
            try :
                self.__data['qnumber'] = tmpSoup.find(id='item_detail').find(id='ilv').text
            except:
                self.__data['qnumber'] =  ''
            try :
                self.__data['position'] = tmpSoup.find(id='item_detail').find('table').find('table').find('th').text
            except:
                self.__data['position'] =  ''
            try :
                self.__data['html'] = tmpSoup.find(id='main').find_all('div')[1].prettify()
            except:
                self.__data['html'] =  ''
            try :
                """ strip html tag """
                parser = HTMLParser()
                tmpList = []
                parser.handle_data = tmpList.append
                parser.feed(tmpSoup.find(id='item_detail').find(id='_dps').prettify().strip("\n"))
                parser.close()
                self.__data['attribute'] = ''.join(tmpList)
            except:
                self.__data['attribute'] = ''
            """ del temporary variables"""
            del(parser,tmpList,tmpSoup,bbCode,tmpCont)

            if not self.__data:
                continue

            return self.save_to_db(self.__data)

crawl = Crawl()
for num in range(1495, 100000):
    try :
        request_url = 'http://db.178.com/wow/cn/item/' + str(num) + '.html'
        crawl.crawl_item(url=request_url)
    except :
        print crawl.output_log('Exception! skip..')
