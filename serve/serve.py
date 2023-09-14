import time
import os
from pyfingerprint.pyfingerprint import PyFingerprint
from datetime import datetime
from flask import Flask, send_file, jsonify
from flask_cors import CORS
import threading
import sys
from PIL import Image

# Add the directory to sys.path
sys.path.append('/home/sg/Documents/projects/hoptal/biometric/secugen/FDx SDK Pro for Linux v4.0c/FDx_SDK_PRO_LINUX4_X64_4_0_0/python')

# Now you can import the module
from pysgfplib import *
from ctypes import *

sgfplib = PYSGFPLib()
folder_name = "fingerprint_data"
if not os.path.exists(folder_name):
    os.mkdir(folder_name)

print('+++ Call sgfplib.Create()')
result = sgfplib.Create()
print('  Returned : ' + str(result))

if result != SGFDxErrorCode.SGFDX_ERROR_NONE:
    print("  ERROR - Unable to open SecuGen library. Exiting\n")
    exit()

print('+++ Call sgfplib.Init(SGFDxDeviceName.SG_DEV_AUTO)')
result = sgfplib.Init(SGFDxDeviceName.SG_DEV_AUTO)
print('  Returned : ' + str(result))

if result != SGFDxErrorCode.SGFDX_ERROR_NONE:
    print("  ERROR - Unable to initialize SecuGen library. Exiting\n")
    exit()

print('+++ Call sgfplib.OpenDevice(0)')
result = sgfplib.OpenDevice(0)
print('  Returned : ' + str(result))

if result != SGFDxErrorCode.SGFDX_ERROR_NONE:
    print("  ERROR - Unable to open the device. Exiting\n")
    exit()

# ///////////////////////////////////////////////
# // GetDeviceInfo()
cImageWidth = c_int(0)
cImageHeight = c_int(0)
print('+++ Call sgfplib.GetDeviceInfo()')
result = sgfplib.GetDeviceInfo(byref(cImageWidth), byref(cImageHeight))
print('  Returned : ' + str(result))
print('  ImageWidth  : ' + str(cImageWidth.value))
print('  ImageHeight : ' + str(cImageHeight.value))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Define a generic folder name
folder_name = "fingerprint_data"


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def delete_existing_image(fingerprint_folder_path):
    image_path = os.path.join(fingerprint_folder_path, 'image.raw')
    if os.path.exists(image_path):
        os.remove(image_path)


def enroll_fingerprint(fingerprint_folder_path):
    while True:
        delete_existing_image(fingerprint_folder_path)
        print('+++ Call sgfplib.GetImage()')
        cImageBuffer1 = (c_char * cImageWidth.value * cImageHeight.value)()
        result = sgfplib.GetImage(cImageBuffer1)
        print("+++ Call CreateTemplate");
        cMinutiaeBuffer1 = (c_char*sgfplib.constant_sg400_template_size)() 
        result = sgfplib.CreateSG400Template(cImageBuffer1, cMinutiaeBuffer1)
        print('  Returned : ' + str(result))
        if result == SGFDxErrorCode.SGFDX_ERROR_NONE:
            image_path = os.path.join(fingerprint_folder_path, 'image.raw')
            with open(image_path, "wb") as image1File:
                image1File.write(cImageBuffer1)
            template_path = os.path.join(fingerprint_folder_path, 'imagetemplate.min')
            with open(template_path, "wb") as minutiaeFile:
                minutiaeFile.write(cMinutiaeBuffer1)

            return  # Exit the loop and function when the fingerprint is successfully captured
        else:
            print("  ERROR - Unable to capture image. Retrying...\n")
            time.sleep(1)  # Sleep for a while before retrying


@app.route('/enroll', methods=['POST'])
def enroll_fingerprint_route():
    fingerprint_folder_path = os.path.join(folder_name)
    thread = threading.Thread(target=enroll_fingerprint, args=(fingerprint_folder_path,))
    thread.start()
    thread.join()  # Wait for the enrollment thread to finish
    return jsonify(message="Fingerprint enrollment complete.")


@app.route('/sendimage', methods=['GET'])
def send_fingerprint_image():
    timestamp = int(time.time())  # Get current timestamp in seconds
    image_path_raw = f'/home/sg/Documents/projects/hoptal/web/vue/serve/{folder_name}/image.raw'
    jpg_path = f'/home/sg/Documents/projects/hoptal/web/vue/serve/{folder_name}/image.jpg'

    try:
        rawData = open(image_path_raw, 'rb').read()
        imgSize = (300, 400)  # the image size
        img = Image.frombytes('L', imgSize, rawData)
        img.save(jpg_path)  # can give any format you like .png

        if os.path.exists(image_path_raw) and os.path.exists(jpg_path):
            #print(image_path_raw, jpg_path)
            # Send the raw image with the timestamp as a query parameter
            return send_file(jpg_path, mimetype='image/jpg', as_attachment=True)
        else:
            return jsonify(message="Fingerprint image not available yet.")
    except Exception as e:
        return jsonify(message="Error processing the image: " + str(e))


def main():
    app.run(host='0.0.0.0', port=5500)


if __name__ == "__main__":
    main()
