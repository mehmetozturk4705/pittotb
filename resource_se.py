import os
from whoosh import fields, index, writing, qparser, analysis, query
import langdetect
from TurkishStemmer import TurkishStemmer

STOP_WORDS_TR = ("acaba", "altı", "ama", "ancak", "artık", "asla", "aslında", "az", "bana", "bazen", "bazı", "bazıları", "bazısı", "belki", "ben", "beni", "benim", "beş", "bile", "bir", "birçoğu", "birçok", "birçokları", "biri", "birisi", "birkaç", "birkaçı", "birşey", "birşeyi", "biz", "bize", "bizi", "bizim", "böyle", "böylece", "bu", "buna", "bunda", "bundan", "bunu", "bunun", "burada", "bütün", "çoğu", "çoğuna", "çoğunu", "çok", "çünkü", "da", "daha", "de", "değil", "demek", "diğer", "diğeri", "diğerleri", "diye", "dokuz", "dolayı", "dört", "elbette", "fakat", "falan", "felan", "filan", "gene", "gibi", "hâlâ", "hangi", "hangisi", "hani", "hatta", "hem", "henüz", "hep", "hepsi", "hepsine", "hepsini", "her", "her biri", "herkes", "herkese", "herkesi", "hiç", "hiç kimse", "hiçbiri", "hiçbirine", "hiçbirini", "için", "içinde", "iki", "ile", "ise", "işte", "kaç", "kadar", "kendi", "kendine", "kendini", "ki", "kim", "kime", "kimi", "kimin", "kimisi", "madem", "mı", "mi", "mu", "mu", "mü", "mü", "nasıl", "ne", "ne kadar", "ne zaman", "neden", "nedir", "nerde", "nerede", "nereden", "nereye", "nesi", "neyse", "niçin", "niye", "on", "ona", "ondan", "onlar", "onlara", "onlardan", "onların", "onların", "onu", "onun", "orada", "oysa", "oysaki", "öbürü", "ön", "önce", "ötürü", "öyle", "rağmen", "sana", "sekiz", "sen", "senden", "seni", "senin", "siz", "sizden", "size", "sizi", "sizin", "son", "sonra", "şayet", "şey", "şeyden", "şeye", "şeyi", "şeyler", "şimdi", "şöyle", "şu", "şuna", "şunda", "şundan", "şunlar", "şunu", "şunun", "tabi", "tamam", "tüm", "tümü", "üç", "üzere", "var", "ve", "veya", "veyahut", "ya", "ya da", "yani", "yedi", "yerine", "yine", "yoksa", "zaten", "zira")


class CustomFuzzyTerm(query.FuzzyTerm):
    def __init__(self, fieldname, text, boost=1.0, maxdist=2, prefixlength=1, constantscore=True):
        super(CustomFuzzyTerm, self).__init__(fieldname, text, boost, maxdist, prefixlength, constantscore)

class ResourceSearchEngine(object):
    def __init__(self, index_dir:str):
        ts = TurkishStemmer()
        self.__schema = fields.Schema(
            message=fields.TEXT(stored=True, field_boost=1.5, analyzer=analysis.StemmingAnalyzer()|analysis.NgramFilter(minsize=2, maxsize=5)),
            meta_content=fields.TEXT(stored=True, analyzer=analysis.StemmingAnalyzer()|analysis.NgramFilter(minsize=2, maxsize=5)),
            message_id=fields.NUMERIC(stored=True, bits=64),
            chat_id=fields.NUMERIC(stored=True, bits=64),
            message_tr=fields.TEXT(stored=False, field_boost=1.5, analyzer=analysis.StemmingAnalyzer(stemfn=ts.stem, stoplist=STOP_WORDS_TR)|analysis.NgramFilter(minsize=2, maxsize=5)),
            meta_content_tr=fields.TEXT(stored=False, analyzer=analysis.StemmingAnalyzer(stemfn=ts.stem, stoplist=STOP_WORDS_TR)|analysis.NgramFilter(minsize=2, maxsize=5)),
        )
        if not os.path.isdir(index_dir):
            os.mkdir(index_dir)
            self.__index = index.create_in(index_dir, self.__schema)
        else:
            self.__index = index.open_dir(index_dir)

    def search_content(self, search_statement:str):
        cur_lang = "en"
        try:
            lng = langdetect.detect(search_statement)
            cur_lang = lng if lng == "tr" else cur_lang
        except Exception as e:
            pass
        result_list = []
        with self.__index.searcher() as searcher:
            query = qparser.MultifieldParser(["message", "meta_content"] if cur_lang=="en" else ["message_tr", "meta_content_tr"], self.__schema, termclass=CustomFuzzyTerm).parse(search_statement)
            results = searcher.search(query)
            for r in results:
                result_list.append({"message_id": r["message_id"], "chat_id": r["chat_id"]})

        return result_list



    def add_documents(self, documents:list):
        with writing.AsyncWriter(self.__index) as writer:
            for doc in documents:
                doc["message_tr"]=doc["message"]
                doc["meta_content_tr"]=doc["meta_content"]
                writer.add_document(**doc)

    def fetch_all_documents(self):
        return self.__index.searcher().documents()