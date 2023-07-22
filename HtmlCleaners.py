import re
import unicodedata
from bs4 import BeautifulSoup, Comment
from string import punctuation
from scrapy.utils.project import get_project_settings
from bs4.element import NavigableString

def process_cleaned_data(html, **kwargs):
    """
    :param html: bs4数据源
    :param tags: 不删除的属性
    :param dtags: 删除的标签
    :return: 返回解析的文本
    """
    bs4_soup = BeautifulSoup(html, 'html.parser')
    settings = get_project_settings()
    tags = kwargs.get('tags') or settings.get('TAGS')
    dtags = kwargs.get('dtags') or settings.get('DTAGS')
    for ta in dtags:
        [e.extract() for e in bs4_soup(ta)]

    for element in bs4_soup(text=lambda text: isinstance(text, Comment)):
        element.extract()

    for i in bs4_soup():
        all_contents_list = i.contents

        if all_contents_list:
            for all_contents_list_index, one_contents in enumerate(all_contents_list):
                if isinstance(one_contents, NavigableString):
                    one_content = str(one_contents)
                    description_url_http_list = re.findall(r"(http[s]?.*?)[<\s]*$", one_content)
                    if description_url_http_list:
                        for one_url in description_url_http_list:
                            if ' ' in one_url:
                                print('http have space')
                                one_url_list = one_url.split()  # 使用空格作为分隔符将 one_url 拆分为 URL 列表
                                # 现在，one_no_space_url 表示没有任何空格的单个 URL
                                for one_no_space_url in one_url_list:
                                    # description_url_list = re.findall(r"(http[s]?://.*?)[<\s]*$", one_no_space_url)
                                    description_url_list = re.findall(r"(http[s]?.*?)[<\s]*$", one_no_space_url)
                                    if description_url_list:
                                        print("change text:{}".format(*description_url_list))
                                        for one_url in description_url_list:
                                            one_content = one_content.replace(one_url, '')
                            else:
                                print("change text:{}".format(*description_url_http_list))
                                for one_url in description_url_http_list:
                                    one_content = one_content.replace(one_url, '')
                    # 在one_content中定位url元素 <可能是标签
                    description_url_list = re.findall(r"([/]{0,2}www.*?)[<\s]*$", one_content)
                    if description_url_list:
                        for one_url in description_url_list:
                            if ' ' in one_url:
                                print('www have space')
                                one_url_list = one_url.split()
                                for one_no_space_url in one_url_list:
                                    # description_url_list = re.findall(r"(www.*?)[<\s]*$", one_no_space_url)
                                    description_url_list = re.findall(r"([/]{0,2}www.*?)[<\s]*$", one_no_space_url)
                                    if description_url_list:
                                        print("change text:{}".format(*description_url_list))
                                        for one_url in description_url_list:
                                            one_content = one_content.replace(one_url, '')
                            else:
                                print("change text:{}".format(*description_url_list))
                                one_content = one_content.replace(one_url, '')

                    all_contents_list[all_contents_list_index] = NavigableString(one_content)

                i.contents = all_contents_list

        local_attrs = i.attrs
        local_keys = [ele for ele in local_attrs.keys()]
        for key in local_keys:
            if kwargs.get('tags'):
                if key not in tags:
                    del i[key]

    texts = bs4_soup.getText().strip()
    if texts == "":
        return ""
    r = re.compile(r'[\W{}]+'.format(re.escape(punctuation)))
    s = [e for e in r.split(texts) if e]

    if len(s) < 10:
        return ""
    finally_str = bs4_soup.decode()
    finally_str = unicodedata.normalize('NFKC', finally_str)
    return finally_str


if __name__ == '__main__':
    html = '''<p class="span_flex_box">
    <span class="span_left">Fabric:</span>
    <span class="span_rigth">Polyester</span>
    </p><p class="span_flex_box">
    <span class="span_left">Season:</span>
    <span class="span_rigth">Summer</span>
    </p>
    <p class="span_flex_box">
    <span class="span_left">Trends:</span>
    <span class="span_rigth">Mono Sense</span>
    </p>
    <p class="span_flex_box">
    <span class="span_left">Element:</span>
    <span class="span_rigth">Lace，Pure Color，Patchwork</span>
    </p>
        '''
    tags = ['class', 'id']
    dtags = ['iframe', 'a', 'script', 'video', 'table', 'style', 'img']

    last_html = process_cleaned_data(html, tags=tags, dtags=dtags)
    print(last_html)
