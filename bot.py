"""Bot Clash of Critters: doc anh moi trong thu muc Google Drive, nhan dien so man,
dang len Discord kem danh sach man da vuot, roi doi ten anh tren Drive de danh dau.

  ✅ 29-80 - ten_goc.png   -> da dang
  ❌ ... - ten_goc.png      -> loi (khong doc duoc / man cu / trung man), bot bo qua

Bien moi truong: DISCORD_WEBHOOK, GDRIVE_KEY (noi dung file JSON), DRIVE_FOLDER_ID
"""
import io, os, re, sys, time, json, uuid, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageFile
from scipy import ndimage

ImageFile.LOAD_TRUNCATED_IMAGES = True
sys.stdout.reconfigure(encoding="utf-8")
STAGES_PER_CHAPTER = 80
TEMPLATES = Path(__file__).parent / "mau_chu_so.npz"
GLYPH_SIZE = (20, 28)
DONE = re.compile(r"^✅ (\d+)-(\d+) - ")


# ---------- Doc so man tu anh ----------
def find_label(im):
    """Tim chuoi ky tu dang 'so-so' o phan tren anh. Tra ve cac ung vien (list glyph)."""
    im = im.convert("RGB")
    W, H = im.size
    top = im.crop((0, 0, W, int(H * 0.2)))
    s = 1440 / W
    top = top.resize((1440, int(top.size[1] * s)), Image.BICUBIC)
    a = np.array(top).astype(int)
    mask = (a.min(2) > 150) & (a.max(2) - a.min(2) < 60)
    lab, n = ndimage.label(mask)
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        comps.append(dict(x0=x0, x1=x1, y0=y0, y1=y1, h=y1 - y0, w=x1 - x0, g=(lab[sl] == i)))
    cands = []
    for d in comps:  # dau gach ngang: rong hon cao, nho
        if not (d["w"] > 1.8 * d["h"] and 8 < d["w"] < 120):
            continue
        cy = (d["y0"] + d["y1"]) / 2
        digits = [c for c in comps if c is not d and 2.5 * d["h"] < c["h"] < 20 * d["h"]
                  and c["y0"] < cy < c["y1"] and abs((c["y0"] + c["y1"]) / 2 - cy) < 0.2 * c["h"]]
        if not digits:
            continue
        h = np.median([c["h"] for c in digits])
        digits = [c for c in digits if abs(c["h"] - h) < 0.2 * h]

        def chain(direction):
            out, edge = [], d["x0"] if direction < 0 else d["x1"]
            while True:
                nxt = [c for c in digits if c not in out and
                       (0 <= edge - c["x1"] < 0.5 * h if direction < 0 else 0 <= c["x0"] - edge < 0.5 * h)]
                if not nxt:
                    return out
                c = min(nxt, key=lambda c: abs(c["x0"] - edge))
                out.append(c)
                edge = c["x0"] if direction < 0 else c["x1"]
        L, R = chain(-1)[::-1], chain(1)
        if 1 <= len(L) <= 3 and 1 <= len(R) <= 3:
            cands.append([c["g"] for c in L] + [None] + [c["g"] for c in R])
    return cands


def norm(g):
    return np.array(Image.fromarray(g.astype(np.uint8) * 255).resize(GLYPH_SIZE)) / 255.0


def load_templates():
    d = np.load(TEMPLATES)
    return {c: d[c] for c in d.files}


def read_stage(im, tpl):
    """Tra ve (tang, man) hoac None neu khong doc duoc."""
    best = None
    for cand in find_label(im):
        text, worst = "", 0.0
        for g in cand:
            if g is None:
                text += "-"
                continue
            v = norm(g)
            dists = {c: np.abs(v - t).mean() for c, t in tpl.items()}
            c = min(dists, key=dists.get)
            worst = max(worst, dists[c])
            text += c
        if best is None or worst < best[1]:
            best = (text, worst)
    if best is None or best[1] > 0.2:
        return None
    c, n = best[0].split("-")
    return int(c), int(n)


# ---------- Caption ----------
def stages_between(prev, cur):
    c, n = prev
    out = []
    while (c, n) != tuple(cur):
        out.append(f"{c}-{n}")
        n += 1
        if n > STAGES_PER_CHAPTER:
            c, n = c + 1, 1
    return out


def caption(prev, cur):
    if prev is None:
        return f"{cur[0]}-{cur[1]}"
    return ", ".join(stages_between(prev, cur))


# ---------- Discord ----------
def post(webhook, filename, data, content):
    boundary = uuid.uuid4().hex
    mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\n"
        f"Content-Type: application/json\r\n\r\n{json.dumps({'content': content})}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[0]\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(webhook, data=body, method="POST", headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "clash-map-bot"})
    urllib.request.urlopen(req).read()


# ---------- Google Drive ----------
class Drive:
    def __init__(self, key_json, folder_id):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_info(
            json.loads(key_json), scopes=["https://www.googleapis.com/auth/drive"])
        self.api = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.folder = folder_id

    def list_images(self):
        files, token = [], None
        while True:
            r = self.api.files().list(
                q=f"'{self.folder}' in parents and mimeType contains 'image/' and trashed=false",
                fields="nextPageToken, files(id, name)", pageSize=1000, pageToken=token,
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            files += r["files"]
            token = r.get("nextPageToken")
            if not token:
                return files

    def download(self, file_id):
        return self.api.files().get_media(fileId=file_id, supportsAllDrives=True).execute()

    def rename(self, file_id, name):
        self.api.files().update(fileId=file_id, body={"name": name}, supportsAllDrives=True).execute()


# ---------- Chay ----------
def run(drive, webhook):
    tpl = load_templates()
    files = drive.list_images()
    done = [tuple(map(int, m.groups())) for f in files if (m := DONE.match(f["name"]))]
    prev = max(done) if done else None
    new = [f for f in files if not f["name"].startswith(("✅", "❌"))]
    print(f"Man cuoi da dang: {prev}. Anh moi: {len(new)}")

    readable = []
    for f in new:
        data = drive.download(f["id"])
        stage = read_stage(Image.open(io.BytesIO(data)), tpl)
        if stage is None:
            print(f"  ❌ {f['name']}: khong doc duoc so man")
            drive.rename(f["id"], f"❌ không đọc được - {f['name']}")
        else:
            readable.append((stage, f, data))

    for stage, f, data in sorted(readable, key=lambda x: x[0]):
        if prev is not None and stage <= tuple(prev):
            reason = "trùng màn" if stage == tuple(prev) else "màn cũ hơn"
            print(f"  ❌ {f['name']}: {reason} ({stage[0]}-{stage[1]})")
            drive.rename(f["id"], f"❌ {reason} {stage[0]}-{stage[1]} - {f['name']}")
            continue
        text = caption(prev, stage)
        post(webhook, f["name"], data, text)
        drive.rename(f["id"], f"✅ {stage[0]}-{stage[1]} - {f['name']}")
        print(f"  ✅ {f['name']} -> {text}")
        prev = stage
        time.sleep(1.5)  # tranh bi Discord gioi han toc do


if __name__ == "__main__":
    missing = [k for k in ("DISCORD_WEBHOOK", "GDRIVE_KEY", "DRIVE_FOLDER_ID") if not os.environ.get(k)]
    if missing:
        sys.exit(f"Thieu secret: {', '.join(missing)}")
    webhook = os.environ["DISCORD_WEBHOOK"].strip()
    # Dang vao 1 bai dang (thread) trong kenh dien dan: nhan ID hoac link bai dang
    thread = os.environ.get("DISCORD_THREAD", "").strip().rstrip("/")
    if thread:
        ids = re.findall(r"\d+", thread)
        # link .../channels/<server>/<bai dang>[/<tin nhan>] -> lay ID bai dang
        thread_id = ids[1] if "channels/" in thread and len(ids) >= 2 else ids[-1]
        webhook += ("&" if "?" in webhook else "?") + f"thread_id={thread_id}"
    run(Drive(os.environ["GDRIVE_KEY"], os.environ["DRIVE_FOLDER_ID"].strip()), webhook)
