import threading
import time
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from imdb import IMDb
import pybase64
import os

class LoadingText:
    def __init__(self, texts):
        self.texts = texts
        self.index = 0

    def next(self):
        result = self.texts[self.index]
        self.index = (self.index + 1) % len(self.texts)
        return result

loading_text = LoadingText(["Grab a snack..."])

def background_task():

    while True:
        st.session_state.loading_text = loading_text.next()
        time.sleep(1)  

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return pybase64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
    background-image: url("data:image/png;base64,{bin_str}");
    background-size: cover;
    }}
    </style>
    '''

    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg(r"C:\Users\sagar\Desktop\Movie recommedation system\pic 2.png")

ia = IMDb()

sub = pd.read_csv('sub.csv')  # replace with your data file

tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(sub['description'])


cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

indices = pd.Series(sub.index, index=sub['clean_movie']).drop_duplicates()

def get_poster_url(movie_title):
    movies = ia.search_movie(movie_title)
    if movies:
        movie_id = movies[0].movieID
        movie = ia.get_movie(movie_id)
        poster_url = movie['cover url'] if 'cover url' in movie.keys() else None
        return poster_url
    else:
        return None

def get_recommendations(title, cosine_sim=cosine_sim):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]  
    movie_indices = [i[0] for i in sim_scores]
    recommendations = sub[['rating', 'clean_movie']].iloc[movie_indices]
    recommendations['poster_url'] = recommendations['clean_movie'].apply(get_poster_url)
    return recommendations

# Streamlit app
st.title('Movie Recommendation System')

movie_options = ['Enter Movie name'] + list(sub['clean_movie'].unique())
selected_movie = st.selectbox('Select a movie for recommendations', movie_options)

if selected_movie == 'Enter Movie name':
    st.write("Please select a movie from the dropdown.")
else:
    if st.button('Recommend'):
        if 'loading_text' not in st.session_state:
            st.session_state.loading_text = loading_text.next()
        threading.Thread(target=background_task).start()
        with st.spinner(st.session_state.loading_text):
            recommendations = get_recommendations(selected_movie)
            cols = st.columns(len(recommendations))  # create columns
            for idx, (col, (_, row)) in enumerate(zip(cols, recommendations.iterrows())):
                with col:
                    st.write(f"**Title**: {row['clean_movie']}, **Rating**: {row['rating']}")
                    if row['poster_url']:
                        st.image(row['poster_url'])
                    else:
                        st.write("Poster not available")

    if st.button('Clear Selection'):
        st.write('Please clear the movie selection from the dropdown menu to start a new search.')

