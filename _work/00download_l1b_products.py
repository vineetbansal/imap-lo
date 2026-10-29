from datetime import datetime, timezone
import imap_data_access


if __name__ == "__main__":

    start = datetime(2026, 4, 1, tzinfo=timezone.utc)

    for descriptor in ("histrates", "monitorrates", "nhk", "de"):
        results = imap_data_access.query(
            instrument="lo",
            data_level="l1b",
            descriptor=descriptor,
            start_date=start.strftime("%Y%m%d"),
        )
        for result in results:
            file_path = result["file_path"]
            downloaded_file_path = imap_data_access.download(file_path)
            print("  " + str(downloaded_file_path))