import os
import shutil
import sys
import cv2
from PIL import Image

def gethist(im):
    res_hist = cv2.calcHist([im], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    res_hist = cv2.normalize(res_hist, res_hist).flatten()
    return res_hist

def get_hist_sim(im1, im2):
    hist1 = gethist(im1)
    hist2 = gethist(im2)

    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL) # higher == more similar

def main():
    if len(sys.argv) < 3:
        print("Wrong syntax")
        return
    in_file = sys.argv[1]
    foldername = sys.argv[2]
    # print(f'{in_file = } \t {foldername = }')
    cmpimg = cv2.imread(in_file)
    # print('reading in_file image complete!')
    for imgfilename in sorted(os.listdir(foldername), key=lambda x: int(x.removeprefix('frame').removesuffix('.jpg'))):
        im2 = cv2.imread(os.path.join(foldername, imgfilename))
        # print(f'reading {imgfilename} image complete!')
        sim = get_hist_sim(cmpimg, im2)
        print(f'Similarity between {in_file} and {imgfilename} is %.4f' % sim)


THRESHOLD = 0.6
def main2():
    pth = 'BigTests'
    fldrs = [ os.path.join(pth, f) for f in os.listdir(pth) ]

    for foldername in fldrs:
        li = os.listdir(foldername)
        fldrs2 = [ os.path.join(foldername, x) for x in li ]
        chkimg = list(filter(lambda x: '.jpg' in x, fldrs2))[0]
        im = cv2.imread(chkimg)
        for fld in fldrs2:
            if '.jpg' not in fld:
                fldrs3 = [ os.path.join(fld, y) for y in os.listdir(fld) ]
                for imm in fldrs3:
                    im2 = cv2.imread(imm)
                    if im is not None:
                        if get_hist_sim(im, im2) > THRESHOLD:
                            print(f'Removing {imm}')
                            try:
                                # hardcoded as of now
                                shutil.move(imm, './toremove')
                            except Exception as e:
                                os.system('del /Q toremove')
                                shutil.move(imm, './toremove')
                    else:
                        print('[error] im is None')
        


if __name__ == '__main__':
    main()