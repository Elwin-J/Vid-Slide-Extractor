import os
import random
import sys
from time import perf_counter, sleep
import youtube_dl
import json
import cv2
from multiprocessing.pool import Pool, ThreadPool
import numpy as np
import cProfile
import pstats

def get_lowest_quality(_formats):
    min_fmt = 10000
    min_fmt_url = ''
    for f in _formats:
        fmt_note = f.get('format_note', None)
        if fmt_note and fmt_note.endswith('p'):
            fmt_num = int(fmt_note[:-1])
            if fmt_num < min_fmt:
                min_fmt = fmt_num
                min_fmt_url = f.get('url', None)
    return min_fmt, min_fmt_url


def get_video(vid_url, ytdl_opts, save_to_json=True):
    ydl = youtube_dl.YoutubeDL(ytdl_opts)
    info_dict = ydl.extract_info(vid_url, download=False)
    if save_to_json:
        vid_id = info_dict.get('id', str(random.randint(1_000, 10_000)))
        jsonfilename = f"vid_info_{vid_id}.json"
        with open(jsonfilename, 'w') as f:
            json.dump(info_dict, f)
    return info_dict


done_frames = set()
THRESHOLD = 24.0
def process_vid(vidcap, endframenum, id=0, vidid='_'):
    i = 0
    # vidcap.set(cv2.CAP_PROP_POS_FRAMES, 10_000.0)
    ret, prev = vidcap.read() # starts at 10_000 + 1 if above line was uncommented
    if ret:
        prev:np.ndarray = prev
        done_frames.add(hash(prev.tobytes()))

    while True:
        ret, frame = vidcap.read()
        frame:np.ndarray = frame
        if ret and vidcap.get(cv2.CAP_PROP_POS_FRAMES) <= endframenum:
            framehash = hash(frame.tobytes())
            if framehash not in done_frames:
                diff:np.ndarray = frame-prev
                shp = diff.shape
                dst = np.sum(np.abs(diff))/(shp[0]*shp[1]*shp[2])
                if dst > THRESHOLD:
                    cv2.imwrite(f'BigTests\\{vidid}\\folder{id}\\frame{i}.jpg', frame)
                    prev = frame
                    i += 1
                done_frames.add(framehash)
        else:
            break
    return endframenum, id

def split_vid(vidurl):
    _compute_cap = cv2.VideoCapture(vidurl)
    fps = _compute_cap.get(cv2.CAP_PROP_FPS)
    n_frames = _compute_cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print(f'{fps= }  {n_frames= }')
    n_secs = n_frames/fps
    n_mins = n_secs/60
    print(f'{n_secs= }  {n_mins= }')
    # n_millis = n_secs*1000
    _compute_cap.release()
    vidcaps = [] # list[8]
    if n_mins > 5:
        for i in range(8):
            vc = cv2.VideoCapture(vidurl)
            vc.set(cv2.CAP_PROP_POS_FRAMES, i * n_frames // 8)
            vidcaps.append(vc)
    else:
        print("Vid too short for multithreading, just go single threaded")
        # ...
    return vidcaps, n_frames

def get_stats_for(prof):
    stats1 = pstats.Stats(prof)
    stats1.sort_stats(pstats.SortKey.TIME)
    stats1.print_stats()


def get_vid(vidlink):
    vid_id = vidlink.removeprefix('https://www.youtube.com/watch?v=')
    info_dct = get_video(vidlink, {}, False)

    if info_dct.get('_type', None) != 'playlist':
        print('Video')
    else:
        print('Given link is that of a playlist')
        return

    formats = info_dct.get('formats', None)

    print("Obtaining frames")
    if formats is not None:
        min_format, url = get_lowest_quality(formats)
        caps, n_frames = split_vid(url)
        for cnt, _ in enumerate(caps):
            os.makedirs(f"BigTests\\{vid_id}\\folder{cnt}")
        
        strt = perf_counter()
        # for i, cap in enumerate(caps[:1]):
        #     process_vid(cap, (i+1)*n_frames//8, i)
        # print("Time taken: ", perf_counter() - strt)
        with ThreadPool() as pool:
            results = pool.imap_unordered(lambda tup: process_vid(tup[1], (tup[0]+1)*n_frames//8, tup[0], vid_id), enumerate(caps))
            for r in results:
                print(r)
        print("Time taken: ", perf_counter() - strt)

        # after done
        for c in caps:
            c.release()

    else:
        print("formats not found...")


def main():
    if len(sys.argv) <= 1:
        print("Provide a url on the command line")
        return
    vidlink = sys.argv[1]
    info_dct = get_video(vidlink, {}, False)

    if info_dct.get('_type', None) != 'playlist':
        print('Individual video')
        get_vid(vidlink)
    else:
        print('Given link is that of a playlist')
        links = [ f'https://www.youtube.com/watch?v={ thing.get("id", "3LaVxEX3F0o") }' for thing in info_dct.get('entries', []) ]
        for lnk in links:
            print(f'doing link: {lnk}')
            os.makedirs(f'BigTests\\{lnk.removeprefix("https://www.youtube.com/watch?v=")}')
            get_vid(lnk)
            sleep(0.2)
            # cont = input('continue? [y/n]')
            # if cont.lower() != 'y':
            #     break


if __name__ == '__main__':
    main()