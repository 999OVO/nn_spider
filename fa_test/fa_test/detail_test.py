import re
import json
import requests
from lxml import etree
import random
import pprint

response = requests.get(url="https://fabrikstyle.com/products/lori-shoulder-tie-printed-maxi-dress")
tree = etree.HTML(response.text)
product_data = tree.xpath('//*[@id="shopify-section-template--14584073289786__main"]/div/script')[0].text
product_data = json.loads(product_data)
pprint.pprint(product_data)
# product_data = re.findall(r'sgGlobalVars.currentProduct = ([\s\S]*)};', response.text)

# product_data = json.loads(product_data[0])

product_title = product_data['title']
# print(product_data['title'])

flag = False

item = dict()
item["product_title"] = ' '.join(product_title.split(" ")[-1:])
# item["description"] = response.xpath('//div[@id="tab1"]').extract_first()
item["description"] = tree.xpath('//div[@id="tab1"]//text()')
item["description"] = ' '.join(item["description"])
p_desc = ' '.join(tree.xpath('//div[@id="tab1"]/p[1]//text()'))
item["description"] = item["description"].replace(p_desc, '')
print(item["description"])

for ele in tree.xpath('//div[@id="tab1"]/p'):
    if 'Please note, this item is final sale' in ele:
        item["description"] = item["description"].replace(ele, '')
# 如果item字典中不存在该键，会引发“KeyError”，所以要用条件表达式捕获异常
# item["description"] = process_cleaned_data(item["description"]).replace('\n', '') if item["description"] else ''
item["image_urls"] = product_data['images']
item["image_urls"] = ['https:' + ele.split('?')[0] for ele in item["image_urls"]]

item["option"] = list()
item["att_val_img"] = list()
group_dict = dict()
have_color_type_name = ''

products_list = product_data['options']
if len(products_list) == 1 and products_list[0] == 'Title':
    products_list = []

if products_list:
    for index, one_option_xpath in enumerate(products_list):
        type_name = one_option_xpath
        if not type_name:
            continue
        type_name = type_name.split("_")[0].replace('-', ' ').replace('|', ' ').replace(':',
                                                                                        '').replace('Choose a',
                                                                                                    '').strip().capitalize()
        if type_name == 'Color':
            type_name = 'Colors'
        if type_name not in item["option"]:
            item["option"].append(type_name)
            type_name_index = item["option"].index(type_name)
            item[f"option{type_name_index + 1}_list"] = list()

        type_name_index = item["option"].index(type_name)
        item[f"option{index + 1}_list"] = list()

        for e in product_data['variants']:
            types1 = e[f'option{(index + 1)}']
            types1 = types1.replace('-', ' ').replace('|', ' ').replace(':', ' ').replace('\n', ' ').replace(
                ',',
                ' ').replace(
                '=', ' ').strip()

            if types1 not in item[f"option{type_name_index + 1}_list"]:
                item[f"option{type_name_index +1 }_list"].append(types1)

                types2 = "0" # 初始化变量types2为0 逻辑是如果图像有颜色url，types2就为url，没有就为0
                if type_name == 'Colors':
                    types_img = ''
                    if e.get('featured_image'):
                        types_img = e['featured_image']['src']

                    if types_img:
                        # types2 = response.urljoin(types_img.replace('/50x50/', '/670x890/'))
                        have_color_type_name = type_name
                        group_dict[types1] = types2

                types = "|".join([type_name + ":" + types1 + "-10000-1-0-0-0-0", types2])
                item["att_val_img"].append(types)

if have_color_type_name:
    item["option_image_urls_dict"] = {have_color_type_name: group_dict}

item['quantity'] = str(random.randint(100, 999))
print(item)