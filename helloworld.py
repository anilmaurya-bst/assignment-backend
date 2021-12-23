import webapp2
import requests
import json
import datetime
from google.appengine.ext import db
from bs4 import BeautifulSoup
import requests_toolbelt.adapters.appengine
requests_toolbelt.adapters.appengine.monkeypatch()

ROOT_URL = "https://play.google.com/store/apps/top"


class HelloWebapp2(webapp2.RequestHandler):
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        json_obj={"id":11,"name":"welcome to webapp2 app"}
        self.response.out.write(json.dumps(json_obj))



class TopAppsDataApi(webapp2.RequestHandler):
    def get(self):
        first_page_data_query=FirstPageData.all().order('-created_date')
        app_data={}
        for data in first_page_data_query:
            row_data={}
            row_data['app_name']=data.app_name
            row_data['image_src']=data.image_src
            row_data['next_page_end_point']=data.next_page_end_point
            row_data['app_header_name']=data.app_header_name
            if data.app_category_name in app_data and len(app_data[data.app_category_name])<=5:
                app_data[data.app_category_name].append(row_data)
            else:
                app_data[data.app_category_name]=[]
                app_data[data.app_category_name].append(row_data)
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(app_data))


class Scrapping:
    def __init__(self,URL):
        self.URL=URL
    def doScrapping(self):
        page = requests.get(self.URL)
        if 200 <= page.status_code < 300:
            soup = BeautifulSoup(page.content, "html.parser")
            return soup
        else:
            print("page is not found page response code :"+page.status_code)
            return None




class ScrappingSecondPage:
    def __init__(self,URL):
       self.URL=URL
    def scrapping_page(self):
        scrapping = Scrapping(self.URL)
        soup = scrapping.doScrapping()
        if soup is None:
            print("page not found")
            return
        main_div=soup.find('main',class_="LXrl4c")
        app_detail_on_second_page={}
        h1=main_div.find('h1',class_="AHFaub")
        app_detail_on_second_page['app_header_name']=h1.text.strip()
        app_image_src=main_div.find('img',class_="T75of sHb2Xb")
        app_detail_on_second_page['app_image_src']=app_image_src['src']
        app_name_elements=main_div.findAll('span',class_="T32cc UAO9ie")
        app_name=""
        for app_name_element in app_name_elements:
            a=app_name_element.find('a',class_="hrTbp R8zArc")
            app_name=app_name+a.text.strip()
        app_detail_on_second_page['app_name']=app_name
        app_rating=main_div.find('div',role='img')
        app_detail_on_second_page['app_ratings']=app_rating['aria-label']
        rating_user_counts=main_div.find('span',class_="AYi5wd TBRnV")
        rating_count=""
        for span in rating_user_counts:
             rating_count+=span.text.strip()
        app_detail_on_second_page['users_rating_count']=rating_count
        button=main_div.find('button',class_="LkLjZd ScJHi HPiPcc IfEcue")
        download_link=button.find('meta',itemprop="url")
        app_detail_on_second_page['download_link']=download_link['content']
        screen_shot_div=main_div.find('div',class_="JiLaSd u3EI9e")
        app_screen_shot_urls=screen_shot_div.findAll('img',class_="T75of DYfLw")
        screen_shot=[]
        for screen_shot_url in app_screen_shot_urls:
            image_shot_src=screen_shot_url['src']
            if image_shot_src.startswith("https://"):
                screen_shot.append(image_shot_src)
        app_detail_on_second_page['app_screen_shot_src']=screen_shot
        trailer_video_div=screen_shot_div.find('div',class_="TdqJUe")
        video_link_url=trailer_video_div.find('button',class_="MMZjL lgooh")
        app_detail_on_second_page['video_link_url']=video_link_url['data-trailer-url']
        description_div=main_div.find('div',jsname="sngebd")
        app_detail_on_second_page['description_content']=description_div.text.strip()[0:500]
        return app_detail_on_second_page



class SecondDataEntityModel(db.Model):
    app_header_name=db.StringProperty()
    app_image_src=db.TextProperty()
    app_name=db.StringProperty()
    app_ratings=db.StringProperty()
    users_rating_count=db.TextProperty()
    download_link=db.TextProperty()
    app_screen_shot_src=db.ListProperty(str)
    video_link_url=db.TextProperty()
    description_content=db.TextProperty()


class SavingSecondPageData:
    def __init__(self,data):
        self.data=data
    def save(self):
       e=SecondDataEntityModel.get_or_insert(self.data['app_key'])
       e.app_header_name=self.data['app_header_name'].encode("ascii","ignore")
       e.app_image_src=self.data['app_image_src']
       e.app_name=self.data['app_name'].encode("ascii","ignore")
       e.app_ratings=self.data['app_ratings']
       e.users_rating_count=self.data['users_rating_count']
       e.download_link=self.data['download_link']
       list_url=[]
       for src in self.data['app_screen_shot_src']:
           list_url.append(src.encode("ascii","ignore"))
       e.app_screen_shot_src=list_url   
       e.video_link_url=self.data['video_link_url']
       e.description_content=self.data['description_content'].encode("ascii","ignore")
       e.put()


class SingleAppPageDetailDataApi(webapp2.RequestHandler):
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        app_id=self.request.get('app_id')
        app_key=app_id
        app_detils=SecondDataEntityModel.get_or_insert(app_key)
        app_data={}
        if app_detils.app_name is None:
            print("data is not present in db")
            second_page_url = ("https://play.google.com/store/apps/details?id=" + ("{}".format(app_id)))
            app_data=ScrappingSecondPage(second_page_url).scrapping_page()
            app_data['app_key']=app_key
            SavingSecondPageData(app_data).save()
        else:
          print("fetched from db ")
          app_data['app_key']=app_key
          app_data['app_header_name']=app_detils.app_header_name
          app_data['app_image_src']=app_detils.app_image_src
          app_data['app_name']=app_detils.app_name
          app_data['app_ratings']=app_detils.app_ratings
          app_data['users_rating_count']=app_detils.users_rating_count
          app_data['download_link']=app_detils.download_link
          app_data['app_screen_shot_src']=app_detils.app_screen_shot_src
          app_data['video_link_url']=app_detils.video_link_url
          app_data['description_content']=app_detils.description_content
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(app_data))
        
        


class FirstPageData(db.Model):
    app_name=db.StringProperty()
    image_src=db.TextProperty()
    next_page_end_point=db.TextProperty()
    app_header_name=db.TextProperty()
    app_category_name=db.TextProperty()
    created_date=db.DateTimeProperty(auto_now_add=True)


class SavingFirstPageData:

    def __init__(self,data):
        self.data=data

    def save(self):
        e = FirstPageData.get_or_insert(self.data['key_name'])
        e.app_name = self.data['app_name'].encode("ascii","ignore")
        e.app_header_name = self.data['app_header_name'].encode("ascii","ignore")
        e.app_category_name = self.data['app_category_name'].encode("ascii","ignore")
        e.image_src = self.data['app_image_src']
        e.next_page_end_point = self.data['next_page_url']
        e.created_date=datetime.datetime.now()
        e.put()




class ScrapPlayStoreDataApi(webapp2.RequestHandler):
    def get(self):
        print("scrapped done!!!")
        scrapping=Scrapping(ROOT_URL)
        soup=scrapping.doScrapping()
        if soup is None:
            print("page not found")
            return
        div_container = soup.findAll("div", class_="Ktdaqe")
        for top_div in div_container:
            app_category_element = top_div.find("h2", class_="sv0AUd bs3Xnd")
            content_of_inner_div = top_div.findAll("div", class_="WHE7ib mpg5gc")
            app_data={}
            for div in content_of_inner_div:
                app_name_element = div.find("div", class_="WsMG1c nnK0zc")
                app_header_element = div.find("div", class_="KoLSrc")
                app_next_page_link = div.find("a", class_="poRVub",href=True)
                app_image_src = div.find("img", class_="T75of QNCnCf")
                next_page_url = app_next_page_link['href']
                start_index=next_page_url.find("?id=")
                key_name=next_page_url[start_index+len("?id="):]
                app_data['key_name']=key_name
                app_data['app_name']=app_name_element.text.strip()
                app_data['app_header_name']=app_header_element.text.strip()
                app_data['app_category_name']=app_category_element.text.strip()
                app_data['app_image_src']=app_image_src['data-src']
                app_data['next_page_url']=key_name
                saving_first_page_data=SavingFirstPageData(app_data)
                saving_first_page_data.save()

        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/text'
        self.response.out.write("successfully stored scrapped data in database")



application = webapp2.WSGIApplication([
      ('/', HelloWebapp2),('/get_top_apps',TopAppsDataApi)
    ,('/rescrapping',ScrapPlayStoreDataApi),('/get_details',SingleAppPageDetailDataApi)
], debug=True)


def main():
    application.run()

if __name__ == "__main__":
    main()

