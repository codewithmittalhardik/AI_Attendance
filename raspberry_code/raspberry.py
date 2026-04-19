import cv2
import requests
import time
import argparse
import subprocess
import numpy as np
from urllib.parse import urljoin

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Replace SERVER_IP with the exact local network IP of the machine running Django
SERVER_IP = "x4tc4p30-8000.inc1.devtunnels.ms/" 
SCAN_COOLDOWN = 5  
HEARTBEAT_INTERVAL = 5 
CAMERA_ROTATE_DEG = -90


def build_endpoint_urls(server_ip):
    base = server_ip.strip()
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"
    if not base.endswith("/"):
        base += "/"
    return (
        urljoin(base, "hardware_scan/"),
        urljoin(base, "api/heartbeat/"),
    )


def open_camera(camera_index=0):
    candidates = [
        (camera_index, cv2.CAP_V4L2),
        (camera_index, None),
    ]
    if camera_index != -1:
        candidates.append((-1, None))

    for index, backend in candidates:
        cap = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Warm-up reads improve stability on some Pi camera stacks.
            stable = False
            for _ in range(5):
                ok, _ = cap.read()
                if ok:
                    stable = True
                    break
                time.sleep(0.1)

            if stable:
                print(f"✅ Camera opened on index {index}{' with V4L2' if backend == cv2.CAP_V4L2 else ''}.")
                return cap

            cap.release()

    return None


def capture_frame_libcamera(width=640, height=480, timeout=5):
    cmd = [
        "libcamera-still",
        "-n",
        "--immediate",
        "--width",
        str(width),
        "--height",
        str(height),
        "--encoding",
        "jpg",
        "-o",
        "-",
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if proc.returncode != 0 or not proc.stdout:
        return None

    img = cv2.imdecode(np.frombuffer(proc.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
    return img


def rotate_frame(frame, rotate_deg):
    rotate_deg = int(rotate_deg) % 360
    if rotate_deg == 0:
        return frame
    if rotate_deg == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if rotate_deg == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotate_deg == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame

def start_pi_scanner(server_ip, headless=True, camera_index=0, camera_mode="auto", camera_rotate_deg=0):
    print("🚀 Booting Raspberry Pi Auto-Scanner Simulator...")

    django_url, heartbeat_url = build_endpoint_urls(server_ip)

    use_libcamera = False
    cap = None

    if camera_mode in ("auto", "opencv"):
        cap = open_camera(camera_index=camera_index)

    if cap is None and camera_mode in ("auto", "libcamera"):
        print("⚠️ OpenCV camera open failed. Falling back to libcamera capture mode...")
        test_frame = capture_frame_libcamera(timeout=8)
        if test_frame is not None:
            use_libcamera = True
            print("✅ libcamera capture mode active.")

    if cap is None and not use_libcamera:
        print("❌ Error: Could not access the Pi camera. Make sure it is connected and enabled.")
        return

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    print(f"✅ Camera active! Looking for faces...")
    print(f"📡 Sending data to: {django_url}")
    print("👉 Press Ctrl+C in terminal to quit.")

    last_scan_time = 0
    last_heartbeat_time = 0
    failed_reads = 0

    try:
        while True:
            if use_libcamera:
                frame = capture_frame_libcamera(timeout=8)
                ret = frame is not None
            else:
                ret, frame = cap.read()

            if not ret or frame is None:
                failed_reads += 1
                print(f"Failed to grab frame ({failed_reads}). Retrying...")

                if failed_reads >= 5 and not use_libcamera:
                    print("🔄 Reinitializing camera after repeated frame failures...")
                    cap.release()
                    cap = open_camera(camera_index=camera_index)
                    if cap is None:
                        if camera_mode == "opencv":
                            print("❌ Error: Camera recovery failed in OpenCV-only mode.")
                            break

                        print("⚠️ OpenCV recovery failed. Switching to libcamera capture mode...")
                        test_frame = capture_frame_libcamera(timeout=8)
                        if test_frame is None:
                            print("❌ Error: libcamera fallback failed.")
                            break
                        use_libcamera = True
                        frame = test_frame
                    failed_reads = 0

                time.sleep(1)
                continue
            failed_reads = 0

            frame = rotate_frame(frame, camera_rotate_deg)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Optimize face detection for Pi performance (scaleFactor 1.3 is faster)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.3, 
                minNeighbors=5, 
                minSize=(60, 60)
            )

            current_time = time.time()

            # ==========================================
            # 1. HEARTBEAT LOGIC (Runs every 5 seconds)
            # ==========================================
            if (current_time - last_heartbeat_time) > HEARTBEAT_INTERVAL:
                try:
                    requests.get(heartbeat_url, timeout=2)
                except requests.exceptions.RequestException:
                    pass # Silently fail if server is down
                last_heartbeat_time = current_time

            # ==========================================
            # 2. AUTO-SCAN LOGIC
            # ==========================================
            if len(faces) > 0 and (current_time - last_scan_time) > SCAN_COOLDOWN:
                print(f"\n📸 Face detected! Auto-scanning...")
                last_scan_time = current_time
                
                # Compress image for faster network transmission
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                image_bytes = buffer.tobytes()
                
                try:
                    headers = {'Content-Type': 'image/jpeg'}
                    response = requests.post(django_url, data=image_bytes, headers=headers, timeout=5)
                    print(f"✅ Server Reply: {response.json()}") 
                except requests.exceptions.ConnectionError:
                    print(f"❌ Connection Error: Is Django running and accessible at {server_ip}?")
                except Exception as e:
                    print(f"❌ Error during request: {e}")

            # Optional visualization if running with a Desktop/GUI on the Pi
            if not headless:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.imshow("Raspberry Pi Auto Scanner", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Shutting down scanner...")
                    break
            else:
                # Add a tiny sleep to prevent 100% CPU usage
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        if cap is not None:
            cap.release()
        if not headless:
            cv2.destroyAllWindows()
        print("Scanner shut down gracefully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raspberry Pi Auto-Scanner")
    parser.add_argument('--ip', type=str, default=SERVER_IP, help="IP address of the Django server")
    parser.add_argument('--show', action='store_true', help="Show video feed window (requires GUI/Desktop)")
    parser.add_argument('--camera-index', type=int, default=0, help="Camera index (try 0, 1, or -1)")
    parser.add_argument('--camera-mode', choices=['auto', 'opencv', 'libcamera'], default='auto', help="Camera backend mode")
    parser.add_argument('--camera-rotate', type=int, default=CAMERA_ROTATE_DEG, choices=[-90, 0, 90, 180], help="Rotate camera frame in degrees")
    args = parser.parse_args()
    
    start_pi_scanner(
        server_ip=args.ip,
        headless=not args.show,
        camera_index=args.camera_index,
        camera_mode=args.camera_mode,
        camera_rotate_deg=args.camera_rotate,
    )
