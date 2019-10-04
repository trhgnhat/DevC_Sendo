from flask import Flask, request
from sqlalchemy import create_engine
from flask.json import jsonify
import pickle
import pandas as pd
import numpy as np
import scipy.sparse as sparse
from selenium import webdriver
import urllib.parse

app = Flask(__name__)

engine = create_engine('mysql+mysqlconnector://root:123456@localhost:3306/sendo')
model = pickle.load(open("model.sav", "rb"))
products_df = pd.read_sql("SELECT * FROM product", engine)
n_products = len(products_df)


def get_info(driver, product):
    item = dict()
    item["product_id"] = int(product.product_id.values[0])
    item["href"] = product.href.values[0]
    item["belong_cate_lvl1_id"] = int(product.cate_lvl1_id.values[0])
    item["belong_cate_lvl2_id"] = int(product.cate_lvl2_id.values[0])
    item["belong_cate_lvl3_id"] = int(product.cate_lvl3_id.values[0])
    item["image_url"] = ""
    item["price"] = "0"
    item["name"] = product.name.values[0]
    item["shop_name"] = ""
    while len(item["name"]) > 0:
        params = {'q': product.name.values[0]}
        driver.get("https://www.sendo.vn/tim-kiem?{}".format(urllib.parse.urlencode(params)))
        try:
            first_item = driver.find_element_by_css_selector("div[class^='list_'] a[class^='item_']")
            item["href"] = first_item.get_attribute("href").split("?")[0]
            item["image_url"] = first_item.find_element_by_tag_name("img").get_attribute("src")
            item["name"] = first_item.find_element_by_css_selector(
                "div[class^='caption_'] h3[class^='productName_'] span").text
            item["price"] = first_item.find_element_by_css_selector(
                "div[class^='caption_'] div[class^='productPrice_'] strong").text
            item["shop_name"] = first_item.find_element_by_css_selector(
                "div[class^='caption_'] div[class^='footer_'] span[class^='shopName_'] span[class^='textSmall_']").text
            break
        except Exception as e:
            item["name"] = " ".join(item["name"].split(" ")[:-1])
    return item

@app.route('/')
def index():
  return 'Index Page'


@app.route('/user_rec/<int:user_id>')
def user_rec(user_id):
    user_id = pd.read_sql("SELECT id, user_id FROM user WHERE id={}".format(user_id), engine).user_id.values[0]
    user_events = pd.read_sql("SELECT * FROM event WHERE user_id='{}'".format(user_id), engine)
    user_events["views"] = 1
    user_events = user_events.groupby(["user_id", "product_id", "belong_cate_lvl3_id"]).sum().reset_index()
    user_events["product_id"] = user_events["product_id"].apply(
        lambda x: pd.read_sql("SELECT id FROM product WHERE product_id={}".format(int(x)), engine).id.values[0])
    products = user_events.product_id.astype(int)
    views = user_events.views.astype(int)
    users = user_events.views.apply(lambda x: 0).astype(int)

    user_items_matrix = sparse.csr_matrix((views, (users, products)), shape=(1, n_products), dtype=np.int16)

    recommended = model.recommend(0, user_items_matrix, N=50, recalculate_user=True)

    result = {"items": []}
    driver = webdriver.Chrome('chromedriver.exe')
    driver.implicitly_wait(3)
    for p_id, score in recommended:
        product = products_df[products_df.id == p_id]
        _item = get_info(driver, product)
        result["items"].append(_item)
    result["status"] = "200"
    driver.quit()
    pickle.dump(model, open("model.sav", "wb"))
    return jsonify(result)


@app.route('/popular_items/<int:top_num>')
@app.route('/popular_items')
def popular_items(top_num=10):
    newest_dates = pd.read_sql("SELECT time FROM event ORDER BY ABS(DATEDIFF(time, NOW())) LIMIT 2", engine).time.values
    top_num = "LIMIT {}".format(top_num)
    pop_pro_query = "SELECT user_id, product_id, belong_cate_lvl3_id, COUNT(*) AS magnitude  FROM sendo.event WHERE date(time) = date('{}') OR date(time) = date('{}') GROUP BY product_id  ORDER BY magnitude DESC {}".format(newest_dates[0], newest_dates[1],top_num)
    popular_product_ids = pd.read_sql(pop_pro_query, engine).product_id.values

    result = {"items": []}
    driver = webdriver.Chrome('chromedriver.exe')
    driver.implicitly_wait(3)
    for p_id in popular_product_ids:
        product = products_df[products_df.product_id == p_id]
        _item = get_info(driver, product)
        result["items"].append(_item)
    result["status"] = "200"
    driver.quit()
    return jsonify(result)


if __name__ == '__main__':
    app.run(host="localhost", port=1000, debug=True)
