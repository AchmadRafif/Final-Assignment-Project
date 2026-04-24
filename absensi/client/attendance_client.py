import sys
import time
import base64
import threading
import argparse
import requests
import cv2

DEFAULT_SERVER  = "http://localhost:5000"
WEBCAM_INDEX    = 0
SNAPSHOT_WIDTH  = 640
SNAPSHOT_HEIGHT = 480
DEBOUNCE_SEC    = 3

def capture_frame(cam):
    ret, frame = cam.read()
    if not ret:
        print("[WARN] Webcam gagal mengambil gambar")
        return None
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode('utf-8')

def send_scan(server, rfid_uid, image_b64):
    try:
        resp = requests.post(
            f"{server}/api/scan",
            json={'rfid_uid': rfid_uid, 'image_b64': image_b64 or ''},
            timeout=10
        )
        data = resp.json()
        if data.get('success'):
            emp = data['employee']
            act = "CHECK-IN" if data['action'] == 'check_in' else "CHECK-OUT"
            print(f"\n  {act}  |  {emp['name']}  |  {emp['department']}  |  {data['time']}\n")
        else:
            print(f"\n  GAGAL: {data.get('message', 'Error tidak diketahui')}\n")
    except requests.exceptions.ConnectionError:
        print(f"\n  ERROR: Tidak bisa terhubung ke server {server}\n")
    except Exception as e:
        print(f"\n  ERROR: {e}\n")

def rfid_reader_loop(server, cam):
    print(f"  Sistem aktif  ->  Server: {server}")
    print("  Menunggu kartu RFID...\n")
    last_uid  = ''
    last_time = 0.0
    while True:
        try:
            uid = input().strip()
        except EOFError:
            break
        if not uid:
            continue
        now = time.time()
        if uid == last_uid and (now - last_time) < DEBOUNCE_SEC:
            continue
        last_uid  = uid
        last_time = now
        print(f"  RFID dibaca: {uid}")
        image_b64 = capture_frame(cam)
        t = threading.Thread(target=send_scan, args=(server, uid, image_b64), daemon=True)
        t.start()

def preview_loop(cam, stop_event):
    while not stop_event.is_set():
        ret, frame = cam.read()
        if ret:
            cv2.imshow("Webcam Preview - tekan Q untuk keluar", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
    cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server',  default=DEFAULT_SERVER)
    parser.add_argument('--cam',     type=int, default=WEBCAM_INDEX)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()

    cam = cv2.VideoCapture(args.cam)
    if not cam.isOpened():
        print(f"ERROR: Tidak bisa membuka webcam index {args.cam}")
        sys.exit(1)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  SNAPSHOT_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, SNAPSHOT_HEIGHT)

    stop_event = threading.Event()
    if args.preview:
        threading.Thread(target=preview_loop, args=(cam, stop_event), daemon=True).start()

    try:
        rfid_reader_loop(args.server, cam)
    except KeyboardInterrupt:
        print("\n  Program dihentikan.")
    finally:
        stop_event.set()
        cam.release()

if __name__ == '__main__':
    main()