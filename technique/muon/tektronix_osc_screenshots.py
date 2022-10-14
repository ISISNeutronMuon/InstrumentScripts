import os
import requests
import sys
import shutil

from datetime import datetime
from io import BytesIO
from PIL import Image
from time import sleep
from zipfile import ZipFile

sys.path.insert(0, os.path.abspath(os.path.join(r"C:\\", "Instrument", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.environ["KIT_ROOT"], "ISIS", "inst_servers", "master")))

from genie_python import genie as g
from genie_python.channel_access_exceptions import UnableToConnectToPVException
from server_common.helpers import register_ioc_start

register_ioc_start("BGRSCRPT_03")

g.set_instrument(None)

# User editable constants
DEVICE_IP = "130.246.50.7"
INSTRUMENT = "EXAMPLE_INST"
MINS_BETWEEN_SCREENSHOTS = 10

TESTING = False  # Stops the permanent while loop running for testing the functions. 

def get_filename(rb_number: str) -> str:
    return rb_number + "_" + datetime.now().replace(microsecond=0).isoformat().replace(":", "-") + ".png"

def get_image() -> Image:
    response = requests.get(f"http://{DEVICE_IP}/image.png", timeout=10)
    return Image.open(BytesIO(response.content))

while not TESTING:
    try:
        print("Creating filenames...")
        run_number = g.get_runnumber()
        rb_number = g.get_rb()
        base_dir = "C:\\data\\"
        zip_base_file_path = base_dir + "NDX" + INSTRUMENT + run_number
        zip_archive_file_path = zip_base_file_path + "_scope_screens.zip"
        zip_temp_file_path = zip_base_file_path + "_scope_screens_temp.zip"

        print("Polling device for image...")
        img = get_image()

        print("Saving image to file system...")
        image_file_name = get_filename(rb_number)
        img.save(base_dir + image_file_name)

        print("Making a temporary copy of the archive zip file...")
        try:
            shutil.copy2(zip_archive_file_path, zip_temp_file_path) #  copy2 preserves metadata
        except IOError as ioe:
            print("Failed to make a copy of the zip archive. Making a new one.")

        print("Writing the new image to the temp zip archive...")
        with ZipFile(zip_temp_file_path, "a") as zip:
            zip.write(base_dir + image_file_name, "oscilloscope_screenshots\\" + image_file_name)

        print("Replacing the original zip file with the temp one...")
        shutil.copy2(zip_temp_file_path, zip_archive_file_path)

        print("Removing temporary files...")
        os.remove(zip_temp_file_path)
        os.remove(base_dir + image_file_name)
    except TypeError as te:
        if str(te) == 'can only concatenate str (not "NoneType") to str':
            print("ERROR: Could not determine run/rb number. Check DAE connection.")
    except AttributeError as ae:
        if str(ae) == "'NoneType' object has no attribute 'get_run_number'":
            print("ERROR: Could not determine run number. Check DAE connection.")
        else:
            print(ae)
    except requests.Timeout as to:
        print(
            "ERROR: Image collection from oscilloscope timed out.\n"
            f"Check that the web server on the device is working by typing {DEVICE_IP} into a browser's address bar. "
            "If the image from the oscillocope's screen is not showing or the page does not load, "
            "the device may need to be rebooted."
            )
    except IOError as ioe:
        print(f"ERROR: Unable to replace {zip_archive_file_path}. It may have been set to read-only by the archive script.\n"
        + str(ioe))

    finally:
        print(f"Waiting for {MINS_BETWEEN_SCREENSHOTS} minutes...")
        sleep(MINS_BETWEEN_SCREENSHOTS * 60)  # Only pull an image after a user defined number of minutes
