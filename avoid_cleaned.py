import re

def Avoid_cleaned(text, delete_brand_set):
    if delete_brand_set:
        for one_brand in delete_brand_set:
            if one_brand:
                one_brand_name = one_brand.strip()
                re_res = re.findall(one_brand_name, text, re.IGNORECASE)
                if re_res:
                    for ele in re_res:
                        text = re.sub(ele, '', text, flags=re.I)

    with open("D:\item\\bing违规词.txt", encoding='utf-8') as f:
        for one_line in f.readlines():
            if not one_line:
                continue
            if re.findall(one_line, text, re.IGNORECASE):
                text = False
                break
        return text
