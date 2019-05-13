# ZhiHuSpider
自写爬虫爬取知乎问题及回答   

for python v 3.7


安装说明

一、安装scrapy

    1、安装wheel
        pip install wheel
    2、安装lxml
        https://pypi.python.org/pypi/lxml/4.1.0
    3、安装pyopenssl
        https://pypi.python.org/pypi/pyOpenSSL/17.5.0
    4、安装Twisted
        https://www.lfd.uci.edu/~gohlke/pythonlibs/
    5、安装pywin32
        https://sourceforge.net/projects/pywin32/files/
    6、安装scrapy
        pip install scrapy
        
二、安装其它依赖

    pip install qyquery
    
    pip install pymysql
    
    pip install selenium
    
    下载chrome版本对应的chromedriver http://npm.taobao.org/mirrors/chromedriver/  放置于 F:\chromedriver\chromedriver.exe
    
三、破解签名
    
    参考 ： https://mp.weixin.qq.com/s?__biz=MzU0NzY0NzQyNw%3D%3D&mid=2247484776&idx=1&sn=875c2decbf41b215ae2d564432ea89e6&chksm=fb4a7fc4cc3df6d2046eaaabed115e18daa4208eefccc0e86e3b02b073432e231cf0bd87cdad&xtrack=1&scene=0&subscene=131&clicktime=1550805130&ascene=7&d=
    
四、运行
    
    cd ZhihuSpider/zhihu
    scrapy crawl zhihu --nolog
    
https://www.lfd.uci.edu/~gohlke/pythonlibs


破解知乎加密方式：
    
    这几天卡在破解知乎的加密上，昨天终于把这个地方卡过去了 ^_^!! 累
    总共试了以下n种方式
    1、首先放弃把知乎的js加密函数通过python实现一遍，因为js代码都经过了混淆工具混淆，很难还原，直接放弃
    
    2、使用网上流传比较广的版本，也看到网上很多人推荐的，估计以前这种方法是可以的，即通过 pyexecjs 直接运行js代码，获取加密后的值，
    通过简单的修改之后，pyexecjs即可运行此js文件不报错，得到加密后的密文，然而很遗憾的是得到的密文与浏览器上运行的js密文不一致，
    经过一天调试无果吗，宣布放弃
    
    3、还是按照执行js脚本的思路，换了一个工具，使用 js2py 来运行js脚本，运行后发现直接报错，运行修改之前的js，发现不支持js中的 
    atob 函数，改成node版本的buff后，发现也不支持，宣告放弃
    
    4、使用selenium，使用谷歌助手打开本地网页文件的方式，获取js中的返回值，和2中一样，可以得到结果，但是chromedriver始终获取的
    结果与chrome不一致，本来以为是chromedriver只有32位版本的缘故，换用geckoxdriver（firefox） 64位版本重试，发现也是始终与
    直接通过firefox打开的结果不一致，放弃
    
    5、沿着4的思路，寻找直接调用浏览器的方法，使用webbrowser直接调用浏览器，然而很遗憾，这个api只提供打开网页，不能获取返回值，
    放弃
    
    6、返回使用selenium，发现直接通过chromedriver访问知乎网站也是不能登录的，即不是程序原因，而是知乎对driver做了限制，经过查
    找资料发现，通过driver打开的浏览器全局对象navigator会多一个属性webdriver的属性值，坑！网上的解决办法是在js中修改navigator
    的webdriver属性值，我相信这种办法之前是奏效的，因为很多人都有提到这种办法，Object.defineProperty(navigator, 'webdriver'
    , {get: () => undefined})); 很不幸的是这种方法已经不奏效的，大概是之前的判断条件是  navigator.webdriver != undefined
      现在是  'webdriver' in navigator，也就是说不管把这个值修改成undefined或者是false或者是null，都没有用了，in条件是都成
    立的，奈何本人js造诣太低，试了很多种办法都没办法重置这个内置对象navigator，然而原因是已经找到了，通过不断的百度，终于找到了
    解决方法，在调用selenium时候，加上几句代码即可以了（这里不得不吐槽一下，百度千篇一律的答案都是没有用的，真正有用的这个答案我是翻
    了七八页翻到的，逐条查看真是绝望！！！）
    
    至此终于把这个加密搞定了，后续可能打算把整个程序改一下，改成selenium直接调用知乎页面，登录之后再由python程序接管爬虫

