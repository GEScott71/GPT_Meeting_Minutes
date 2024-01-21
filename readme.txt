This program is my take on the OpenAI tutorial for creating meeting minutes from an audio file.
It takes a single MP3 audio file as an input, and outputs 2 text files:  a transcription, and minutes

# 21-Jan-2024 updates:
# - Removed timings, and added token tracking
# - Changed to use single function for GPT API call, and moved various prompts outside of the API call function
# - Changed to provide the transcript as a system message and the individual prompts as user mesages, and added each to message history
# - No clear change in performance vs. v1