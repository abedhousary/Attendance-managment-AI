import cv2  # importing opencv to capture
import csv  # importing csv library to control csv files
import os  # import os library to use system commands
import shutil  # import shutil to control folders
import time  # import time to add delay between method
import pickle  # pickle to encode images
import face_recognition  # to recognize faces
import mysql.connector  # to create mysql connection
from tkinter import *  # to create  gui window
from imutils import paths  # to create check
from datetime import datetime  # to get system date
from tkinter.messagebox import *  # to create gui message
from tkinter.ttk import Notebook  # using ttk to import notebook
from tkinter.filedialog import askopenfilename  # to open upload files


class face_detect:
    # create haar cascade to detect faces using XML
    facecas = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    # create haar cascade to detect eyes using XML
    eyecas = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml")
    windows_open = False

    def __init__(self):
        # creating connection
        self.cn = mysql.connector.connect(
            host="localhost",  # connecting to server name
            user="root",  # adding user for phpmyadmin
            password="",  # adding password for phpmyadmin
        )
        # intializing cursor
        self.cr = self.cn.cursor()
        # creating database
        self.cr.execute("create database if not exists ams")
        # creating table student
        self.cr.execute("""create table if not exists ams.student (
        id int primary key auto_increment,
        fnames varchar(15),
        lnames varchar(15)
        )""")
        # creating table attendane with composed primary key
        self.cr.execute("""create table if not exists ams.attendance(
            aids int ,
            adate  DATETIME  DEFAULT CURRENT_TIMESTAMP,
            aresult boolean,
            primary key (aids, adate)
        ) """)
        self.cn.commit()  # commiting changes
        self.getlastid()  # getting last id in the database

    def make_dir(self, ids, maindirectory):  # method to create folder
        directory = f"{ids}"  # adding file name
        main_dir = "student_images"  # main directory
        path = os.path.join(main_dir, directory)  # prepare folder
        if os.path.exists(path):  # check if the folder exists
            pass
        else:
            os.mkdir(path)  # create folder

    def check_input(self):  # method to check inputs
        ids = e1.get()  # Get value of entry ID
        fname = e2.get()  # Get value of entry firstname
        lname = e3.get()  # Get value of entry lastname
        if fname == "" or lname == "":  # check if any field is empty
            showerror("Missing data", "Please insert first name and last name")
            return False
        else:
            return True

    def take_picture(self):  # method to take picture and store it in folder
        if self.check_input():  # checking inputs
            ids = e1.get()  # getting id entry value
            fname = e2.get()  # getting firstname entry value
            lname = e3.get()  # getting lastname entry value
            directory = f"{e1.get()}"  # assigning name
            # making folder in the directory
            self.make_dir(ids, "student_images")
            first_read = True  # check if first time starting camera
            cap = cv2.VideoCapture(0)  # create object to obtain video
            ret, img = cap.read()  # start read from camera
            while ret:  # check if camera started
                ret, img = cap.read()  # capture frame by frame
                if ret == False:  # stop camera
                    break
                # reading the image from video
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # reading the image from video
                gray = cv2.bilateralFilter(gray, 5, 1, 1)
                faces = face_detect.facecas.detectMultiScale(
                    gray, 1.3, 5)  # detecting faces
                if len(faces) > 0:  # check how many faces in frame
                    for (x, y, w, h) in faces:  # looping through face map
                        # detect face full image
                        roi_face = gray[y: y + h, x: x + w]
                        # detect  face croped image
                        roi_face_clr = img[y: y + h, x: x + w]
                        eyes = face_detect.eyecas.detectMultiScale(
                            roi_face, 1.3, 5)  # detect eyes
                        if (len(eyes) >= 2):  # check if eyes present to create to take images
                            if first_read:  # check if first time reading from camera
                                for i in range(2):  # started loop to get two photos
                                    ret, img = cap.read()  # read faces from camera
                                    # creating images in folder using id as the name
                                    cv2.imwrite(
                                        f"./student_images/{directory}/{ids}-{i}.jpg", roi_face_clr, )  # saving image
                                    # waiting  1 second between each frame
                                    time.sleep(1)
                                cap.release()  # show image
                                cv2.destroyAllWindows()  # close camera
                                self.cr.execute("insert into ams.student (fnames,lnames) values (%s,%s)",
                                                (fname, lname))  # mysql query to insert detect person name and lastname in database
                                self.cn.commit()  # commit changes
                                # show message on screen
                                showinfo("AMS", f"{fname + lname} Registered")
                                self.extract_face()  # create encode file using added images
                                self.getlastid()  # getting last id from database
                        else:  # if no eyes detected put message on cam frame
                            if first_read:  # when camera starts check if eyes appear in frame
                                cv2.putText(
                                    img,
                                    "No eyes detected",
                                    (70, 70),
                                    cv2.FONT_HERSHEY_PLAIN,
                                    3,
                                    (0, 0, 255),
                                    2,
                                )
                cv2.imshow("img", img)  # show result
                k = cv2.waitKey(33)  # wait milliseconds
                if k == 27:  # when escape key pressed
                    break
            cap.release()  # everything done release capture
            cv2.destroyAllWindows()  # destroy cam frame
            self.clear()  # clear interface

    def extract_face(self):  # method to create file using stored images
        # get all images in the directory
        imgpath = list(paths.list_images("./student_images"))
        knownEncodings = []  # create list to store know images
        knownNames = []  # create list to store unkown images
        for (i, imagePath) in enumerate(imgpath):  # iterate through known images
            name = imagePath.split(os.path.sep)[-1]  # getting images name
            image = cv2.imread(imagePath)  # reading image
            # adding colors to camera
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(
                rgb, model="hog")  # get face
            encodings = face_recognition.face_encodings(
                rgb, boxes)  # create encoding use faces
            for encoding in encodings:
                # add faces of known images (stored images)
                knownEncodings.append(encoding)
                # add name of known images (stored images)
                knownNames.append(name)
        # create dictionary with encoding and knownnames
        data = {"encodings": knownEncodings, "names": knownNames, }
        f = open("face_enc", "wb")  # open file face_enc with write and binary
        f.write(pickle.dumps(data))  # write all data in file
        f.close()  # close the file

    def recognize(self):  # method to recognize face using live video and compare it with stored images
        data = pickle.loads(open("face_enc", "rb").read()
                            )  # reading from face_enc
        video_capture = cv2.VideoCapture(0)  # creating camera frame
        c = 0  # initializing variable
        counts = []  # initializing variable
        waittime = 0  # initializing variable
        name = "Unknown"  # initializing variable with default name
        while True:  # keep running
            ret, frame = video_capture.read()  # creating camera frame
            # adding color for frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detect.facecas.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )  # adding rectange shape for each face in camera
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # adding color
            encodings = face_recognition.face_encodings(rgb)  # detect faces
            names = []  # initializing list
            cv2.putText(frame, "Press ESCAPE to exit", (65, 450), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2, cv2.LINE_4,)  # adding text in camera frame
            for encoding in encodings:
                matches = face_recognition.compare_faces(
                    data["encodings"], encoding)  # comparing photos
                if True in matches:  # if recognized face have image stored
                    # iterate through know images
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    for i in matchedIdxs:  # looping through names
                        name = data["names"][i]  # adding name
                        # geting id from full name
                        student_id = name.split("-")[0]
                        counts.append(student_id)  # adding id to the list
                        waittime += 1  # start delay
                        if waittime == 5:  # check if window stayed for 5 secs
                            while c < 1:  # check if two faces appear on camera
                                c += 1  # adding value
                                # iterating throught ids detected on camera
                                for id in set(counts):
                                    self.cr.execute("insert into ams.attendance (aids,aresult) values (%s,%s)",
                                                    (id, True))  # insert student in attendace list
                                    self.cn.commit()  # commit changes
                                cv2.imshow("Frame", frame)  # show image
                    names.append(name)  # adding names to list
                for ((x, y, w, h), name) in zip(faces, names):  # show name on top of face
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 255, 0), 2)  # creating rectange on each face
                    cv2.putText(  # adding student name above face if detected
                        frame,
                        name,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.75,
                        (0, 255, 0),
                        2,
                    )
            cv2.imshow("Frame", frame)  # show image
            k = cv2.waitKey(33)  # wait 33 miliseconds
            if waittime >= 10:  # if no face detected add unknown name above each face
                if name != "Unknown":  # if face detected
                    showinfo("Congrats!!",
                             "You have been added to the attendance")  # show message
                    break  # close window
            if k == 27:  # wait for escape key to quit
                break
        video_capture.release()  # show image
        cv2.destroyAllWindows()  # closing window

    def clear(self):
        e1.delete(0, END)  # clear id entry
        e2.delete(0, END)  # clear first name entry
        e3.delete(0, END)  # clear last name entry

    def getlastid(self):  # getting last id in database
        # sql query to get last id from table
        self.cr.execute("select * from ams.student order by id desc limit 1")
        if len(self.cr.fetchall()) == 0:  # check if table doesn't contain students
            v1.set("1")  # add value to id entry
        else:
            self.cr.execute(
                "select id from ams.student order by id desc limit 1")  # sql query to get last id from table
            for row in self.cr.fetchall():  # check if table doesn't contain students
                v1.set(int(row[0]) + 1)  # add value to id entry

    def one_window(self, window):  # method to keep only one window open
        face_detect.windows_open = False  # adding false value if window closes
        window.destroy()  # closing window

    def show_students(self):  # method to get students list
        if face_detect.windows_open == False:  # check if another window opened
            face_detect.windows_open = True  # True value if new window opened
            win2 = Tk()  # create window
            win2.title("Students List")  # adding title for window
            width = 600  # adding window width
            height = 400  # adding window height
            sw = win2.winfo_screenwidth()  # get screen width
            sh = win2.winfo_screenheight()  # get screen height
            x = (sw / 2) - (width / 2)  # getting width in center
            y = (sh / 2) - (height / 2)  # getting height in center
            # adding width and height to the window
            win2.geometry("%dx%d+%d+%d" % (width, height, x, y))
            headerdata = "{:^40}{:^40}{:^40}".format(
                "ID", "First Name", "Last Name")  # adding table header
            # adding label with header text
            header = Label(win2, text=headerdata)
            header.pack()  # adding on window
            sc = Scrollbar(win2)  # intialize scroll bar
            # adding scrollbar on the right side of window
            sc.pack(fill=Y, side=RIGHT)
            lis = Listbox(win2, yscrollcommand=sc.set, width=100,
                          height=200)  # intialize list
            lis.pack()  # adding list in window
            # giving scroll bar command to scroll horizontal
            sc.config(command=lis.yview)
            # sql query to get all students from table
            self.cr.execute("select * from ams.student")
            for row in self.cr.fetchall():  # get data
                records = "{:>52}{:>40}{:>45}".format(
                    row[0], row[1], row[2])  # formating names
                lis.insert(END, records)  # adding data to the list
            # adding method to close button on window
            win2.protocol("WM_DELETE_WINDOW", lambda: app.one_window(win2))
            win2.mainloop()  # show window

    def export_sheet(self):  # method to export names as csv file
        with open("students_sheet.csv", "w+", newline='') as sheet:  # creating csv file
            # intialize csv writer
            data_writer = csv.writer(sheet, delimiter=",")
            Header = "ID", "FullName", "Date and Time", "Present"  # adding header for csv file
            data_writer.writerow(Header)  # writing header in file
            date = f"{datetime.today().date()}%"  # getting today system date
            self.cr.execute(
                """SELECT
                            ams.student.id,
                            concat(ams.student.fnames,' ',ams.student.lnames),
                            ams.attendance.adate,
                            ams.attendance.aresult
                            FROM
                            ams.attendance
                            INNER JOIN ams.student ON ams.attendance.aids = ams.student.id
                            WHERE
                            ams.attendance.adate like %s""",
                (date,))  # query to get all attendace from today's date

            data_writer.writerows(self.cr.fetchall())  # write data to the file

    def update_window(self):  # method for update window
        if face_detect.windows_open == False:  # check if window already opened
            face_detect.windows_open = True  # adding true value if window opens

            def clear():  # method to clear entries
                en1.delete(0, END)  # clear id entry
                en2.delete(0, END)  # clear first name entry
                en3.delete(0, END)  # clear last name entry

            def update():  # method to update record values
                ids = en1.get()  # get id from entry
                fname = en2.get()  # get first name entry
                lname = en3.get()  # get last name entry
                if ids == "" or fname == "" or lname == "":  # check if empty entries exists
                    showerror(
                        "Missing data", "please make sure you inserted required data", parent=win3)  # show message
                    en1.focus()  # focus on id entry
                else:
                    self.cr.execute(
                        "select * from ams.student where id = %s", (en1.get(),))  # query to select student by id
                    if len(self.cr.fetchall()) == 0:  # check if data exists
                        showerror(
                            "Not Found", "Unable to find student with this id", parent=win3)  # show meesage
                    else:
                        directory = f"{en1.get()}"  # adding file name
                        # making folder in the directory
                        self.make_dir(ids, "student_images")  # creating folder
                        first_read = True  # check if first time starting camera
                        # create object to obtain video
                        cap = cv2.VideoCapture(0)  # create camera frame
                        ret, img = cap.read()  # start reading
                        while ret:
                            ret, img = cap.read()  # capture frame by frame
                            if ret == False:  # stop camera
                                break
                            # reading the image from video
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            # reading the image from video
                            gray = cv2.bilateralFilter(gray, 5, 1, 1)
                            faces = face_detect.facecas.detectMultiScale(
                                gray, 1.3, 5)  # detecting faces
                            if len(faces) > 0:  # check how many faces exists
                                for (x, y, w, h) in faces:  # iterate through faces
                                    # detect face full image
                                    roi_face = gray[y: y + h, x: x + w]
                                    # detect  face croped image
                                    roi_face_clr = img[y: y + h, x: x + w]
                                    eyes = face_detect.eyecas.detectMultiScale(
                                        roi_face, 1.3, 5)  # detect eyes
                                    if (len(eyes) >= 2):  # check if eyes present to create to take images
                                        if first_read:  # check if first time reading from camera
                                            for i in range(2):  # loop to save two images
                                                ret, img = cap.read()  # read from camera
                                                # creating images in folder using id as the name
                                                cv2.imwrite(f"./student_images/{directory}/{ids}-{i}.jpg",
                                                            roi_face_clr, )  # sae images
                                                time.sleep(1)  # wait 1 seconds
                                            cap.release()  # show image
                                            cv2.destroyAllWindows()  # close camera frame
                                            self.cr.execute(
                                                "update ams.student set fnames = %s ,lnames = %s where id = %s ",
                                                (fname, lname, en1.get()))  # query to update student data
                                            self.cn.commit()  # commit changes
                                            showinfo(
                                                "AMS", f"{fname + lname} record updated ")  # show message
                                            clear()  # clear all entries
                                            win3.focus()  # focus on window
                                            self.extract_face()  # create encode file using added images
                                            self.getlastid()  # get last id from database
                                    else:  # if no eyes detected put message on cam frame
                                        if first_read:
                                            cv2.putText(
                                                img,
                                                "No eyes detected",
                                                (70, 70),
                                                cv2.FONT_HERSHEY_PLAIN,
                                                3,
                                                (0, 0, 255),
                                                2,
                                            )  # show text in camera frame
                            cv2.imshow("img", img)  # show result
                            a = cv2.waitKey(1)
                            k = cv2.waitKey(33)  # wait for 33 milisecond
                            if k == 27:  # check if escape key clicked
                                break  # close window
                        cap.release()  # everything done release capture
                        cv2.destroyAllWindows()  # destroy cam frame
                        self.clear()  # clear interface

            def delete():  # method to delete record
                ids = en1.get()  # get id from entry
                if ids == "":  # check if id entry empty
                    showerror("Missing data",
                              "please make sure you insert id", parent=win3)  # show message
                    en1.focus()  # focus on id entry
                else:
                    self.cr.execute(
                        "select * from ams.student where id = %s", (en1.get(),))  # query to select student by id
                    if len(self.cr.fetchall()) == 0:  # check if data exists
                        showerror(
                            "Not Found", "Unable to find student with this id", parent=win3)  # show message
                    else:
                        directory = f"{ids}"  # get id as file name
                        main_dir = "student_images"  # get folder to save folder
                        path = os.path.join(
                            main_dir, directory)  # prepare folder
                        if os.path.exists(path):  # check if the folder exists
                            shutil.rmtree(path)  # remove folder
                        self.cr.execute(
                            "delete from ams.student where id = %s ", (en1.get(),))  # query to delete studnet by id
                        self.cn.commit()  # commit changes
                        clear()  # clear all entries
                        showinfo("Done", "Student Deleted",
                                 parent=win3)  # show message
                        win3.focus()  # focus on window

            def view_student():  # method to get studnet data
                self.cr.execute(
                    "select * from ams.student where id = %s ", (en1.get(),))  # query to select student by id
                if len(self.cr.fetchall()) == 0:  # check if student exists
                    showerror(
                        "Not Found", "No Record with this id found", parent=win3)  # show message
                else:
                    self.cr.execute(
                        "select * from ams.student where id = %s ", (en1.get(),))  # query to select student by id
                    clear()  # clear entries
                    for row in self.cr.fetchall():  # iterate through data
                        en1.insert(END, row[0])  # insert id to entry
                        en2.insert(END, row[1])  # insert first name to entry
                        en3.insert(END, row[2])  # insert last name to entry

            win3 = Toplevel()  # create top level window
            win3.resizable(0, 0)  # make window unresizable

            width = 600  # set window width
            height = 400  # set window height
            sw = win3.winfo_screenwidth()  # get screen width
            sh = win3.winfo_screenheight()  # get screen height
            x = (sw / 2) - (width / 2)  # get center position horizontally
            y = (sh / 2) - (height / 2)  # get center position vertically
            # assigning width and height to window
            win3.geometry("%dx%d+%d+%d" % (width, height, x, y))
            win3.title("Update and delete students")  # adding title to window
            lb = Label(win3, text="ID", font=(
                ("Arial"), 13))  # adding label id
            lb1 = Label(win3, text="First Name", font=(
                ("Arial"), 13))  # adding first name label
            lb2 = Label(win3, text="Last Name", font=(
                ("Arial"), 13))  # adding last name label
            en1 = Entry(win3, font=(("Arial"), 13))  # adding id entry
            en2 = Entry(win3, font=(("Arial"), 13))  # adding first name entry
            en3 = Entry(win3, font=(("Arial"), 13))  # adding last name entry
            b1 = Button(win3, text=f"Update\nName or Image",
                        width=13, font=(("Arial"), 10), command=update)  # button to update record
            b2 = Button(win3, text="Delete\nStudent ", width=13,
                        font=(("Arial"), 10), fg="red", command=delete)  # button to delete record
            b3 = Button(win3, text="View\nStudent ", width=13,
                        font=(("Arial"), 10), command=view_student)  # button to select studnet data
            b4 = Button(win3, text="Close", width=13, font=(
                ("Arial"), 10), command=lambda: app.one_window(win3))  # button to close window
            # adding widget to window
            lb.grid(row=0, column=0, padx=20, pady=20)
            # adding widget to window
            lb1.grid(row=1, column=0, padx=20, pady=20)
            # adding widget to window
            lb2.grid(row=2, column=0, padx=20, pady=20)
            # adding widget to window
            en1.grid(row=0, column=1, padx=20, pady=20)
            en2.grid(row=1, column=1, padx=20)  # adding widget to window
            en3.grid(row=2, column=1, padx=20)  # adding widget to window

            b1.grid(row=4, column=0, padx=50)  # adding widget to window
            b2.grid(row=4, column=1, padx=35)  # adding widget to window
            b3.grid(row=4, column=2, padx=35)  # adding widget to window
            b4.grid(row=5, column=1, pady=10)  # adding widget to window
            # adding close method to window close button
            win3.protocol("WM_DELETE_WINDOW", lambda: app.one_window(win3))
            win3.mainloop()  # show window

    def attendance_sheet(self):  # method to show attendance
        def loadbydate():  # method to load data by date
            date = e.get()  # get date from entry
            if date == "":  # if date is empty
                showerror("Search", "Please insert date",
                          parent=win4)  # show message
            else:
                searchdate = f"{date}%"  # format date
                self.cr.execute(
                    """SELECT
	                ams.student.id,
                    concat(ams.student.fnames,' ',ams.student.lnames),
                    ams.attendance.adate,
                    ams.attendance.aresult
                    FROM
                    ams.attendance
                    INNER JOIN ams.student ON ams.attendance.aids = ams.student.id
                    WHERE
                    ams.attendance.adate like %s""",
                    (searchdate,))  # query to select data by date
                if len(self.cr.fetchall()) == 0:  # check if data exists
                    lis.delete(0, END)  # clear list
                else:
                    self.cr.execute(
                        """SELECT
                        ams.student.id,
                        concat(ams.student.fnames,' ',ams.student.lnames),
                        ams.attendance.adate,
                        ams.attendance.aresult
                        FROM
                        ams.attendance
                        INNER JOIN ams.student ON ams.attendance.aids = ams.student.id
                        WHERE
                        ams.attendance.adate like %s""",
                        (searchdate,))  # query to select data by date
                    lis.delete(0, END)  # clear data in list
                    for row in self.cr.fetchall():  # get data
                        date = str(row[2]).split(" ")  # format date
                        # get date with timestamp
                        fdate = f"{date[0]} {date[1]}"
                        if row[3] == 1:  # check if record attendace is true
                            present = "Present"
                        records = "{:>20}{:^80}{:^20}{:>30}".format(
                            row[0], row[1], fdate, present)  # format data
                        lis.insert(END, records)  # add data to list

        def refresh():  # method to get new data
            present = ""
            date = f"{datetime.today().date()}%"  # get system date
            self.cr.execute(
                """SELECT
                    ams.student.id,
                    concat(ams.student.fnames,' ',ams.student.lnames),
                    ams.attendance.adate,
                    ams.attendance.aresult
                    FROM
                    ams.attendance
                    INNER JOIN ams.student ON ams.attendance.aids = ams.student.id
                    WHERE
                    ams.attendance.adate like %s""",
                (date,))  # query to select data by date
            lis.delete(0, END)  # clear list from data
            for row in self.cr.fetchall():  # get data
                date = str(row[2]).split(" ")  # get date
                fdate = f"{date[0]} {date[1]}"  # get date with timestamp
                if row[3] == 1:  # check if record attendace is true
                    present = "Present"
                records = "{:>20}{:^80}{:^20}{:>30}".format(
                    row[0], row[1], fdate, present)  # format data
                lis.insert(END, records)  # insert data in list

        if face_detect.windows_open == False:  # check if another window already opened
            face_detect.windows_open = True  # adding true new window opened
            win4 = Tk()  # create new frame
            win4.title("Students Present list")  # adding title to window
            width = 600  # set width
            height = 400  # set height
            sw = win4.winfo_screenwidth()  # get screen width
            sh = win4.winfo_screenheight()  # get screen height
            x = (sw / 2) - (width / 2)  # get center position horizontally
            y = (sh / 2) - (height / 2)  # get center position vertically
            # assigning width and height to window
            win4.geometry("%dx%d+%d+%d" % (width, height, x, y))
            headerdata = "{:^1}{:^90}{:^30}{:>20}".format(
                "ID", "Name", "Date/Time", "Presence")  # format data in header
            header = Label(win4, text=headerdata)  # add label with header data
            header.pack()  # display on window
            sc = Scrollbar(win4)  # adding scrollbar
            # add scroll bar in right side of window
            sc.pack(fill=Y, side=RIGHT)
            lis = Listbox(win4, yscrollcommand=sc.set,
                          width=100, height=20)  # adding list
            lis.pack()  # display on window
            sc.config(command=lis.yview)  # scroll command to scroll vertically
            frame = Frame(win4, width=590, height=50)  # adding frane
            frame.pack()  # show frame
            lb = Label(frame, text="Enter a date\nyyyy-mm-dd",
                       font=("Arial", 9))  # adding label with date format
            lb.place(x=100, y=10)  # show on window
            e = Entry(frame)  # create entry for date
            e.place(x=200, y=10)  # show entry on window
            btn = Button(frame, text="Load", width=9,
                         font=("Arial", 9), command=loadbydate)  # button to get date
            btn.place(x=350, y=5)  # show button on window
            btn1 = Button(frame, text="Refresh", width=9,
                          font=("Arial", 9), command=refresh)  # button to refresh list
            btn1.place(x=450, y=5)  # show button on window

            present = ""  # create empty variable
            date = f"{datetime.today().date()}%"  # get system date
            self.cr.execute(
                """SELECT
                    ams.student.id,
                    concat(ams.student.fnames,' ',ams.student.lnames),
                    ams.attendance.adate,
                    ams.attendance.aresult
                    FROM
                    ams.attendance
                    INNER JOIN ams.student ON ams.attendance.aids = ams.student.id
                    WHERE
                    ams.attendance.adate like %s""",
                (date,))  # query to get attendance
            for row in self.cr.fetchall():  # get data from table
                date = str(row[2]).split(" ")  # get full date
                fdate = f"{date[0]} {date[1]}"  # get date with timestamp
                if row[3] == 1:  # check if student present
                    present = "Present"  # adding present value
                records = "{:>20}{:^80}{:^20}{:>30}".format(
                    row[0], row[1], fdate, present)  # formating data
                lis.insert(END, records)  # insert data to the list
            # adding method to window close button
            win4.protocol("WM_DELETE_WINDOW", lambda: app.one_window(win4))
            win4.mainloop()  # show window

    def close(self):  # method to close window and databse connector
        root.destroy()  # close main window
        self.cr.close()  # close connection cursor
        self.cn.close()  # close connection

    def upload_image(self):  # method to upload fake image
        self.getlastid()  # method to get last id in database
        try:
            directory = e1.get()  # get id as file name
            file_path = askopenfilename(
                filetypes=[('Image Files', '*jpg *jpeg *png')])  # option to choose file with jpg and jpeg and png extension
            self.make_dir(directory, "student_images")  # create file with id
            des = os.path.join("./student_images",
                               str(directory))  # adding photo
            shutil.copy(file_path, des)  # make a copy
            self.cr.execute("insert into ams.student (fnames,lnames) values (%s,%s) ",
                            (f"module{directory}", f"module{directory}"))  # query to insert data to database
            self.cn.commit()  # commit changes
            showinfo("Upload", "Upload successfully")  # show message on screen
            self.getlastid()  # get last id in database
        except:
            # show message on screen
            showerror("Upload", "You must choose an image")


if __name__ == "__main__":
    # create object for face_detect class
    root = Tk()  # intialize window
    root.resizable(0, 0)  # make window not resizable
    # centering window on screen
    width = 600  # adding window width
    height = 400  # adding window height
    sw = root.winfo_screenwidth()  # getting screen width
    sh = root.winfo_screenheight()  # getting screen heihgt
    x = (sw / 2) - (width / 2)  # getting center in horizantal
    y = (sh / 2) - (height / 2)  # getting center in vertical
    # assigning width and height to window
    root.geometry("%dx%d+%d+%d" % (width, height, x, y))
    root.title("Attendance Management System ")  # adding title for window
    notebook = Notebook(root)    # add notebook
    notebook.pack(expand=True, fill=BOTH)    # adding to window
    # creating new frames
    frame1 = Frame(notebook, width=400, height=200)  # creating new frame
    frame2 = Frame(notebook, width=400, height=200)  # creating new frame

    frame1.pack(fill="both", expand=True)  # adding frames to window
    frame2.pack(fill="both", expand=True)  # adding frames to window

    # Widgets in Frame1
    lb = Label(frame1, text="ID", font=(("Arial"), 13))  # adding label for id
    lb1 = Label(frame1, text="First Name", font=(
        ("Arial"), 13))  # adding label for first name
    lb2 = Label(frame1, text="Last Name", font=(
        ("Arial"), 13))  # adding label for last name
    v1 = StringVar()  # creating string variable
    e1 = Entry(frame1, font=(("Arial"), 13), textvariable=v1,
               state="disabled")  # adding entry for id
    e2 = Entry(frame1, font=(("Arial"), 13))  # adding Entry for first name
    e3 = Entry(frame1, font=(("Arial"), 13))  # adding Entry for last name
    app = face_detect()  # creating class object
    b2 = Button(
        frame1, text="Register", width=13, command=app.take_picture, font=(("Arial"), 13)
    )  # button to register new student
    b3 = Button(frame1, text="Update", width=13, font=(
        ("Arial"), 13), command=app.update_window)  # Button to update window
    b4 = Button(frame1, text="View Students", width=13,
                font=(("Arial"), 13), command=app.show_students)  # Button to view students
    b5 = Button(frame1, text="Quit", width=13, font=(
        ("Arial"), 13), height=2, command=root.destroy)  # Button to close window
    b6 = Button(frame1, text="Train\nModel",
                width=13, font=(("Arial"), 12), command=app.upload_image)  # Button to upload fake image

    lb.grid(row=0, column=0, padx=20, pady=20)  # adding button on window
    lb1.grid(row=1, column=0, padx=20, pady=20)  # adding button on window
    lb2.grid(row=2, column=0, padx=20, pady=20)  # adding button on window

    e1.grid(row=0, column=1, padx=20, pady=20)  # adding button on window
    e2.grid(row=1, column=1, padx=20)  # adding button on window
    e3.grid(row=2, column=1, padx=20)  # adding button on window

    b2.grid(row=4, column=0, padx=25)  # adding button on window
    b3.grid(row=4, column=1)  # adding button on window
    b4.grid(row=4, column=2)  # adding button on window
    b5.grid(row=5, column=1, columnspan=1, pady=10)  # adding button on window
    b6.grid(row=5, column=0, padx=25, pady=10)  # adding button on window
    # Ending of widgets in Frame1
    # Widgets in Frame2
    btn = Button(frame2, text="Take Attendance", width=14, command=app.recognize, font=(
        ("Arial"), 13))  # button to take attendance
    btn.pack(pady=20)  # adding button on window
    btn1 = Button(frame2, text="Attendance sheet", width=14,
                  font=(("Arial"), 13), command=app.attendance_sheet)  # button to get attendance sheet
    btn1.pack(pady=20)  # adding button on window
    btn2 = Button(frame2, text="Export sheet", width=14,
                  font=(("Arial"), 13), command=app.export_sheet)  # button to export sheet
    btn2.pack(pady=20)  # adding button on window
    btn3 = Button(frame2, text="Quit !",
                  command=root.destroy, width=14, font=(("Arial"), 13))  # button to quit
    btn3.pack(pady=20)  # adding button on window

    # Ending of widgets in Frame2
    # add frames as tabs in notebook
    notebook.add(frame1, text="Registration")  # adding registration tab
    notebook.add(frame2, text="Attendance")  # adding attendace tab
    # adding method to close window
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()  # show window
