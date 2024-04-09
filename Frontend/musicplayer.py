import random

import pandas as pd
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import numpy as np
import webbrowser
import mediapipe as mp
from keras.models import load_model
import cv2
import pydub
from pydub.playback import play
import pytube

import hashlib
def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False

import sqlite3
conn = sqlite3.connect('data.db')
c = conn.cursor()

def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data



def main():


	st.title("Sentiment Based music composer")

	menu = ["Home","Login","SignUp"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice == "Home":

		st.image("wal.jpg",width = 400)
		st.subheader("Home")

	elif choice == "Login":
		st.subheader("Login and select your interest")
		st.image("wal1.jpg", width=500)


		username = st.sidebar.text_input("User Name")
		password = st.sidebar.text_input("Password",type='password')
		if st.sidebar.checkbox("Login"):
			create_usertable()
			hashed_pswd = make_hashes(password)

			result = login_user(username,check_hashes(password,hashed_pswd))
			if result:

				st.success("Logged In as {}".format(username))

				task = st.selectbox("Task",["By capturing emotion","By mentioning emotion"])
				if task == "By capturing emotion":
					model = load_model("model.h5")
					label = np.load("labels.npy")
					holistic = mp.solutions.holistic
					hands = mp.solutions.hands
					holis = holistic.Holistic()
					drawing = mp.solutions.drawing_utils

					if "run" not in st.session_state:
						st.session_state["run"] = "true"
					try:
						emotion = np.load("emotion.npy")[0]
					except:
						emotion = ""

					if not (emotion):
						st.session_state["run"] = "true"
					else:
						st.session_state["run"] = "false"

					class SentimentProcessor:
						def recv(selfself, frame):
							frm = frame.to_ndarray(format="bgr24")
							frm = cv2.flip(frm, 1)

							res = holis.process(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
							lst = []
							if res.face_landmarks:
								for i in res.face_landmarks.landmark:
									lst.append(i.x - res.face_landmarks.landmark[1].x)
									lst.append(i.y - res.face_landmarks.landmark[1].y)

								if res.left_hand_landmarks:
									for i in res.left_hand_landmarks.landmark:
										lst.append(i.x - res.left_hand_landmarks.landmark[8].x)
										lst.append(i.y - res.left_hand_landmarks.landmark[8].y)
								else:
									for i in range(42):
										lst.append(0.0)

								if res.right_hand_landmarks:
									for i in res.right_hand_landmarks.landmark:
										lst.append(i.x - res.right_hand_landmarks.landmark[8].x)
										lst.append(i.y - res.right_hand_landmarks.landmark[8].y)
								else:
									for i in range(42):
										lst.append(0.0)

								lst = np.array(lst).reshape(1, -1)

								pred = label[np.argmax(model.predict(lst))]

								print(pred)
								cv2.putText(frm, pred, (50, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
								np.save("emotion.npy", np.array([pred]))

							drawing.draw_landmarks(frm, res.face_landmarks, holistic.FACEMESH_CONTOURS)
							drawing.draw_landmarks(frm, res.left_hand_landmarks, hands.HAND_CONNECTIONS)
							drawing.draw_landmarks(frm, res.right_hand_landmarks, hands.HAND_CONNECTIONS)
							return av.VideoFrame.from_ndarray(frm, format="bgr24")

					language_artists = {
						"English": ["Justin Bieber", "Taylor Swift"],
						"Spanish": ["Shakira", "Enrique Iglesias"],
						"French": ["Edith Piaf", "Charles Aznavour"],
						"German": ["Rammstein", "Nena"],
						"Japanese": ["Hikaru Utada", "Arashi"],
						"Telugu": ["SP Balasubrahmanyam", "Chitra"],
						"Hindi": ["Shreya Ghoshal", "Arijit Singh"]
					}
					#if st.session_state["run"] != "false":
					webrtc_streamer(key="yup", desired_playing_state=True,video_processor_factory=SentimentProcessor)
					language = st.text_input("Preferrable Language")
					artist = st.text_input("Favourite artist")
					if not language:
						languages = list(language_artists.keys())
						language = random.choice(languages)
						artist = random.choice(language_artists[language])
					if not artist:
						if language in language_artists:
							artist = random.choice(language_artists[language])
						else:
							artist = "Unknown Artist"
					#if language and artist and st.session_state["run"] != "false":
						#webrtc_streamer(key="yup", desired_playing_state=True,video_processor_factory=SentimentProcessor)
					butnn = st.button("Relatable songs")

					if butnn:
						if not emotion:
							st.warning("Capture your emotion first")
						else:
							#webbrowser.open(f"https://www.youtube.com/results?search_query={language}+{emotion}+songs+by+{artist}")
							query = f"{language} {emotion} songs by {artist}"
							try:
								# Search for videos matching the query
								results = pytube.Search(query).results

								if not results:
									st.warning("No matching videos found.")
								else:
									# Play a random video from the search results
									random_video = random.choice(results)
									video_url = f"https://www.youtube.com/watch?v={random_video.video_id}&autoplay=1"
									st.success(f"Now playing: {random_video.title}")
									#webbrowser.open(video_url)
									st.video(video_url)


								# You can then use this video URL to embed the video in Streamlit or open it in a web browser
								# For example:
								# st.video(video_url)
								# or
								# webbrowser.open(video_url)
							except Exception as e:
								st.error(f"An error occurred: {e}")

							np.save("emotion.npy", np.array([""]))
							st.session_state["run"] = "false"

				elif task == "By mentioning emotion":
					language_artists = {
						"English": ["Justin Bieber", "Taylor Swift"],
						"Spanish": ["Shakira", "Enrique Iglesias"],
						"French": ["Edith Piaf", "Charles Aznavour"],
						"German": ["Rammstein", "Nena"],
						"Japanese": ["Hikaru Utada", "Arashi"],
						"Telugu": ["SP Balasubrahmanyam", "Chitra"],
						"Hindi": ["Shreya Ghoshal", "Arijit Singh"]
					}
					language = st.text_input("Preferrable Language")
					if not (language):
						# st.warning("Enter language first")
						# st.session_state["run"] = "true"
						languages = list(language_artists.keys())
						language = random.choice(languages)
						artist = random.choice(language_artists[language])
					artist = st.text_input("Favourite artist")
					if not (artist):
						# st.warning("Enter artist name first")
						# st.session_state["run"] = "true"
						if language in language_artists:
							artist = random.choice(language_artists[language])
						else:
							artist = "Unknown Artist"
					feeling = st.text_input("How are you feeling today")
					butn = st.button("Relatable songs")
					if butn:
						if not (feeling):
							st.warning("Enter emotion first")
							st.session_state["run"] = "true"
						else:
							query = f"{language} {feeling} songs by {artist}"
							try:
								# Search for videos matching the query
								results = pytube.Search(query).results

								if not results:
									st.warning("No matching videos found.")
								else:
									# Play a random video from the search results
									random_video = random.choice(results)
									video_url = f"https://www.youtube.com/watch?v={random_video.video_id}&autoplay=1"
									st.success(f"Now playing: {random_video.title}")
									#webbrowser.open(video_url)
									st.video(video_url)
									
								# You can then use this video URL to embed the video in Streamlit or open it in a web browser
								# For example:
								# st.video(video_url)
								# or
								# webbrowser.open(video_url)
							except Exception as e:
								st.error(f"An error occurred: {e}")


			else:
				st.sidebar.warning("Incorrect Username/Password")





	elif choice == "SignUp":
		st.image("wal2.jpg", width=500)
		st.sidebar.subheader("Create New Account")
		new_user = st.sidebar.text_input("Username")
		new_password = st.sidebar.text_input("Password",type='password')

		if st.sidebar.button("Signup"):
			create_usertable()
			add_userdata(new_user,make_hashes(new_password))
			st.sidebar.success("You have successfully created a valid Account")
			st.sidebar.info("Go to Login Menu to login")



if __name__ == '__main__':
	main()
