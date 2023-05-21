#!/usr/bin/env python3

from pytube import YouTube    # library for downloading YouTube videos
from pydub import AudioSegment    # library for working with audio files
import whisper    # library for sending and receiving messages over a network
from whisper.utils import get_writer
import openai    # library for working with the OpenAI API
import re, os, sys, traceback
from datetime import datetime
from tqdm import tqdm
import config

youtube_list = config.YouTube_List
PREFIX = config.PREFIX

def slice_audio(audio_file, filename, offset):
    # pydub does things in milliseconds
    audio_length = audio_file.duration_seconds
    minutes_duartion = int(audio_length // 60)

    one_minutes = 1 * 60 * 1000
    # Set the start and end timestamp
    start = offset * one_minutes
    # The last part is less than one minute
    end = audio_length if start == minutes_duartion else (offset+1) * one_minutes
    sliced_audio = audio_file[start:end]
    sliced_audio.export(filename, format="mp3")

def rephrase_text(text, language="zh"):
    if language=="zh":
      q = f"請幫我將下列文字更正錯字、加標點符號、轉成台灣的繁體中文，並且讓內容更通順:\n\n{text}\n\n 修正後文字:"
    else:
      q = f"Please rephrase the following text:\n{text}\n\nRevision:"

    rsp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Editor"},
            {"role": "user", "content": q}
        ]
    )

    summary = rsp.get("choices")[0]["message"]["content"].strip()
    return summary

def split_article(article, language="en", max_words=2000):
    word_count = 0   # word count of the current piece
    pieces = []      # list to store article pieces
    current_piece = ""

    if language=="zh":
        max_words = 2000
        lines = re.split(r"，", article)  # split article into lines at each period and space
    else:
        lines = re.split(r"\.\s", article)  # split article into lines at each period and space

    for line in lines:
        if language=="zh":
            line = line + "，"  # add period and space to end of line for grammatical correctness
            words_length = len(line)  # get length of words
        else:
            line = line + ". "  # add period and space to end of line for grammatical correctness
            words = line.split()  # split line into words
            words_length = len(words)  # get length of words list

        if ((word_count + words_length) > max_words):  # if word count exceeds max_words
            current_piece = rephrase_text(current_piece, language)  # send current piece to rephrase_text function for modification
            pieces.append(current_piece)  # append modified piece to pieces list
            current_piece = line  # reset current piece to current line
            word_count = words_length  # reset word count to length of current line's words list
        else:
            current_piece += line  # add current line to current piece
            word_count += words_length  # increment word count by length of current line's words list

    pieces.append(current_piece)  # append last current piece to pieces list
    return pieces  # return list of article pieces

def summarize_text(text, language="en"):
    # Create a question for the AI model to summarize the text
    if language=="zh":
        q = f"請依據下列的影片逐字稿內容，使用繁體中文進行摘要:\n{text}\n\n摘要:"
    else:
        q = f"Please summarize the following text:\n{text}\n\nSummary:"

    # Use OpenAI's GPT-3.5 Turbo model to generate a summary of the text
    rsp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Editor"},
            {"role": "user", "content": q}
        ]
    )

    # Get the summary from the AI model's response
    summary = rsp.get("choices")[0]["message"]["content"].strip()

    # Return the summary
    return summary

# iterate over the items in the youtube_list dictionary
for k, v in youtube_list.items():

    print(f"Downloading {k} ({v})")
    start_time = datetime.now()
    try:

        yt = YouTube(f"https://www.youtube.com/watch?v={v}", use_oauth=True)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_stream.download(output_path="/tmp/", filename=f"audio_{k}")
        audio_file = AudioSegment.from_file(f"/tmp/audio_{k}")
        audio_file.export(f"/tmp/audio_{k}.mp3", format="mp3")
        mp3_file = AudioSegment.from_file(f"/tmp/audio_{k}.mp3", 'mp3')

        # Transcribe the audio

        mp3_duration_minutes = int(mp3_file.duration_seconds // 60)
        seconds = round(mp3_file.duration_seconds - mp3_duration_minutes * 60, 2)
        #print(f"Duration: {mp3_duration_minutes} minutes {seconds} seconds\n")
        model = whisper.load_model("small")

        with open(f"{PREFIX}{k}.txt", 'w') as outfile:
            for offset in tqdm(range(mp3_duration_minutes + 1)):
                fname_offset = f"{k}_{offset}_{offset+1}"
                fname_offset_mp3 = f"/tmp/{fname_offset}.mp3"
                slice_audio(mp3_file, fname_offset_mp3, offset)

                result = model.transcribe(fname_offset_mp3, fp16=False)
                txt_writer = get_writer("txt","/tmp/")
                txt_writer(result,f"{fname_offset}.txt")

                with open(f"/tmp/{fname_offset}.txt") as infile:
                    outfile.write(infile.read() + " ")
        
                if os.path.exists(f"/tmp/{fname_offset}.txt"):
                    os.remove(f"/tmp/{fname_offset}.txt")
                if os.path.exists(f"/tmp/{fname_offset}.mp3"):
                    os.remove(f"/tmp/{fname_offset}.mp3")


        lang = "zh"
        msg = ""

        with open(f"{PREFIX}{k}.txt") as infile:
            lines = infile.read().splitlines()
            for line in lines:
                msg += line + "，"

        msgs = split_article(msg, lang)

        while len(msgs)>1:
            summary = ""
            for m in msgs:
                r = summarize_text(m, lang)
                summary += r
            msgs = split_article(summary, lang)

        with open(PREFIX + k + "-summary.txt", "w") as out_file:
            out_file.write(msgs[0])
            out_file.close()

        if os.path.exists("/tmp/audio_" + k + ".mp3"):
            os.remove("/tmp/audio_" + k + ".mp3")
        if os.path.exists("/tmp/audio_" + k):
            os.remove("/tmp/audio_" + k)


    except BaseException as ex:
        ex_type, ex_value, ex_traceback = sys.exc_info()
        trace_back = traceback.extract_tb(ex_traceback)
        stack_trace = list()
        for trace in trace_back:
            stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

        print("Exception type : %s " % ex_type.__name__)
        print("Exception message : %s" %ex_value)
        print("Stack trace : %s" %stack_trace)

    end_time = datetime.now()
    delta_time = end_time - start_time
    print(k + "," + v + "," + str(delta_time.total_seconds()))

