from PIL import Image, ImageDraw
import os

sizes = [256, 128, 64, 48, 32, 16]
imgs = []

for sz in sizes:
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 다크 라운드 배경
    pad = sz // 16
    r = sz // 5
    d.rounded_rectangle([pad, pad, sz - pad, sz - pad], radius=r, fill=(30, 30, 30, 255))

    # 보라색 메모지
    m = sz // 8
    nr = sz // 8
    d.rounded_rectangle([m, m + sz//12, sz - m, sz - m], radius=nr, fill=(167, 139, 250, 255))

    # 접힌 상단 (진한 보라)
    fold_h = sz // 10
    d.rounded_rectangle([m, m, sz - m, m + fold_h + nr], radius=nr, fill=(142, 110, 230, 255))
    d.rectangle([m, m + fold_h, sz - m, m + fold_h + nr], fill=(142, 110, 230, 255))

    # 텍스트 라인 (흰색 반투명)
    lw = max(1, sz // 50)
    y_start = m + fold_h + sz // 7
    line_gap = sz // 7
    line_left = m + sz // 7
    line_right = sz - m - sz // 7

    for i in range(3):
        y = y_start + i * line_gap
        if y + lw < sz - m - sz // 10:
            right = line_right - (i * sz // 8)
            d.line([(line_left, y), (right, y)], fill=(255, 255, 255, 140), width=lw)

    # 빨간 핀
    pin_r = max(2, sz // 14)
    pin_cx = m + sz // 10
    pin_cy = m + sz // 20
    d.ellipse([pin_cx - pin_r, pin_cy - pin_r, pin_cx + pin_r, pin_cy + pin_r],
              fill=(230, 70, 70, 230))
    hl = max(1, pin_r // 3)
    d.ellipse([pin_cx - hl, pin_cy - pin_r + hl, pin_cx + hl, pin_cy - pin_r + hl*3],
              fill=(255, 150, 150, 200))

    imgs.append(img)

ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memo.ico")
imgs[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes],
             append_images=imgs[1:])
print(f"Icon saved: {ico_path}")
