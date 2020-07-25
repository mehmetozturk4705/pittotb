import requests
from bs4 import BeautifulSoup
from linkpreview import link_preview


class Utils:
    @staticmethod
    def extract_meta_of_webpage(url: str):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url.strip()}"
        r = requests.get(url)
        r.raise_for_status()
        preview_text=""
        try:
            preview = link_preview(content=r.text.encode())
            preview_text = f"{preview.force_title if preview.force_title else ''}\n{preview.description if preview.description else ''}"
        except Exception as e:
            pass

        if len(preview_text) < 8:
            soup = BeautifulSoup(r.text, features="lxml")
            metas = soup.find_all('meta')
            preview_text = "\n".join([meta.attrs['content']
                                      for meta in metas
                                      if 'name' in meta.attrs and meta.attrs['name'] in ['description',
                                                                                         'twitter:description',
                                                                                         'twitter:title']])

        return preview_text