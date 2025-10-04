import cv2
import time
import os
import threading
import argparse
import re
from queue import Queue, Empty

# Default configuration
DEFAULT_SAVE_FOLDER = os.path.join(os.path.dirname(__file__), "current_image")
CAPTURE_INTERVAL = 10.0  # seconds


class CameraWorker:
    """Background camera capture worker that continuously reads frames.

    The latest frame is kept in a thread-safe queue of size 1 (always the newest).
    """

    def __init__(self, src=0, test_images=None):
        self.src = src
        self.test_images = test_images or []
        self._stop_event = threading.Event()
        self._thread = None
        self._frame_q = Queue(maxsize=1)
        self._cap = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="CameraWorker", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap and hasattr(self._cap, 'release'):
            try:
                self._cap.release()
            except Exception:
                pass

    def _open_capture(self):
        if self.test_images:
            # In test mode we don't open a real camera
            return None
        cap = cv2.VideoCapture(self.src)
        if not cap.isOpened():
            raise RuntimeError("Could not open webcam")
        return cap

    def _run(self):
        # If test images provided, iterate them; otherwise read from webcam
        if self.test_images:
            for p in self.test_images:
                if self._stop_event.is_set():
                    break
                frame = cv2.imread(p)
                if frame is None:
                    continue
                # keep only the latest frame in queue
                try:
                    self._frame_q.get_nowait()
                except Empty:
                    pass
                self._frame_q.put(frame)
                # small sleep to simulate continuous capture
                time.sleep(0.1)
            return

        try:
            self._cap = self._open_capture()
        except Exception as e:
            print(f"Error opening capture: {e}")
            return

        while not self._stop_event.is_set():
            ret, frame = self._cap.read()
            if not ret:
                # avoid busy loop on failure
                time.sleep(0.1)
                continue
            try:
                self._frame_q.get_nowait()
            except Empty:
                pass
            self._frame_q.put(frame)

    def get_latest_frame(self, timeout=0.0):
        try:
            return self._frame_q.get(timeout=timeout)
        except Empty:
            return None


def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def saver_loop(camera: CameraWorker, save_folder: str, interval: float, stop_event: threading.Event, count: int = None):
    """Save latest frame every `interval` seconds without blocking the camera thread.

    This function runs in the main thread (or a dedicated thread) and uses a timer to decide
    when to save, but it never sleeps for the whole interval — it waits with a timeout so it
    can react to stop_event quickly.
    """
    ensure_folder(save_folder)
    next_save = time.time()
    saved = 0
    while not stop_event.is_set():
        now = time.time()
        # if it's time to save (or overdue), attempt to get the latest frame
        if now >= next_save:
            frame = camera.get_latest_frame(timeout=0.5)
            if frame is not None:
                # write to a temp file first to avoid partial files during rotation
                temp_name = os.path.join(save_folder, "image_temp.jpg")
                try:
                    cv2.imwrite(temp_name, frame)
                    # rotate and rename files so latest is image_1_<timestamp>.jpg
                    try:
                        rotate_and_save(save_folder, temp_name, keep=5)
                    except Exception as e:
                        print(f"Warning: rotate_and_save failed: {e}")
                except Exception as e:
                    print(f"Failed to write image to {temp_name}: {e}")
                saved += 1
                if count is not None and saved >= count:
                    break
            else:
                print("No frame available to save at", time.strftime("%Y-%m-%d %H:%M:%S"))
            next_save += interval
        # wait a short time so we don't busy-wait, but remain responsive
        time.sleep(0.1)


def parse_args():
    p = argparse.ArgumentParser(description="Non-blocking camera capture that saves every interval.")
    p.add_argument("--save-folder", "-o", default=DEFAULT_SAVE_FOLDER, help="Folder to save images")
    p.add_argument("--interval", "-i", type=float, default=CAPTURE_INTERVAL, help="Seconds between saved images")
    p.add_argument("--src", type=int, default=0, help="Camera device index")
    p.add_argument("--test", action="store_true", help="Run in test mode using sample images")
    p.add_argument("--count", type=int, default=None, help="Stop after saving this many images (useful for tests)")
    return p.parse_args()


def prune_folder(folder_path: str, keep: int = 1):
    """Remove oldest files in folder_path until only `keep` newest files remain.

    Files are ordered by modification time. Non-file entries are ignored.
    """
    if keep < 0:
        return
    # list files only
    entries = []
    for name in os.listdir(folder_path):
        full = os.path.join(folder_path, name)
        if os.path.isfile(full):
            try:
                mtime = os.path.getmtime(full)
            except OSError:
                continue
            entries.append((mtime, full))
    # sort by mtime ascending (oldest first)
    entries.sort(key=lambda x: x[0])
    # remove oldest until len(entries) <= keep
    to_remove = len(entries) - keep
    for i in range(to_remove):
        try:
            os.remove(entries[i][1])
            print(f"Pruned old image: {entries[i][1]}")
        except Exception:
            # ignore errors removing individual files
            pass


def rotate_and_save(folder_path: str, temp_filename: str, keep: int = 5):






    """Deterministic rotate-and-save that avoids duplicate indexes.

    Strategy:
    - Collect files matching image_<index>_<suffix> and group by index.
    - For each index keep only the newest file (by mtime), remove others.
    - Remove any indexes > keep.
    - Shift files from high->low (idx -> idx+1), removing destination before rename.
    - Move temp file to image_1_<timestamp>.jpg.
    - Final pass: remove any image_ files with index outside 1..keep and ensure
      there is at most one file per index.
    """
    pattern = re.compile(r'^image_(\d+)_(.+)$')
    grouped = {}  # idx -> list of (mtime, name)

    # collect and group matching files
    for name in os.listdir(folder_path):
        full = os.path.join(folder_path, name)
        if not os.path.isfile(full):
            continue
        m = pattern.match(name)
        if not m:
            # ignore non-conforming names (they may be removed later)
            continue
        try:
            idx = int(m.group(1))
        except Exception:
            continue
        try:
            mtime = os.path.getmtime(full)
        except Exception:
            mtime = 0
        grouped.setdefault(idx, []).append((mtime, name))

    # deduplicate: keep newest per index, remove others
    existing = {}
    for idx, items in grouped.items():
        items.sort(key=lambda x: x[0], reverse=True)  # newest first
        keep_name = items[0][1]
        existing[idx] = keep_name
        for _, old_name in items[1:]:
            try:
                os.remove(os.path.join(folder_path, old_name))
                print(f"Removed duplicate index file: {old_name}")
            except Exception:
                pass

    # remove any indexes beyond keep
    for idx in sorted([i for i in existing.keys() if i > keep]):
        try:
            os.remove(os.path.join(folder_path, existing[idx]))
            print(f"Removed overflow image: {existing[idx]}")
            del existing[idx]
        except Exception:
            pass

    # shift files from highest to lowest to avoid clobbering
    for idx in range(keep - 1, 0, -1):
        src_name = existing.get(idx)
        if not src_name:
            continue
        src_path = os.path.join(folder_path, src_name)
        # build destination name preserving suffix
        parts = src_name.split('_', 2)
        suffix = parts[2] if len(parts) > 2 else ''
        dst_name = f"image_{idx+1}_{suffix}"
        dst_path = os.path.join(folder_path, dst_name)
        try:
            # remove any existing destination first to avoid duplicates
            if os.path.exists(dst_path):
                os.remove(dst_path)
            os.rename(src_path, dst_path)
            # update mapping
            existing[idx+1] = dst_name
            del existing[idx]
        except Exception:
            # if rename failed, try to continue
            pass

    # move temp file to image_1_<ts>.jpg
    if not os.path.exists(temp_filename):
        return
    ts = time.strftime("%Y%m%d-%H%M%S")
    final_name = f"image_1_{ts}.jpg"
    final_path = os.path.join(folder_path, final_name)
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_filename, final_path)
        print(f"Saved {final_path}")
    except Exception as e:
        print(f"Warning: failed to finalize saved image: {e}")

    # final cleanup: ensure at most one file per index and indices are 1..keep
    seen = {}
    for name in os.listdir(folder_path):
        full = os.path.join(folder_path, name)
        if not os.path.isfile(full):
            continue
        m = pattern.match(name)
        if not m:
            # non-matching image_ names (or others) -> ignore
            continue
        try:
            idx = int(m.group(1))
        except Exception:
            continue
        if idx < 1 or idx > keep:
            try:
                if os.path.abspath(full) == os.path.abspath(final_path):
                    continue
                os.remove(full)
                print(f"Removed out-of-range image: {name}")
            except Exception:
                pass
            continue
        # deduplicate any remaining duplicates by keeping newest
        if idx in seen:
            # decide which one to keep by mtime
            try:
                cur_mtime = os.path.getmtime(full)
                kept_mtime = os.path.getmtime(os.path.join(folder_path, seen[idx]))
                if cur_mtime > kept_mtime:
                    # replace kept with current, remove old
                    try:
                        os.remove(os.path.join(folder_path, seen[idx]))
                    except Exception:
                        pass
                    seen[idx] = name
                else:
                    try:
                        os.remove(full)
                    except Exception:
                        pass
            except Exception:
                # best-effort: remove duplicate
                try:
                    os.remove(full)
                except Exception:
                    pass
        else:
            seen[idx] = name


def main():
    args = parse_args()
    save_folder = args.save_folder
    interval = float(args.interval)

    test_images = None
    if args.test:
        # look for test images shipped with project
        base = os.path.join(os.path.dirname(__file__), "tests")
        test_images = []
        if os.path.isdir(base):
            for n in os.listdir(base):
                if n.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_images.append(os.path.join(base, n))
        test_images.sort()

    camera = CameraWorker(src=args.src, test_images=test_images)
    stop_event = threading.Event()

    try:
        camera.start()
        print("Camera worker started. Saving every", interval, "seconds to", save_folder)
        saver_loop(camera, save_folder, interval, stop_event, count=args.count)
    except KeyboardInterrupt:
        print("Stopping due to KeyboardInterrupt")
    finally:
        stop_event.set()
        camera.stop()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()