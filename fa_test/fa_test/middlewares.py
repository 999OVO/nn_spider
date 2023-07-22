# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from fake_useragent import UserAgent
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from w3lib.http import basic_auth_header


class MyUserAgentMiddleware(UserAgentMiddleware):
    """
    class MyUserAgentMiddleware(UserAgentMiddleware):：这是一个自定义的User-Agent中间件类，它继承自Scrapy框架中的 UserAgentMiddleware 类。通过继承，我们可以覆盖或扩展原始的User-Agent中间件的行为，以满足我们的需求。

def process_request(self, request, spider):：这是 MyUserAgentMiddleware 类的一个方法，它在处理每个请求之前被调用。在Scrapy中，中间件的 process_request 方法可以用于在请求发送前对请求进行预处理。

request.headers['User-Agent'] = UserAgent(verify_ssl=False).random：这行代码将请求的User-Agent头部信息替换为一个随机的User-Agent字符串。具体来说：

UserAgent(verify_ssl=False)：UserAgent 是一个由第三方库 fake-useragent 提供的工具，用于生成随机的User-Agent字符串。在这里，它被实例化，并传递了 verify_ssl=False 参数。这个参数设置为False，表示在生成User-Agent时不会执行SSL证书验证。这通常是为了避免在部分环境中（例如一些不稳定的网络或代理环境）执行SSL验证时可能出现的问题。

UserAgent(verify_ssl=False).random：通过调用 random 方法，UserAgent 实例会随机选择一个User-Agent字符串。生成的User-Agent字符串会被赋值给请求的 headers 中的 User-Agent 字段，从而替换原始的User-Agent。

总结：这段代码通过使用 fake-useragent 库生成一个随机的User-Agent字符串，并将其设置为请求的User-Agent头部信息。这样做的目的是为了提高爬虫的匿名性和反爬虫抵御能力，因为使用不同的User-Agent可以使爬虫看起来更像不同的浏览器或设备，增加爬取的成功率。同时，设置 verify_ssl=False 参数是为了确保在生成User-Agent时避免执行SSL验证，以防止一些网络环境中可能出现的问题。
    """

    # def __init__(self, user_agent):
    #     self.user_agent = user_agent
    #
    # @classmethod
    # def from_crawler(cls, crawler):
    #     return cls(
    #         user_agent=crawler.settings.get('MY_USER_AGENT')
    #     )

    def process_request(self, request, spider):

        request.headers['User-Agent'] = UserAgent(verify_ssl=False).random

        # if 'products' in request.url:
        #     agent = random.choice(settings.MY_USER_PC_AGENT)
        #     request.headers['User-Agent'] = agent


class FaTestSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class FaTestDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
