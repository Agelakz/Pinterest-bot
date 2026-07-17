from services.pinterest_api import PinterestAPI
api = PinterestAPI(cookies_file="all_cookies.txt")
print(f"CSRF Token: {api.csrftoken}")
