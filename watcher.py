import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from file_organizer import process_file


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events by processing new or modified files."""

    def __init__(self, duplicates_dir: str):
        super().__init__()
        self.duplicates_dir = duplicates_dir

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"Detected new file: {event.src_path}")
            process_file(event.src_path, self.duplicates_dir)

    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"Detected modified file: {event.src_path}")
            process_file(event.src_path, self.duplicates_dir)


def start_watcher(source_dir: str, duplicates_dir: str):
    """Start watching the source directory for new or modified files."""
    event_handler = FileEventHandler(duplicates_dir)
    observer = Observer()
    observer.schedule(event_handler, path=source_dir, recursive=True)
    observer.start()
    logging.info(f"Watching for changes in: {source_dir}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopping watcher...")
    observer.join()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Watch a directory for new or modified files.")
    parser.add_argument('--source', required=True, help='Path to the source directory')
    parser.add_argument('--duplicates', required=True, help='Path to the duplicates directory')
    args = parser.parse_args()

    start_watcher(args.source, args.duplicates)
