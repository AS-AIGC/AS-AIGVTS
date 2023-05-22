#!/usr/bin/env python3

from pytube import YouTube    # library for downloading YouTube videos
from pydub import AudioSegment    # library for working with audio files
import pysrt
import whisper    # library for sending and receiving messages over a network
from whisper.utils import get_writer
import openai    # library for working with the OpenAI API
import re, os, sys, traceback
from datetime import datetime
from tqdm import tqdm
from googletrans import Translator, LANGUAGES
import config

youtube_list = config.YouTube_List
PREFIX = config.PREFIX
LANGUAGES = config.LANGUAGES

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

def concatenate_srt_file(main, sliced_part, offset):
    # Open the srt file
    main_subtitles = pysrt.open(main)
    sliced_part_subtitles = pysrt.open(sliced_part)

    # Shift start and end timestamp of the sliced part subtitles
    sliced_part_subtitles.shift(minutes=offset)

    # Shift subtiltes index of the sliced part subtitles
    main_subtitles_length = len(main_subtitles)
    for subtitle in sliced_part_subtitles:
        subtitle.index += main_subtitles_length
        main_subtitles.append(subtitle)
    main_subtitles.save(main, encoding='utf-8')

def translate_srt_file_by_googletrans(lang, sliced_part_srt, sliced_part_subtitle_srt):
    translator = Translator()
    subtitles = pysrt.open(sliced_part_srt)
    for subtitle in subtitles:
        translated_subtitle = translator.translate(text=subtitle.text, dest=lang)
        subtitle.text = translated_subtitle.text
    subtitles.save(sliced_part_subtitle_srt, encoding='utf-8')

# iterate over the items in the youtube_list dictionary
for k, v in youtube_list.items():

    #print(f"Downloading {k} ({v})")
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

        with open(f"{PREFIX}{k}.txt", 'w') as out_txt, open(f"{PREFIX}{k}.srt", 'w') as out_srt:

            for lang in LANGUAGES:
                out_offset = open(f"{PREFIX}{k}_{lang}.srt",'w')

            for offset in tqdm(range(mp3_duration_minutes + 1)):
                fname_offset = f"{k}_{offset}_{offset+1}"
                fname_offset_mp3 = f"/tmp/{fname_offset}.mp3"
                slice_audio(mp3_file, fname_offset_mp3, offset)

                result = model.transcribe(fname_offset_mp3, fp16=False)
                txt_writer = get_writer("txt","/tmp/")
                txt_writer(result,f"{fname_offset}.txt")
                srt_writer = get_writer("srt","/tmp/")
                srt_writer(result,f"{fname_offset}.srt")


                with open(f"/tmp/{fname_offset}.txt") as infile:
                    out_txt.write(infile.read() + " ")

                # Concatenate the caption
                concatenate_srt_file(f"{PREFIX}{k}.srt", f"/tmp/{fname_offset}.srt", offset)

                for lang in LANGUAGES:
                    subtitle = translate_srt_file_by_googletrans(lang, f"/tmp/{fname_offset}.srt", f"/tmp/{fname_offset}_{lang}.srt")
                    concatenate_srt_file(f"{PREFIX}{k}_{lang}.srt", f"/tmp/{fname_offset}_{lang}.srt", offset)
                    if os.path.exists(f"/tmp/{fname_offset}_{lang}.srt"):
                        os.remove(f"/tmp/{fname_offset}_{lang}.srt")
        
                if os.path.exists(f"/tmp/{fname_offset}.txt"):
                    os.remove(f"/tmp/{fname_offset}.txt")
                if os.path.exists(f"/tmp/{fname_offset}.srt"):
                    os.remove(f"/tmp/{fname_offset}.srt")
                if os.path.exists(f"/tmp/{fname_offset}.mp3"):
                    os.remove(f"/tmp/{fname_offset}.mp3")

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
    print(os.path.basename(__file__) + "," + k + "," + v + "," + str(seconds) + "," + str(delta_time.total_seconds()))

