from flask import Flask, render_template, request
import json
from wordcloud import WordCloud
import base64
import io
import datetime
import requests
import plotly.graph_objects as go

app = Flask(__name__)

url = ''
try:
    response = requests.get(url)
    data = response.json()

except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")


def generate_word_cloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    # Convert the word cloud image to a BytesIO object
    buffer = io.BytesIO()
    wordcloud.to_image().save(buffer, format='PNG')
    # Encode the image as base64
    wordcloud_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return wordcloud_base64


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # Prepare data for the Plotly graph and word cloud
    graphs = []  # List to store individual graph and word cloud for each date
    # capture the dates, duplicated values are removed
    dates = set(tweet['date_without_time'] for tweet in data)
    # Calculate the number of negative and positive tweets for each date
    tweets_by_date = {}
    for date in dates:  # loop that iterates over each unique date in the 'dates' set
        tweets = [tweet for tweet in data if tweet['date_without_time'] == date]
        negative_tweets = sum(1 for tweet in tweets if tweet['sentiment_score'] < 0)
        positive_tweets = sum(1 for tweet in tweets if tweet['sentiment_score'] > 0)
        # Dictionary with date key, holds two other dictions one with the neg tweets and one with pos tweets
        tweets_by_date[date] = {'negative': negative_tweets, 'positive': positive_tweets}

        # Prepare data for the Plotly graph
        dates_list = list(tweets_by_date.keys())  # this list of dates becomes the x-axis
        negative_counts = [tweets_by_date[date]['negative'] for date in dates_list]  # count the number of neg tweets
        positive_counts = [tweets_by_date[date]['positive'] for date in dates_list]  # count the number of pos tweets

        # Create the dual bar graph using Plotly
        fig = go.Figure()  # new Plotly figure
        fig.add_trace(go.Bar(x=dates_list, y=negative_counts, name='Negative', marker=dict(color='red')))  # neg bar
        fig.add_trace(go.Bar(x=dates_list, y=positive_counts, name='Positive', marker=dict(color='blue')))  # pos bar
        # update the layout
        fig.update_layout(title='Number of Negative and Positive Tweets by Date',
                          xaxis_title='Date',
                          yaxis_title='Number of Tweets')

        # Convert the Plotly graph to HTML to be passed to the template
        graph_html = fig.to_html()

    if request.method == 'POST':
        selected_date = request.form['selected_date']
        print(selected_date)

        # Table of tweets
        # current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        tweets_with_scores = [(tweet['tweet'], tweet['sentiment_score']) for tweet in data if
                              tweet['date_without_time'] == selected_date]
        # sort them in order of negative to positive tweets
        sorted_tweets_with_scores = sorted(tweets_with_scores, key=lambda x: x[1])

        # Generate the word cloud for the current date
        tweets_for_date = [tweet['tweet'] for tweet in data if tweet['date_without_time'] == selected_date]
        text_for_wordcloud = ' '.join(tweets_for_date)
        wordcloud_base64 = generate_word_cloud(text_for_wordcloud)

        # Append both the graph HTML and word cloud base64 to the list
        graphs.append((graph_html, wordcloud_base64))

        return render_template('dashboard.html', tweets_with_scores=sorted_tweets_with_scores, graph_html=graph_html,
                               current_date=current_date, display_date=selected_date, graphs=graphs)

    tweets_with_scores = [(tweet['tweet'], tweet['sentiment_score']) for tweet in data if
                          tweet['date_without_time'] == current_date]
    # sort them in order of negative to positive tweets
    sorted_tweets_with_scores = sorted(tweets_with_scores, key=lambda x: x[1])

    # Generate the word cloud for the current date
    tweets_for_date = [tweet['tweet'] for tweet in data if tweet['date_without_time'] == current_date]
    text_for_wordcloud = ' '.join(tweets_for_date)
    wordcloud_base64 = generate_word_cloud(text_for_wordcloud)

    # Append both the graph HTML and word cloud base64 to the list
    graphs.append((graph_html, wordcloud_base64))

    return render_template('dashboard.html', tweets_with_scores=sorted_tweets_with_scores, graph_html=graph_html,
                           current_date=current_date, display_date=current_date, graphs=graphs)


if __name__ == '__main__':
    app.run()
