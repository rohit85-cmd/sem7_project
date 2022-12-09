from flask import Flask, render_template, Response
import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import csv
import smtplib
import winsound

from dotenv import load_dotenv
load_dotenv()

    
sender_email = os.getenv('mail')
print(sender_email)
# password = input(str("Enter your gmail password: "))
password = os.getenv('password')
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, password)
print("Login successful to your gmail account")
    

app = Flask(__name__)

camera = cv2.VideoCapture(0)

### implemented dictionary ###
nameMail = {'Rohit Jindamwar': 'rohitjindamwar123@gmail.com',
            'Rajnandini Kadam': 'rajnandini.kadam@walchandsangli.ac.in', 
            'Tejal Mane': 'tejal.mane@walchandsangli.ac.in',
}
### implemented dictionary ###
path = 'imagesDatabase'
imagesList = os.listdir(path)
studentNames = []
images = []
message = "Your Attendance has been Marked"
present = []
presenty ={}


for currentImg in imagesList:
    curImg = cv2.imread(f'{path}/{currentImg}')
    images.append(currentImg)
    studentNames.append(os.path.splitext(currentImg)[0])

students = studentNames.copy()
print(studentNames)

def sound():
    print("reasched")
    frequency = 2500
    duration = 1000
    winsound.Beep(frequency,duration)


def FindEncodings(images):
    encodingList = []
    for img in images:
        img = cv2.imread(f'{path}/{img}')
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # converted to RGB
        encode = face_recognition.face_encodings(img)[0]
        encodingList.append(encode)
    return encodingList


now = datetime.now()
currentDate = now.strftime("%Y-%m-%d")

faceNames = []
check = True

if not camera.isOpened():
    print("Cannot open camera")
    exit()

knownEncodingList = FindEncodings(images)
print("Encoding Done")

count = 0

def generate_frames():
    
    while True:

        # read the camera frame
        success, frame = camera.read()
        if not success:
            break
        else:
            imgS = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # converted to RGB

            if check:

                facesCurFrame = face_recognition.face_locations(imgS)
                encodesCurFrame = face_recognition.face_encodings(
                    imgS, facesCurFrame)

                for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):

                    matches = face_recognition.compare_faces(
                        knownEncodingList, encodeFace)
                    faceDist = face_recognition.face_distance(
                        knownEncodingList, encodeFace)

                    matchIndex = np.argmin(faceDist)

                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.rectangle(frame, (x1, y2-35), (x2, y2),
                                  (0, 255, 0), cv2.FILLED)
                    if matches[matchIndex]:
                        name = studentNames[matchIndex]
                        faceNames.append(name)
                    if matches[matchIndex] == False:
                        name = 'UNKNOWN'

                    cv2.putText(frame, name, (x1+6, y2-6),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    if name in studentNames and name in students:
                        print(name)
                        sound()
                        
                        current_time = now.strftime("%I:%M %p")
                        if name not in presenty:
                            presenty[name]=current_time
                        students.remove(name)

                        

                        
                        with open(currentDate+'.csv', 'w+', newline='') as f:
                            lnwriter = csv.writer(f)
                            lnwriter.writerow([name,current_time])
                        
                            
                        if (name) in nameMail:
                            server.sendmail(sender_email,nameMail[name] , message)
                            print("Email sent to ", nameMail[name])

        if(cv2.waitKey(1)& 0xFF==ord('q')):
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        


@app.route('/')
def index():
    return render_template('faceRecognition.html')

@app.route('/list')
def printlist():
    return render_template('presenty.html',present=presenty, length = len(presenty))
  


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
