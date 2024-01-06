# This Python program uses OpenAI tools to create meeting minutes from an audio file, like company earnings calls
# First, it uses Pydub (not from OpenAI) to segment the audio file into small enough chunks for OpenAI to process
# Next, it uses Whisper from OpenAI to transcribe the audio into a text file
# Then it uses the ChatGPT API to extract the following from the transcription:
#   - Summary
#   - Key Points
#   - Action Items
#   - Sentiment
# Also, I've added to additional functions beyond the tutorial scope:
#   - Participants
#   - Mentions of items of interest specified by the user
# Last, it combines them into a single text file
# Input: mp3 audio file
# Output: 2 text files:  transcription.txt and minutes.txt

from pydub import AudioSegment
import math
import os
import openai
from openai import OpenAI
import time
import json
from datetime import date

openai.api_key = open(r"C:\Users\GESco\Documents\key.txt", "r").read().strip('\n')
client = OpenAI(
    api_key=openai.api_key
)


def split_mp3(file_path, segment_size_mb=25): # Splits an MP3 file into multiple segments if its size is greater than
    # the specified segment size, and returns a list of paths to the generated segments.

    # Calculate the file size in MB
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # If the file size is smaller than the segment size, no splitting is needed
    if file_size_mb <= segment_size_mb:
        print(f"The file is smaller than {segment_size_mb}MB, no segmentation needed.")
        return [file_path]

    # Load the audio file
    audio = AudioSegment.from_mp3(file_path)

    # Calculate the total duration in milliseconds
    total_duration_ms = len(audio)

    # Calculate the duration of each segment in milliseconds
    # We assume the bit rate of the mp3 is 128kbps for calculation
    segment_duration_ms = (segment_size_mb * 1024 * 8) / 128 * 1000

    # Calculate the number of segments needed
    num_segments = math.ceil(total_duration_ms / segment_duration_ms)

    # Split and export the segments
    segment_paths = []
    for i in range(num_segments):
        start_ms = i * segment_duration_ms
        end_ms = min((i + 1) * segment_duration_ms, total_duration_ms)
        segment = audio[start_ms:end_ms]
        segment_path = f"{file_path}_segment_{i + 1}.mp3"
        segment.export(segment_path, format="mp3")
        segment_paths.append(segment_path)
        print(f"Segment {i + 1} exported as {segment_path}.")

    return segment_paths


def transcribe_audio_list(segments):
    combined_transcription = ""
    for audio_file_path in segments:
        with open(audio_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file)
            combined_transcription += transcription.text + " "

    return combined_transcription


def abstract_summary_extraction(transcription):
    response = client.chat.completions.create(
        model = gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following transcription of a meeting and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    # return response['choices'][0]['message']['content']  # Format from old API
    # response = response.choices[0].message.content
    return response


def key_points_extraction(transcription):
    response = client.chat.completions.create(
        model=gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a proficient AI with a specialty in distilling information into key points. Based on the following text, identify and list the main points that were discussed or brought up. These should be the most important ideas, findings, or topics that are crucial to the essence of the discussion. Your goal is to provide a list that someone could read to quickly understand what was talked about."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    response = response.choices[0].message.content
    return response


def action_item_extraction(transcription):
    response = client.chat.completions.create(
        model=gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting action items. Please review the text and identify any tasks, assignments, or actions that were agreed upon or mentioned as needing to be done. These could be tasks assigned to specific individuals, or general actions that the group has decided to take. Please list these action items clearly and concisely."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    response = response.choices[0].message.content
    return response


def participant_list(transcription):
    response = client.chat.completions.create(
        model=gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting names and roles of the people speaking. Please review the text and identify each person named in the discussions, their title or role, and any other personal information they provide such as location.  Be sure to review the entire conversation and include new people named later in the meeting.  The meeting may be a company earnings conference call with analysts; if this is the case be sure to include the analysts asking questions later in the call.  Please list all of the the names and their related information clearly and concisely.  If there are clear groups of people, such as customer and supplier, group them accordingly"
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    response = response.choices[0].message.content
    return response


def ioi_extraction(transcription):  # Items of interest
    with open('ioi.txt', 'r') as file:  # Read items of interest from file
        ioi = file.read()
    ioi = ioi.replace('\n', ', ').strip(', ')  # Replace line breaks with commas
    content = "You are a helpful and very talented AI trained to search and analyze meeting transcripts.  Carefully search the transcript provided for the following terms.  For each of the terms found, do 2 things: 1) repeat the quote where the term was used, and 2)explain your expert interpretation of what was meant by the discussion about that term.  Provide the output in an organized way.  When complete, review the transcription again to ensure none of the specified terms were missed.  Here is the list of terms: "
    content += ioi
    response = client.chat.completions.create(
        model = gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": content
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    # response = response.choices[0].message.content
    return response


def sentiment_analysis(transcription):
    response = client.chat.completions.create(
        model=gpt_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "As an AI with expertise in language and emotion analysis, your task is to analyze the sentiment of the following text. Please consider the overall tone of the discussion, the emotion conveyed by the language used, and the context in which words and phrases are used. Indicate whether the sentiment is generally positive, negative, or neutral, and provide brief explanations for your analysis where possible."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    response = response.choices[0].message.content
    return response


if __name__ == '__main__':

    today = str(date.today())
    file_prefix = "unp_Q3_2023_earnings_call"  # filename without extension to use for loading and writing various files

    gpt_model = "gpt-4-1106-preview"
    # gpt_model = "gpt-4-32k"
    # gpt_model = "gpt-3.5-turbo-16k-0613"

    # Segment audio file into smaller chunks if needed
    t0 = time.time()
    # segments = split_mp3('Data/' + file_prefix +'.mp3')  # Split mp3 into segments small enough to transcribe
    t1 = time.time()

    # Transcribe audio
    # transcription = transcribe_audio_list(segments)  # Transcribe each segment and return single combined transcription
    t2 = time.time()

    # with open(r'Data/' + file_prefix + '_transcript_' + today + '.txt',
    #           'w') as file:  # Save transcription as file
    #     file.write(transcription)

    with open(r'Data/unp_Q3_2023_earnings_call_transcript_2023-12-23.txt',
              'r') as file:  # Read transcription from file
        transcription = file.read()

    print('\n *** Transcription ***\n')
    print(transcription)
    t3 = time.time()

    # Create sections of meeting minutes
    summary_response = abstract_summary_extraction(transcription)
    summary = "\n Summary: \n" + summary_response.choices[0].message.content
    # summary = "\n Summary: \n" + abstract_summary_extraction(transcription)
    t4 = time.time()

    key_points = "\n\n Key Points \n" + key_points_extraction(transcription)
    t5 = time.time()

    action_items = "\n\n Action Items \n" + action_item_extraction(transcription)
    t6 = time.time()

    participants = "\n\n Participants \n" + participant_list(transcription)
    t7 = time.time()

    ioi_response = ioi_extraction(transcription)
    ioi_discussion = "\n\n Items of Interest \n" + ioi_response.choices[0].message.content
    # ioi_discussion = "\n\n Items of Interest \n" + ioi_extraction(transcription)
    t8 = time.time()

    sentiment = "\n\n Sentiment Analysis \n" + sentiment_analysis(transcription)
    t9 = time.time()

    # Create combined minutes
    minutes = summary
    minutes += key_points
    minutes += action_items
    minutes += participants
    minutes += ioi_discussion
    minutes += sentiment

    print('\n *** Minutes: ***\n')
    print(minutes)

    with open(r'Data/' + file_prefix + '_minutes_' + today + '.txt','w') as file:  # Save minutes
        file.write(minutes)
    t10 = time.time()

    print('\nsegment time =', t1 - t0)
    print('transcribe time = ', t2 - t1)
    print('print time = ', t3 - t2)
    print('summary time =', t4 - t3)
    print('key points time = ', t5 - t4)
    print('action items time = ', t6 - t5)
    print('participants time =', t7 - t6)
    print('ioi time = ', t8 - t7)
    print('sentiment time = ', t9 - t8)
    print('file time = ', t10 - t9)
    print('total time = ', t10 - t0)

    print(json.dumps((summary_response.model_dump()), indent=2))
    print(json.dumps((ioi_response.model_dump()), indent=2))

