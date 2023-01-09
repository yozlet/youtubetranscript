# youtubetranscript.com
#
# Created by Andy Barry:
# https://github.com/andybarry/youtubetranscript
#
# For license, see the file named "LICENSE" (it's GPL 3.0)

import os
from flask import Flask, request, render_template, Response, escape
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    VideoUnavailable,
    TranscriptsDisabled,
    NoTranscriptAvailable,
)

USE_CACHE = False

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

def xml_format_line(video_id, line):
    start = line["start"]
    duration = line["duration"]
    # end = start+duration
    text = escape(line["text"])
    out = f'<text start="{start}" dur="{duration}">{text}</text>'
    return out


def xml_format_transcript(video_id, trans):
    one_break = 0
    two_break = 5

    out = '<?xml version="1.0" encoding="utf-8" ?><transcript>'
    last_t = 0
    for line in trans:
        out += xml_format_line(video_id, line)
    out += "</transcript>"
    return out


def get_transcript(video_id):
    # Check for a cached version of the transcript
    if USE_CACHE:
        cache_dir = "cache"
        for f in os.listdir(cache_dir):
            if f == video_id:
                # Read the file
                with open(cache_dir + "/" + f, "r") as f2:
                    print("Cache hit")
                    return f2.read()

        print("Cache miss")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatted = xml_format_transcript(video_id, transcript)
    if USE_CACHE:
        f = open(cache_dir + "/" + video_id, "w")
        f.write(formatted)
        f.close()

        # Limit cache to 1000 files
        cache_limit = 1000
        list_of_files = os.listdir(cache_dir)
        if len(list_of_files) > cache_limit:
            # Delete the oldest file
            full_path = [cache_dir + "/{0}".format(x) for x in list_of_files]
            oldest_file = min(full_path, key=os.path.getctime)
            os.remove(oldest_file)
            print("removing ", oldest_file)

    return formatted


@app.route("/")
def root():
    if (
        request.args.get("server_vid") is None
        or len(request.args.get("server_vid")) < 1
    ):
        return render_template("index2.html")

    # Otherwise, do server-side caption getting:

    # Read the youtube link
    video_id = request.args.get("server_vid")
    # print(video_url)
    # # Parse the url
    # f = None
    # if 'youtu.be/' in video_url:
    # f = video_url.find('youtu.be/') + 9
    # elif 'v=' in video_url:
    # f = video_url.find('v=') + 2

    # if f is None:
    # return render_template("get_caption.html", transcript='Failed to parse URL')

    # video_id = video_url[f:f+11]

    # return render_template("output_page.html", video_id=video_id)

    print("video id = ", video_id)
    try:
        transcript = get_transcript(video_id)
    except VideoUnavailable:
        # Render the captcha
        return Response(
            '<?xml version="1.0" encoding="utf-8" ?><error>Error: video unavailable</error>',
            mimetype="text/xml",
        )
    except TranscriptsDisabled:
        return Response(
            '<?xml version="1.0" encoding="utf-8" ?><error>Error: transcripts disabled for that video</error>',
            mimetype="text/xml",
        )
    except NoTranscriptAvailable:
        return Response(
            '<?xml version="1.0" encoding="utf-8" ?><error>Error: No transcript available for that video</error>',
            mimetype="text/xml",
        )
    except Exception as error:
        return Response(
            '<?xml version="1.0" encoding="utf-8" ?><error>:( Unknown error:'
            + str(error)
            + "</error>",
            mimetype="text/xml",
        )
        # return render_template("starting_page.html", header_text='That failed: ' + str(e))

    # return render_template("output_page.html", video_id=video_id, transcript=transcript)
    return Response(transcript, mimetype="text/xml")
    # return render_template("get_caption.html", transcript=transcript)


if __name__ == "__main__":
    # This is used when running locally only.
    app.run(host="127.0.0.1", port=8080, debug=True)
