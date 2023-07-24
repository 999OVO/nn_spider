# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import zipfile
import unicodedata
import time
import csv
import hashlib
import os
import shutil
import random
import re
import pandas as pd
from avoid_cleaned import Avoid_cleaned
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes


def clean_item(item):
    for one_key in item:
        one_value = item[one_key]
        if type(one_value) == str:
            one_normalize_value = unicodedata.normalize('NFKC', one_value)
            item[one_key] = one_normalize_value
        elif type(one_value) == list:
            one_normalize_value = [unicodedata.normalize('NFKC', e) for e in one_value]
            item[one_key] = one_normalize_value
        elif type(one_value) == dict and one_key == 'option_image_urls_dict':
            one_normalize_have_img_att_name = ''
            group_dict = dict()
            for one_value_key in one_value:
                one_normalize_have_img_att_name = unicodedata.normalize('NFKC', one_value_key)
                one_small_dict = one_value[one_value_key]
                if one_small_dict:
                    for one_color_value_key in one_small_dict:
                        one_color_value_image = one_small_dict[one_color_value_key]
                        one_normalize_color_value_key = unicodedata.normalize(('NFKC',one_color_value_key))
                        one_normalize_color_value_image = unicodedata.normalize('NFKC', one_color_value_image)
                        group_dict[one_normalize_color_value_key] = one_normalize_color_value_image
            if one_normalize_have_img_att_name and group_dict:
                item[one_key] = {one_normalize_have_img_att_name: group_dict}

    return item


class Opencard_302s_Pipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        cls.filename = crawler.settings.get("CSV_FILENAME", str(time.strftime("%m-%d", time.localtime())))
        cls.file_prefixes = '-opencard-'
        cls.csv_file_handle = open(crawler.spider.name + cls.file_prefixes + cls.filename + ".csv", 'w+',
                                   encoding='utf-8',
                                   newline='')

        cls.fileheader = [
            'Product ID', 'Language', 'Stores', 'Stores id (0=Store;1=next if presemt) (1=2)',
            'Model', 'SKU', 'UPC', 'EAN',
            'JAN', 'ISBN', 'MPN', 'Location',
            'Product Name', 'Meta Tag Description', 'Meta Tag Keywords', 'Description',
            'Product Tags', 'Price', 'Quantity', 'Minimum Quantity',
            'Subtract Stock  (1=YES 0= NO)',
            'Out Of Stock Status  (5=Out Of Stock , 8=Pre_Order , In Stock=7, 6=2 _ 3 Days)',
            'Requires Shipping (1=YES 0= NO)', 'SEO Keyword  (Must Unquie)',
            'Image(Main image)', 'Date Available', 'Length Class (1=Centimeter, 3=Inch, 2=Millimeter)', 'Length',
            'Width', 'height', 'Weight', 'Weight Class  (1=Kilogram,2=Gram,6=Ounce,Pound=5)',
            'Status (1=Enabled, 0= Disabled)', 'Sort Order', 'Manufacturer ID', 'Manufacturer', 'Categories id',
            'Categories (category>subcategory; category1>subcategory1 )', 'Related Product ID(productid,productid)',
            'Related Product (model,model)', 'Option (name and type) size:select;color:radio',
            'option:value1-qty-Subtract Stock-Price-Points-Weight;option:value1-qty-Subtract Stock-Price-Points-Weight',
            '(image1;image2;image3)', 'Product Special price:(customer_group_id:start date:end date: special price )',
            'Tax Class (None=0,Taxable Goods=9,Downloadable Products=10) Rest you can make and put that ID',
            'Filter Group Name      (Group Name: Sort order;Group Name: Sort order)',
            'Attributes (Attribute group name:sort order=atrribute name-value-sort order;Attribute group name:sort order=atrribute name-value-sort order;)',
            'Discount (customer_group_id:qty:Priority:Price-Date Start-Date End;customer_group_id:qty:Priority:Price-Date Start-Date End;)',
            'Reward Points',
            'Meta Title',
            'Viewed',
            'Download id',
            'Reviews(Customer ID::author::text::ratting::status::date_added::date_modified|Customer ID::author::text::ratting::status::date_added::date_modified)',
            'BB', 'Product price', 'Product url'
        ]
        cls.wr = csv.writer(cls.csv_file_handle)
        cls.wr.writerow(cls.fileheader)
        cls.type_map = {
            'size': ':select',
            'color': ':select'
        }
        cls.time = 1
        sp = cls()
        return sp

    def process_item(self, item, spider):

        def category_format(*sqe):
            from functools import reduce
            sqe = list(filter(lambda e: e is not None, sqe))
            if sqe.__len__() == 1:
                return sqe[0]
            elif sqe.__len__() == 0:
                return ''

            def a(x, y):
                if not isinstance(x, str):
                    yield x

                yield x + ">" + y

            fmt = list(reduce(a, sqe))
            fmt.insert(0, sqe[0])
            return ";".join(fmt) + ';'

        item["categories_opencard"] = category_format(item.get('type_1'), item.get('type_2'), item.get('type_3'), )

        if item.get("delete_brand"):
            delete_brand = item.get("delete_brand")
        else:
            delete_brand = None
        if ',' in item['other_image_urls']:
            other_image_urls_list = item['other_image_urls'].split(',')
            item['other_image_urls'] = ';'.join(other_image_urls_list)
        item["pd_img_list"] = ';'.join(item["pd_img_list"])
        # 将other_image_urls从字符串变成列表，再根据索引拿到真实数据
        if type(item['other_image_urls']) == str:
            other_image_urls_list = item['other_image_urls'].split(';')
            item['other_image_urls'] = ';'.join(other_image_urls_list)
            image = other_image_urls_list[0]
        else:
            other_image_urls_list = item['other_image_urls']
            item['other_image_urls'] = ';'.join(other_image_urls_list)
            image = other_image_urls_list[0]

        md5 = hashlib.md5()
        data = image.split('/')[-1].replace('.jpg', '') + item['product_title'] + item["categories_opencard"]
        md5.update(data.encode('utf-8'))
        item['SKU'] = md5.hexdigest()[0:7]

        item["product_title"] = Avoid_cleaned(item["product_title"], delete_brand)
        if not item["product_title"]:
            return
        item['product_title'] = item['product_title'].strip()
        item["description"] = Avoid_cleaned(item["description"], delete_brand)
        if not item["description"]:
            return

        if len(item["option"]) == 0:
            line = [
                self.time, 'en', 'default;', '0;',
                "NO" + item["SKU"], "SKUNO" + item['SKU'], '', '',
                '', '', '', '',
                item["product_title"], '', '', item["description"],
                '', item["original_price"], '10000', '1',
                '1', '7', '1', item["product_title"],
                item["image_urls"].split(";")[0], '', '2', '0',
                '0', '0', '1500', '2',
                '1', '0', '', '', '', item["categories_opencard"],
                '', '', '',
                '', item["image_urls"] + ";",
                "1:0000-00-00:0000-00-00:" + item["special_price"].__str__() + ";", '0',
                '', '', '', '', '', item["product_title"], '', '', '', item["Product_price"], item["details"]
            ]
            self.wr.writerow(line)
            self.time += 1

        elif len(item["option"]) > 0:
            line = [
                self.time, 'en', 'default;', '0;',
                "NO" + item["SKU"], "SKUNO" + item['SKU'], '', '',
                '', '', '', '',
                item["product_title"], '', '', item["description"],
                '', item["original_price"], '10000', '1',
                '1', '7', '1', item["product_title"],
                item["image_urls"].split(";")[0], '', '2', '0',
                '0', '0', '1500', '2',
                '1', '0', '', '', '', item["categories_opencard"],
                '', '', "".join([ele + ":select;" for ele in item['option']]),
                ";".join(item["att_val_img"]) + ";",
                item["image_urls"] + ";",
                "1:0000-00-00:0000-00-00:" + item["special_price"].__str__() + ";", '0',
                '', '', '', '', '', item["product_title"], '', '', '', item["Product_price"], item["details"]
            ]
            self.wr.writerow(line)
            self.time += 1

        return item

    def close_spider(self, spider):
        self.csv_file_handle.close()
        new_csv = pd.read_csv(self.csv_file_handle.name, encoding='utf8')
        excel_path = self.csv_file_handle.name.replace('.csv', '.xlsx')

        # writer = pd.ExcelWriter(excel_path, engine='xlsxwriter', options={'strings_to_urls': False})
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        new_csv.to_excel(writer, index=False, encoding='utf8')
        writer.save()
        writer.close()

        self.opencardsZip(hashlib.sha1(to_bytes(spider.name)).hexdigest()[:6], excel_path)

    def opencardsZip(self,image_id,excel_path):
        name = self.csv_file_handle.name.replace('.csv', '').strip()
        abs_path = os.getcwd()
        file_path = abs_path + '\\' + self.csv_file_handle.name.rsplit('.', 1)[0]

        if os.path.exists(file_path + '\\images\\{}\\'.format(str(time.strftime("%Y", time.localtime())) + '-' + self.filename)):
            shutil.rmtree(file_path + '\\images\\{}\\'.format(str(time.strftime("%Y", time.localtime())) + '-' + self.filename))

        os.makedirs(file_path + '\\images\\{}\\'.format(str(time.strftime("%Y", time.localtime())) + '-' + self.filename), 0o777)

        shutil.copytree(abs_path + '\\images\\{}\\{}'.format(str(time.strftime("%Y", time.localtime())) + '-' + self.filename, image_id),
                    file_path + '\\images\\{}\\{}'.format(str(time.strftime("%Y", time.localtime())) + '-' + self.filename, image_id))

        opencard_zip = zipfile.ZipFile(f'{name}({self.time - 1}条).zip', 'w')
        for path, dirnames, filenames in os.walk(file_path):
            fpath = path.replace(file_path, '')
            for filename in filenames:
                opencard_zip.write(os.path.join(path, filename), os.path.join(fpath, filename))

        opencard_zip.write(self.csv_file_handle.name, compress_type=zipfile.ZIP_DEFLATED)

    def csvOpTAbantecart(self):
        reader = csv.DictReader(open(self.csv_file_handle.name, encoding='utf8'))
        csv_file_handle = open(self.csv_file_handle.name.replace('opencard', 'abantecart'), 'w+', encoding='utf8', newline='')
        wr = csv.writer(csv_file_handle)

        site_data = dict()
        site_data['option_name'] = list()
        for li in reader:

            if li.get('Option (name and type) size:select;color:radio'):

                for option in li['Option (name and type) size:select;color:radio'].split(':select;')[:-1]:

                    if option not in site_data['option_name']:
                        site_data['option_name'].append(option)
                        site_data['option{}_len'.format(site_data['option_name'].index(option) + 1)] = 0

                    site_data['option{}_list'.format(site_data['option_name'].index(option) + 1)] = list()
                    option_len = 0
                    for option_str in li[
                                          'option:value1-qty-Subtract Stock-Price-Points-Weight;option:value1-qty-Subtract Stock-Price-Points-Weight'].split(
                            ';')[:-1]:

                        option_name = option_str.split(':')[0]
                        option_value = option_str.split(':')[-1].split('-')[0]

                        site_data['option{}_list'.format(site_data['option_name'].index(option) + 1)] = list()

                        if option == option_name:
                            index = site_data['option_name'].index(option_name) + 1

                            if option_value not in site_data['option{}_list'.format(index)]:
                                option_len += 1

                    if not site_data.get('option{}_len'.format(site_data['option_name'].index(option) + 1)):
                        site_data['option{}_len'.format(site_data['option_name'].index(option) + 1)] = 0

                    if option_len > site_data['option{}_len'.format(site_data['option_name'].index(option) + 1)]:
                        site_data['option{}_len'.format(site_data['option_name'].index(option) + 1)] = option_len

        fileHeaders = [
            'status', 'sku', 'model', 'name', 'blurb', 'description', 'category', 'meta keywords', 'meta description',
            'seo url', 'warehouse', 'stock', 'track stock', 'minimum quantity', 'maximum quantity', 'price', 'cost',
            'tax id', 'sort order', 'call to order', 'manufacturer name', 'weight', 'weight id', 'width', 'height',
            'length', 'length id', 'requires shipping', 'shipping price', 'free shipping', 'date available',
            'image url 1', 'image url 2', 'image url 3', 'image url 4', 'image url 5', 'image url 6', 'image url 7',
            'image url 8'
        ]

        print('site_data', site_data)

        option_sku = {}
        if site_data['option_name']:
            for index, option_name in enumerate(site_data['option_name'], start=1):

                option_name = 'option name {}'.format(index)
                option_sku[option_name] = ''
                option_sort_order = 'option sort order {}'.format(index)
                option_sku[option_sort_order] = ''
                option_status = 'option status {}'.format(index)
                option_sku[option_status] = ''
                option_required = 'option required {}'.format(index)
                option_sku[option_required] = ''
                fileHeaders += [option_name, option_sort_order, option_status, option_required]

                if index == 1:
                    for i in range(1, site_data['option{}_len'.format(index)] + 1):
                        option_value_name = 'option value name' + ' {}'.format(i)
                        option_value_sku = 'option value sku' + ' {}'.format(i)
                        option_value_quantity = 'option value quantity' + ' {}'.format(i)
                        option_value_price = 'option value price' + ' {}'.format(i)
                        option_value_default = 'option value default' + ' {}'.format(i)
                        option_value_weight = 'option value weight' + ' {}'.format(i)
                        option_value_sort_order = 'option value sort order' + ' {}'.format(i)

                        fileHeaders += [option_value_name, option_value_sku, option_value_quantity, option_value_price,
                                        option_value_default, option_value_weight, option_value_sort_order]

                        option_sku[option_value_name] = ''
                        option_sku[option_value_sku] = ''
                        option_sku[option_value_quantity] = ''
                        option_sku[option_value_price] = ''
                        option_sku[option_value_default] = ''
                        option_sku[option_value_weight] = ''
                        option_sku[option_value_sort_order] = ''
                else:

                    for i in range(1, site_data['option{}_len'.format(index)] + 1):
                        option_value_name = 'option value name' + ' {} {}'.format(index, i)
                        option_value_sku = 'option value sku' + ' {} {}'.format(index, i)
                        option_value_quantity = 'option value quantity' + ' {} {}'.format(index, i)
                        option_value_price = 'option value price' + ' {} {}'.format(index, i)
                        option_value_default = 'option value default' + ' {} {}'.format(index, i)
                        option_value_weight = 'option value weight' + ' {} {}'.format(index, i)
                        option_value_sort_order = 'option value sort order' + ' {} {}'.format(index, i)

                        fileHeaders += [option_value_name, option_value_sku, option_value_quantity, option_value_price,
                                        option_value_default, option_value_weight, option_value_sort_order]

                        option_sku[option_value_name] = ''
                        option_sku[option_value_sku] = ''
                        option_sku[option_value_quantity] = ''
                        option_sku[option_value_price] = ''
                        option_sku[option_value_default] = ''
                        option_sku[option_value_weight] = ''
                        option_sku[option_value_sort_order] = ''

        wr.writerow(fileHeaders)

        reader = csv.DictReader(open(self.csv_file_hanle.name, encoding='utf-8'))
        count_1 = 1
        for li in reader:

            item = list()

            option_sku_deep = option_sku
            keys = option_sku_deep.keys()
            for k in list(keys):
                option_sku_deep[k] = ''

            if li.get('Option (name and type) size:select;color:radio'):
                for option in li['Option (name and type) size:select;color:radio'].split(':select;')[:-1]:

                    index = site_data['option_name'].index(option) + 1
                    option_sku_deep['option name {}'.format(index)] = option
                    option_sku_deep['option sort order {}'.format(index)] = '2'
                    option_sku_deep['option status {}'.format(index)] = '1'
                    option_sku_deep['option required {}'.format(index)] = '1'

                    count = 1
                    for option_str in li[
                                          'option:value1-qty-Subtract Stock-Price-Points-Weight;option:value1-qty-Subtract Stock-Price-Points-Weight'].split(
                            ';')[:-1]:

                        option_name = option_str.split(':')[0]
                        option_value = option_str.split(':')[-1].split('-')[0]
                        if option == option_name:

                            if index == 1:
                                option_sku_deep['option value name' + ' {}'.format(count)] = option_value
                                option_sku_deep['option value sku' + ' {}'.format(count)] = option_value
                                option_sku_deep['option value quantity' + ' {}'.format(count)] = str(
                                    random.randint(100, 999))
                                option_sku_deep['option value price' + ' {}'.format(count)] = ''
                                option_sku_deep['option value default' + ' {}'.format(count)] = str(1)
                                option_sku_deep['option value weight' + ' {}'.format(count)] = str(
                                    random.randint(10, 50))
                                option_sku_deep['option value sort order' + ' {}'.format(count)] = str(2)
                            else:
                                option_sku_deep['option value name' + ' {} {}'.format(index, count)] = option_value
                                option_sku_deep['option value sku' + ' {} {}'.format(index, count)] = option_value
                                option_sku_deep['option value quantity' + ' {} {}'.format(index, count)] = str(
                                    random.randint(100, 999))
                                option_sku_deep['option value price' + ' {} {}'.format(index, count)] = ''
                                option_sku_deep['option value default' + ' {} {}'.format(index, count)] = str(1)
                                option_sku_deep['option value weight' + ' {} {}'.format(index, count)] = str(
                                    random.randint(1, 5))
                                option_sku_deep['option value sort order' + ' {} {}'.format(index, count)] = str(2)

                            count += 1

            # status
            item.append(1)

            # sku
            sku_prefix = random.choice(['B', 'I', 'V'])
            for _ in range(5):
                sku_prefix += str(random.randint(1, 10))
            item.append(sku_prefix)

            # model
            item.append('')

            # name
            item.append(li['Product Name'])

            # blurb
            item.append('')

            # description
            item.append(li['Description'].replace('images', 'image'))

            # category
            item.append(li['Categories (category>subcategory; category1>subcategory1 )'])

            # meta keywords/meta description
            item.append('')
            item.append('')

            # seo url
            item.append('-'.join(re.findall('[a-zA-Z0-9]+', li.get('Product Name'))))

            # warehouse
            item.append('')

            # stock  li['Quantity']
            item.append(random.randint(101, 999))

            # track stock
            item.append(random.randint(0, 1))

            # minimum quantity/maximum quantity
            item.append('')
            item.append('')

            # price
            item.append(li['Product price'])

            # cost
            item.append(random.randint(11, 99) / 10)

            # tax id
            item.append(1)

            # sort order
            item.append(count_1)

            # call to order
            item.append('')

            # manufacturer name
            item.append('')

            # weight  weight id	width	height	length  length id
            item.append(random.randint(0, 10) / 100)
            item.append(1)
            item.append(random.randint(11, 99) / 10)
            item.append(random.randint(11, 99) / 10)
            item.append(random.randint(11, 99) / 10)
            item.append(1)

            # requires shipping	shipping price	free shipping   item.append(0)
            item.append(0)
            item.append('')
            item.append('')
            item.append('')

            # image url 1	image url 2	image url 3	image url 4	image url 5	image url 6	image url 7	image url 8
            image_list = li['(image1;image2;image3)'].split(';')[:8]
            if len(image_list) < 8:
                image_list += (8 - len(image_list)) * ['']

            for i in image_list:
                item.append(i.replace('images', 'image'))

            for name in fileHeaders[39:]:
                item.append(option_sku_deep.get(name))

            wr.writerow(item)

            count_1 += 1

        csv_file_handle.close()


class OthersImagesPipeline(ImagesPipeline):
    MIN_WIDTH = 200
    MIN_HEIGHT = 200

    def __init__(self, *args, **kwargs):
        self.TIME = str(time.strftime("%Y-%m-%d", time.localtime()))
        super(OthersImagesPipeline, self).__init__(*args, **kwargs)

    def get_media_requests(self, item, info):
        if item.get("image_urls") is not None:
            for index2, img_url in enumerate(item["image_urls"], start=1):
                headers = {
                    "authority": "cdn.shopify.com",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "cache-control": "no-cache",
                    "pragma": "no-cache",
                    "sec-ch-ua": "^\\^Not?A_Brand^^;v=^\\^8^^, ^\\^Chromium^^;v=^\\^108^^, ^\\^Google",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "^\\^Windows^^",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                }
                cookies = {
                    "_pin_unauth": "dWlkPU4yWm1ObUV3TWpBdE9UTXhNaTAwTlRVeExXRXpNV1l0Wm1RNE1qaGxNRFUwWkRWbQ",
                    "PHPSESSID": "vje4sckuj3a2n06p7ndbh6pip1",
                    "PrestaShop-d798225e36c66710f3ae9602981a6def": "def50200b1e0ae69a097d325c1701a731f98a55b3e6d5c6b07c63bf19bed9eff0d5a5a0a7d48bb4aab0bb2c7647aabe0072e9e29b189cb2d840a810e7874e7de9b70ce32503f5a869400629b5b378800b139bf4497be8fb035a7df37ddd0a9d6f308eafb05b5d4552f1fb017194f6ebcf54e6efbf49c99320235c261653da8326e856b1a0295d0f4331ed343bba98a2e6a3ca4d20de19815cb8cc7d1a5ce294d03a7144f38a597ecd057c85ebea20bc6f4bdb0a59163d0cd5d9afb200397584d2f0a560af3bb2b05d1b71671effb02ed0b64b36cb193a19c4e84c1db8635dc929e07dd7437d496b18e858613f40c65a69206a603ced6fd3cea937f938b1ca4780bf9bfd3e3d2f2cc101b7a42d3cd017cc29c0c0ba2f84085caf938c84bae76105f2ca3b816adb4b63358da09b4d753",
                    "__tins__21203457": "^%^7B^%^22sid^%^22^%^3A^%^201668831664671^%^2C^%^20^%^22vd^%^22^%^3A^%^201^%^2C^%^20^%^22expires^%^22^%^3A^%^201668833464671^%^7D",
                    "__51cke__": "",
                    "__51laig__": "1",
                    "_clck": "dz17sq^|1^|f6p^|0",
                    "_clsk": "2bwnul^|1668831711932^|2^|1^|a.clarity.ms/collect"
                }

                yield Request(img_url, headers=headers, cookies=cookies,
                              meta={"item": item, "index2": index2}, dont_filter=True)

    def item_completed(self, results, item, info):
        image_paths = [self.DEFAULT_FILES_RESULT_FIELD + "/" + x["path"] for ok, x in results if ok]
        if not image_paths:
            return
        item["image_urls"] = ";".join(image_paths)
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        spider_name = hashlib.sha1(to_bytes(info.spider.name)).hexdigest()[:6]
        image_guid = hashlib.sha1(to_bytes(request.meta["item"]["details"])).hexdigest()
        image_path = "/".join([self.TIME, spider_name, image_guid])
        return '%s.jpg' % (image_path + "_" + str(int(request.meta["index2"]) + 100))





class FaTestPipeline:
    def process_item(self, item, spider):
        return item
