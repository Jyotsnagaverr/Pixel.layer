from __future__ import print_function
from tkinter import *
from tkinter import messagebox
from Motion_Detector import BasicMotionDetector
from Stitcher_Algo import Stitcher
from imutils.video import VideoStream
import numpy as np
import datetime
import imutils
import time
import cv2


# ---------------------------- Camera SETUP ------------------------------- #
def start_camera():
    # FPS Counting
    cTime = 0
    pTime = 0
    # initialize the video streams and allow them to warmup
    print("[INFO] Starting cameras...")

    leftStream = VideoStream(src=left_camera_entry.get() + "/video").start()
    rightStream = VideoStream(src=right_camera_entry.get() + "/video").start()
    time.sleep(2.0)

    # initialize the image stitcher, motion detector, and total number of frames read
    stitcher = Stitcher()
    motion = BasicMotionDetector(minArea=15000)
    total = 0

    # loop over frames from the video streams
    while True:
        # grab the frames from their respective video streams
        left = leftStream.read()
        right = rightStream.read()

        # resize the frames
        left = imutils.resize(left, width=400)
        right = imutils.resize(right, width=400)

        # stitch the frames together to form the panorama and frames should be supplied in left-to-right order
        result = stitcher.stitch([left, right])

        # no homography could be computed
        if result is None:
            print("[INFO] Homography could not be computed")
            break

        # convert the panorama to grayscale, blur it slightly, update the motion detector
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        locs = motion.update(gray)

        # only process the panorama for motion if a nice average has been built up
        if total > 32 and len(locs) > 0:
            # initialize the minimum and maximum (x, y)-coordinates, respectively
            (minX, minY) = (np.inf, np.inf)
            (maxX, maxY) = (-np.inf, -np.inf)

            # loop over the locations of motion and accumulate the minimum and maximum locations of the bounding boxes
            for l in locs:
                (x, y, w, h) = cv2.boundingRect(l)
                (minX, maxX) = (min(minX, x), max(maxX, x + w))
                (minY, maxY) = (min(minY, y), max(maxY, y + h))

            # draw the bounding box
            cv2.rectangle(result, (minX, minY), (maxX, maxY), (0, 0, 255), 3)

        # increment the total number of frames read and draw the timestamp on the image
        total += 1
        timestamp = datetime.datetime.now()
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(result, ts, (10, result.shape[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # FPS display
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(left, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
        cv2.putText(right, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
        cv2.putText(result, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)

        # show the output images
        cv2.imshow("Result", result)
        cv2.imshow("Left Camera", left)
        cv2.imshow("Right Camera", right)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

    # do a bit of cleanup
    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    leftStream.stop()
    rightStream.stop()


# ---------------------------- Confirmation ------------------------------- #
def save_file():
    # if entry is not sufficient then warning
    if (len(left_camera_entry.get()) <= 20) or (len(right_camera_entry.get()) <= 20):
        messagebox.showwarning(title="Pixellayer Warning", message="Oops..\nYou have left any field empty")
    else:
        # check for orientation
        is_okay = messagebox.askokcancel(title="Pixellayer Confirmation",
                                         message=f"Left Camera IP: {left_camera_entry.get()}\nRight Camera IP: {right_camera_entry.get()}\nYour IP might look like http://XYZ:UV:MN:ABC:8080\nAre your sure?")

        # if both entries are good enough to start or not
        if is_okay and left_camera_entry.get() != right_camera_entry.get():
            start_camera()
        else:
            messagebox.showerror(title="Pixellayer Error",
                                 message="Both Camera IP is same.\nMake sure you are using different cameras.")


# ---------------------------- UI SETUP ------------------------------- #
window = Tk()
window.title("Pixellayer")
window.config(padx=50, pady=50, bg="white")
window.wm_iconbitmap("icon2.ico")
# window.geometry("644x788")
window.resizable(0, 0)  # It stops window to get minimize or maximize
canvas = Canvas(width=200, height=200, bg="white", highlightthickness=0)
logo = PhotoImage(file="logo1.png")
canvas.create_image(50, 100, image=logo)
canvas.grid(row=0, column=1)

# left camera orientation
Label(text="Left Camera IP ", bg="white", fg="black", font="Helvetica 9").grid(row=1, column=0)
left_camera_entry = Entry(width=33, bg="white", fg="black")
left_camera_entry.grid(row=1, column=1, columnspan=2, sticky="w")
left_camera_entry.insert(0, "http://")
left_camera_entry.focus()

# right camera orientation
Label(text="Right Camera IP ", bg="white", fg="black", font="Helvetica 9").grid(row=2, column=0)
right_camera_entry = Entry(width=33, bg="white", fg="black")
right_camera_entry.grid(row=2, column=1, columnspan=2, sticky="w")
right_camera_entry.insert(0, "http://")

# just a spacer
spacer1 = Label(text="", bg="white")
spacer1.grid(row=3, column=0)

# button for starting camera
add_btn = Button(text="Run", width=20, bg="white", command=save_file)
add_btn.grid(row=4, column=1, sticky="w")

window.mainloop()
