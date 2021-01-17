import os
import json
import zipfile
import logging
from datetime import datetime
from datetime import timedelta
from logging.handlers import TimedRotatingFileHandler


class ArchivingRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        """
        Do a log rollover. Overriding default method to enable archiving to a zip file.
        """
        filename = os.path.basename(self.baseFilename)
        if not os.path.exists(f"logs/{filename}"):
            return
        if os.path.getsize(f"logs/{filename}") == 0:
            return
        if self.stream:
            self.stream.close()
            self.stream = None

        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%Y-%m")

        if not os.path.exists(f"logs/{year}"):
            os.mkdir(f"logs/{year}")
        if not os.path.exists(f"logs/{year}/{month}"):
            os.mkdir(f"logs/{year}/{month}")

        with open(f"logs/{filename}", "r") as f:
            lines = f.read().splitlines()
            last_line = lines[len(lines) - 2]
            last_line = json.loads(last_line)

        date = datetime.strptime(last_line.get("asctime"), "%Y-%m-%d %H:%M:%S,%f").strftime(
            "%Y-%m-%d"
        )
        if os.path.exists(f"logs/{year}/{month}/{date}.json"):
            i = 1
            while os.path.exists(f"logs/{year}/{month}/{date}_{i:03}.json"):
                i += 1
            i = f"{i:03}"
            newname = f"logs/{year}/{month}/{date}_{i}.json"
        else:
            newname = f"logs/{year}/{month}/{date}.json"

        archive = self.rotation_filename(newname)

        self.rotate(self.baseFilename, archive)
        if not self.delay:
            self.stream = self._open()
        self.archiver()

    def archiver(self):
        """
        Log archiving method.
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        files = self.scan_log_dir("logs/")
        for entry in files:
            if entry.is_file() and ".json" in entry.name:
                if "_" in entry.name:
                    name = entry.name.split("_")[0]
                else:
                    name = entry.name.replace(".json", "")
                entry_date = datetime.strptime(name, "%Y-%m-%d")
                if entry_date < today - timedelta(seconds=10):
                    filepath = "logs/log_archive.zip"
                    with zipfile.ZipFile(filepath, "a") as zipf:
                        zipf.write(entry.path)
                        os.remove(entry.path)

    def scan_log_dir(self, dir):
        """
        File scanning method for archiver
        """
        files = []
        with os.scandir(dir) as entries:
            for entry in entries:
                if entry.is_file() and ".json" in entry.name:
                    files.append(entry)
                if entry.is_dir():
                    directory = os.listdir(entry.path)
                    if len(directory) == 0:
                        os.rmdir(entry.path)
                    else:
                        files.extend(self.scan_log_dir(entry.path))
        return files


# Custom formatter
class CustomStdoutFormatter(logging.Formatter):

    default_fmt = "%(levelname)s: %(message)s ~ %(pathname)s - %(funcName)s | %(asctime)s"
    info_fmt = "%(levelname)s: %(message)s | %(asctime)s"

    def format(self, record):
        """
        Custom formatter for different outputs depending on log level.
        Currently only INFO behaves differently, with less information than other errors.
        """

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.INFO:
            self._style._fmt = CustomStdoutFormatter.info_fmt

        else:
            self._style._fmt = CustomStdoutFormatter.default_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result
