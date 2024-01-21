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
#
# 21-Jan-2024 updates:
# - Removed timings, and added token tracking
# - Changed to use single function for GPT API call, and moved various prompts outside of the API call function
# - Changed to provide the transcript as a system message and the individual prompts as user mesages, and added each to message history
# - No clear change in performance vs. v1

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


def gpt_minutes(message_history):
    response = client.chat.completions.create(
        model = gpt_model,
        temperature=0,
        messages=message_history
    )
    print(response)
    reply_content = response.choices[0].message.content
    message_history.append({"role": "assistant", "content": reply_content})
    tokens.append(response.usage.total_tokens)
    return reply_content

if __name__ == '__main__':

    today = str(date.today())
    file_prefix = "unp_Q3_2023_earnings_call"  # filename without extension to use for loading and writing various files

    gpt_model = "gpt-4-1106-preview"


    # Segment audio file into smaller chunks if needed
    # segments = split_mp3('Data/' + file_prefix +'.mp3')  # Split mp3 into segments small enough to transcribe
    #
    # Transcribe audio
    # transcription = transcribe_audio_list(segments)  # Transcribe each segment and return single combined transcription
    #
    # Save transcription as file
    # with open(r'Data/' + file_prefix + '_transcript_' + today + '.txt','w') as file:
    #     file.write(transcription)

    # Read transcription from file
    with open(r'Data/unp_Q3_2023_earnings_call_transcript_2023-12-22.txt','r') as file:
        transcription = file.read()

    print('\n *** Transcription ***\n')
    print(transcription)

    message_history=[]
    tokens=[]

    # Initialize with transcription
    content = "You are a helpful and highly skilled AI trained in language comprehension and summarization. Follows is a transcription of a business meeting.  I will be asking you questions about this meeting. For each request, go back and evaluate the full transcript carefully before responding. Do not reply to this initial message - wait for further instructions.  Here is the transcription: "
    content += transcription
    message_history.append({"role": "system", "content": content})
    response = gpt_minutes(message_history)
    print(response)

    header = "\n --> Summary ***\n"
    message_history.append({"role": "user", "content": "1 - Summary:  Please read the transcription provided above of a meeting and summarize it into a concise abstract paragraphs. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points. The meeting may be a company earnings call with analysts. In this case, provide 2 summary paragraphs - a paragraph summarizing the company officers report in the first part of the call, and a 2nd paragraph summarizing the question and answer session with analysts in the latter part of the call.  Title this response --->SUMMARY<---"})
    response = gpt_minutes(message_history)
    print(response)
    minutes = header
    minutes += response

    header = "\n\n --> Items Of Interest ***\n"
    with open('ioi.txt', 'r') as file:  # Read items of interest from file
        ioi = file.read()
    ioi = ioi.replace('\n', ', ').strip(', ')  # Replace line breaks with commas
    content = "2 - Items of Interest:  You are a helpful and very talented AI trained to search and analyze meeting transcripts.  Carefully search the transcript provided for the following terms.  For each of the terms found, do 2 things: 1) repeat the quote where the term was used, and 2)explain your expert interpretation of what was meant by the discussion about that term.  If a term is not mentioned, only state that it is not mentioned - do not provide any commentary or interpretation of that term.  When complete, review the transcription again to ensure none of the specified terms were missed.  Provide the output in an organized way. Title this response --->ITEMS OF INTEREST<--- Here is the list of terms: "
    content += ioi
    message_history.append({"role": "user", "content": content})
    response = gpt_minutes(message_history)
    print(response)
    minutes += header
    minutes += response

    header = "\n\n --> Key Points ***\n"
    message_history.append({"role": "user", "content": "3 - Key Points:  You are a proficient AI with a specialty in distilling information into key points. Based on the transcription provided, identify and list the main points that were discussed or brought up. These should be the most important ideas, findings, or topics that are crucial to the essence of the discussion. Your goal is to provide a list that someone could read to quickly understand what was talked about. Title this response --->KEY POINTS<---"})
    response = gpt_minutes(message_history)
    print(response)
    minutes += header
    minutes += response

    header = "\n\n --> Action Items ***\n"
    message_history.append({"role": "user", "content": "4 - Action Items:  You are an AI expert in analyzing conversations and extracting action items.  Please review the transcription provided and identify any tasks, assignments, or actions that were agreed upon or mentioned as needing to be done. These could be tasks assigned to specific individuals, or general actions that the group has decided to take. Please list these action items clearly and concisely. Title this response --->ACTION ITEMS<---"})
    response = gpt_minutes(message_history)
    print(response)
    minutes += header
    minutes += response

    header = "\n\n --> Sentiment Analysis ***\n"
    message_history.append({"role": "user", "content": "5 - Sentiment Analysis:  As an AI with expertise in language and emotion analysis, your task is to analyze the sentiment of the transcription provided. Please consider the overall tone of the discussion, the emotion conveyed by the language used, and the context in which words and phrases are used. Indicate whether the sentiment is generally positive, negative, or neutral, and provide brief explanations for your analysis where possible. Title this response --->SENTIMENT ANALYSIS<---"})
    response = gpt_minutes(message_history)
    print(response)
    minutes += header
    minutes += response

    header = "\n\n --> Participants ***\n"
    message_history.append({"role": "user", "content": "6 - Participants:  Analyze the transcription provided and extract the names and roles of the people speaking. Do this by reviewing the text and identifying each person named in the discussions, their title or role, and any other personal information they provide such as location.  Be sure to review the entire conversation and include new people named later in the meeting.  The meeting may be a company earnings conference call with analysts; if this is the case be sure to include the analysts asking questions later in the call.  Please list all of the the names and their related information clearly and concisely.  If there are clear groups of people, such as customer and supplier, group them accordingly.  Provide the output in a table format. Title this response --->PARTICIPANTS<---"})
    response = gpt_minutes(message_history)
    print(response)
    minutes += header
    minutes += response


    with open(r'Data/' + file_prefix + '_minutes_' + today + '.txt','w') as file:  # Save minutes
        file.write(minutes)

    print('\n\n ---> Minutes: ***\n')
    print(minutes)
    print("Tokens: ", tokens)