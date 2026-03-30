from PIL import Image, ImageDraw, ImageFont
import os

sizes = [256, 128, 64, 48, 32, 16]
imgs = []

for sz in sizes:
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = max(1, sz // 32)  # margin scale
    
    # 포스트잇 본체 (둥근 모서리 노란색)
    pad = sz // 16
    r = sz // 8
    body = [pad, pad + sz//10, sz - pad, sz - pad]
    d.rounded_rectangle(body, radius=r, fill=(255, 225, 80, 255))
    
    # 상단 접힌 부분 (살짝 진한 노란색)
    fold_h = sz // 10
    fold_box = [pad, pad, sz - pad, pad + fold_h + r]
    d.rounded_rectangle(fold_box, radius=r, fill=(255, 210, 50, 255))
    # 하단 직선 마감
    d.rectangle([pad, pad + fold_h, sz - pad, pad + fold_h + r], fill=(255, 210, 50, 255))
    # 접힌 그림자 선
    d.line([(pad + sz//12, pad + fold_h), (sz - pad - sz//12, pad + fold_h)], 
           fill=(220, 180, 40, 180), width=max(1, sz//64))
    
    # 텍스트 라인들 (연필로 쓴 느낌)
    line_color = (120, 100, 60, 160)
    lw = max(1, sz // 64)
    y_start = pad + fold_h + sz // 8
    line_gap = sz // 7
    line_left = pad + sz // 6
    line_right = sz - pad - sz // 6
    
    for i in range(3):
        y = y_start + i * line_gap
        if y + lw < body[3] - sz//10:
            # 각 줄 길이 다르게
            right = line_right - (i * sz // 10)
            d.line([(line_left, y), (right, y)], fill=line_color, width=lw)
    
    # 왼쪽 상단에 작은 핀/클립 (빨간 원)
    pin_r = max(2, sz // 12)
    pin_cx = pad + sz // 8
    pin_cy = pad + sz // 16
    d.ellipse([pin_cx - pin_r, pin_cy - pin_r, pin_cx + pin_r, pin_cy + pin_r],
              fill=(230, 70, 70, 230))
    # 핀 하이라이트
    hl = max(1, pin_r // 3)
    d.ellipse([pin_cx - hl, pin_cy - pin_r + hl, pin_cx + hl, pin_cy - pin_r + hl*3],
              fill=(255, 150, 150, 200))
    
    imgs.append(img)

# ICO 저장
ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memo.ico")
imgs[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes], 
             append_images=imgs[1:])
print(f"Icon saved: {ico_path}")
