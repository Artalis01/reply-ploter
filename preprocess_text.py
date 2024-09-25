from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from tqdm import tqdm
import numpy as np
import pandas as pd
import scipy, nltk, joblib, re, copy

nltk.download('punkt')
nltk.download('punkt_tab')

def normalize(dicts, topic=False):
    # clean and normalize text

    # entity dictionary
    path = 'resources/preprocess_csv'
    entities_df = pd.read_csv(path+'/entities.csv')
    entities = entities_df.to_dict(orient='records')

    # slang word dictionary
    slang_df = pd.read_csv(path+'/slang_dictionary.csv')
    slang_dicts = slang_df.to_dict(orient='records')

    pattern_list = [entities, slang_dicts]
    # entity & slang word normalization
    for patterns in pattern_list:
        for pattern in patterns:
            slang = pattern['slang']
            standard = pattern['standard']
            regex_pattern = r'\b' + re.escape(slang) + r'\b'
            
            if topic:
                content = dicts['content']
                corrected_content = re.sub(regex_pattern, standard, content.lower())
                dicts['content'] = corrected_content
            
            else:
                for item in dicts:
                    content = item.get('content', '')
                    corrected_content = re.sub(regex_pattern, standard, content.lower())
                    item['content'] = corrected_content

    return dicts

def clean(dicts, topic=False):
    # clean irrelevant character & symbol
    key = 'content'
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    pattern = re.compile(r'[^a-zA-Z0-9?! ]')
    if topic:
        if re.search(url_pattern, dicts[key]):
            dicts[key] = re.sub(url_pattern, '', dicts[key])
            
        if re.search(pattern, dicts[key]):
            dicts[key] = re.sub(pattern, ' ', dicts[key])
            dicts[key] = dicts[key].strip()
            dicts[key] = dicts[key].split()
            dicts[key] = ' '.join(dicts[key])

    else:
        for d in dicts:
            if re.search(url_pattern, d[key]):
                d[key] = re.sub(url_pattern, '', d[key])
                
            if re.search(pattern, d[key]):
                d[key] = re.sub(pattern, ' ', d[key])
                d[key] = d[key].strip()
                d[key] = d[key].split()
                d[key] = ' '.join(d[key])

    return dicts

def stem_text(dicts, topic=False):
    # stemming and removing stopword
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    factory = StopWordRemoverFactory()
    stopword_remover = factory.create_stop_word_remover()

    if topic:
        dicts['content'] = stemmer.stem(dicts['content'])
        dicts['content'] = stopword_remover.remove(dicts['content'])
    else:
        for d in dicts:
            d['content'] = stemmer.stem(d['content'])
            d['content'] = stopword_remover.remove(d['content'])

    return dicts

def get_content(topic, replies):
    # get content value of data
    content_topics = []
    content_replies = []

    for i in range(len(replies)):
        content_topics.append(topic['content'])
        content_replies.append(replies[i]['content'])

    return content_topics, content_replies

def extract_tfidf(topics, replies):
    # Load Vectorizer
    topic_vectorizer = joblib.load('resources/model/topic_tfidf_vectorizer.pkl')
    reply_vectorizer = joblib.load('resources/model/reply_tfidf_vectorizer.pkl')

    # Tranform topics and replies using the trained vectorizer
    topics_tfidf = topic_vectorizer.transform(topics)
    replies_tfidf = reply_vectorizer.transform(replies)

    # Combine topic_tfdif with replies_tfidf for every data point. 
    tfidf = scipy.sparse.hstack([topics_tfidf, replies_tfidf])

    return tfidf

def extract_cosine_similarity(topics, replies):
    vectorizer = TfidfVectorizer(ngram_range=(1,2), lowercase=True, max_features=35000)
    
    cos_sim_features = []
    for i in range(len(topics)):
        topic_vs_reply = []
        topic_vs_reply.append(topics[i])
        topic_vs_reply.append(replies[i])
        tfidf = vectorizer.fit_transform(topic_vs_reply)
        
        cosine_sim = cosine_similarity(tfidf[0], tfidf[1])
        cos_sim_features.append(cosine_sim[0][0])

    # Convert the list to a sparse matrix (in order to concatenate the cos sim with other features)
    cos_sim_array = scipy.sparse.coo_matrix(np.array(cos_sim_features).reshape(-1, 1)) 

    return cos_sim_array

def combine_features(tfidf_vectors, cosine_similarity): #, word_overlap):
    combined_features =  sparse.bmat([[tfidf_vectors, cosine_similarity.toarray()]]) 
    return combined_features

def extract_features(topic, replies):
    # extract features from text data
    content_topics, content_replies = get_content(topic, replies)
    
    # extract tfidf value
    tfidf_vectors = extract_tfidf(content_topics, content_replies)

    # extract cosine similarity
    cosim = extract_cosine_similarity(content_topics, content_replies)

    # combine features
    features = combine_features(tfidf_vectors, cosim)

    return features

def preprocess(pbar, topic, replies):
    base_topic = copy.deepcopy(topic)
    base_replies = copy.deepcopy(replies)
    pbar.progress(int((6/11)*100), text='(6/11) Menormalisasi teks')
    normalized_topic = normalize(base_topic, topic=True)
    normalized_reply = normalize(base_replies)
    
    pbar.progress(int((7/11)*100), text='(7/11) Membersihkan teks')
    cleaned_topic = clean(normalized_topic, topic=True)
    cleaned_reply = clean(normalized_reply)

    pbar.progress(int((8/11)*100), text='(8/11) Menyederhanakan teks')
    stemmed_topic = stem_text(cleaned_topic, topic=True)
    stemmed_reply = stem_text(cleaned_reply)

    pbar.progress(int((9/11)*100), text='(9/11) AI Memahami teks')
    features = extract_features(stemmed_topic, stemmed_reply)
    return features
