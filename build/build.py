import os, time

build_cmd = """pyinstaller -F --add-data="../inital/*;inital/" --add-data="../assets/*;assets/" ../main.py"""

os.system(build_cmd)

time.sleep(10)