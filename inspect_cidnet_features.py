"""
inspect_cidnet_features.py  (Thành viên 2)
Trích và trực quan hóa đặc trưng trung gian của HVI-CIDNet:
  - Kênh HVI đầu vào: H_hat, V_hat, I_max
  - Đặc trưng sau mỗi khối encoder/decoder/LCA của nhánh I và nhánh HV

Chạy (đặt file này ở thư mục gốc của repo HVI-CIDNet):
  python inspect_cidnet_features.py --list
  python inspect_cidnet_features.py --input duong_dan_anh_toi.png --out feat_out
Mặc định tự tải trọng số Fediory/HVI-CIDNet-LOLv1-wperc từ Hugging Face
(cần internet lần đầu). Dùng file cục bộ: thêm --weights file.safetensors

LƯU Ý: tên module/file trọng số có thể khác. Chạy với --list để in toàn bộ
tên module rồi chỉnh PATTERNS cho khớp.
"""
import argparse
import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from net.CIDNet import CIDNet  # theo cấu trúc repo: net/CIDNet.py

# Chỉ hook các module "mức trên cùng" có tên chứa các chuỗi sau.
# Nhánh I: IE_block/ID_block/I_LCA ; nhánh HV: HVE_block/HVD_block/HV_LCA
PATTERNS = ("IE_block", "ID_block", "I_LCA", "HVE_block", "HVD_block", "HV_LCA")


def branch_of(name):
    return "HV" if name.startswith("HV") else "I"


def load_model(weights, hf_repo, device):
    model = CIDNet().to(device)
    if weights:  # file cục bộ: .pth hoặc .safetensors
        if weights.endswith(".safetensors"):
            import safetensors.torch as sf
            state = sf.load_file(weights)
        else:
            state = torch.load(weights, map_location=device)
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
    else:  # tải từ Hugging Face giống eval_hf.py
        from huggingface_hub import hf_hub_download
        import safetensors.torch as sf
        f = hf_hub_download(repo_id=hf_repo, filename="model.safetensors", repo_type="model")
        state = sf.load_file(f)
    model.load_state_dict(state, strict=False)
    model.eval()
    # Các cờ này giống eval_hf.py khi suy luận
    model.trans.alpha_s = 1.0
    model.trans.alpha = 1.0
    model.trans.gated = True
    model.trans.gated2 = True
    return model


def read_image(path, max_side=512):
    pil = Image.open(path).convert("RGB")
    if max_side and max(pil.size) > max_side:  # thu nhỏ để không hết RAM khi chạy CPU
        r = max_side / max(pil.size)
        pil = pil.resize((max(1, round(pil.width * r)), max(1, round(pil.height * r))), Image.LANCZOS)
        print("Đã thu nhỏ ảnh về", pil.size)
    img = np.asarray(pil, dtype=np.float32) / 255.0
    x = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
    h, w = x.shape[-2:]
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8  # 3 tầng downsample -> bội số của 8
    x = F.pad(x, (0, pw, 0, ph), mode="reflect")
    return x, (h, w)


def to_tensor(out):
    if isinstance(out, (tuple, list)):
        out = out[0]
    return out if torch.is_tensor(out) else None


def norm01(a):
    a = a - a.min()
    return a / (a.max() + 1e-8)


def save_map(fm, size, path, title):
    """fm: (C,H,W). Lưu bản đồ trung bình |.| theo kênh + lưới 8 kênh mạnh nhất."""
    fm = fm.float().cpu()
    mean_map = fm.abs().mean(0, keepdim=True)[None]
    mean_map = F.interpolate(mean_map, size=size, mode="bilinear", align_corners=False)[0, 0]
    top = fm.abs().mean((1, 2)).argsort(descending=True)[:8]
    fig, ax = plt.subplots(1, 9, figsize=(22, 2.8))
    ax[0].imshow(norm01(mean_map.numpy()), cmap="inferno")
    ax[0].set_title("mean|F|", fontsize=8)
    for i, c in enumerate(top):
        ax[i + 1].imshow(norm01(fm[c].numpy()), cmap="viridis")
        ax[i + 1].set_title(f"ch {int(c)}", fontsize=8)
    for a in ax:
        a.axis("off")
    fig.suptitle(title, fontsize=10)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return norm01(mean_map.numpy())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=None,
                    help="file .pth/.safetensors cục bộ (bỏ trống để tải từ Hugging Face)")
    ap.add_argument("--hf", default="Fediory/HVI-CIDNet-LOLv1-wperc",
                    help="repo Hugging Face chứa trọng số")
    ap.add_argument("--input", default=None)
    ap.add_argument("--max_side", type=int, default=512,
                    help="thu nhỏ cạnh dài nhất của ảnh (0 = giữ nguyên)")
    ap.add_argument("--out", default="feat_out")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--list", action="store_true", help="in tên module rồi thoát")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    model = load_model(args.weights, args.hf, args.device)
    if args.list:
        for n, m in model.named_modules():
            if n and "." not in n:
                print(n, "->", type(m).__name__)
        return

    feats = {}
    hooks = []
    for name, mod in model.named_children():
        if any(p in name for p in PATTERNS):
            hooks.append(mod.register_forward_hook(
                lambda m, i, o, n=name: feats.__setitem__(n, to_tensor(o))))
    print("Đã hook:", [n for n, _ in model.named_children() if any(p in n for p in PATTERNS)])

    if not args.input:
        raise SystemExit("Thiếu --input <đường dẫn ảnh>")
    x, (h, w) = read_image(args.input, args.max_side)
    x = x.to(args.device)
    with torch.no_grad():
        hvi = model.trans.HVIT(x)          # kênh 0,1 = H_hat,V_hat ; kênh 2 = I_max
        y = model(x)
    for h_ in hooks:
        h_.remove()

    # 1) Kênh HVI đầu vào
    names = ["H_hat", "V_hat", "I_max"]
    fig, ax = plt.subplots(1, 5, figsize=(20, 3.5))
    ax[0].imshow(x[0].permute(1, 2, 0).cpu().numpy()[:h, :w]); ax[0].set_title("Input sRGB")
    for i in range(3):
        ax[i + 1].imshow(hvi[0, i].cpu().numpy()[:h, :w], cmap="gray"); ax[i + 1].set_title(names[i])
    ax[4].imshow(y[0].clamp(0, 1).permute(1, 2, 0).cpu().numpy()[:h, :w]); ax[4].set_title("Output")
    for a in ax:
        a.axis("off")
    fig.savefig(os.path.join(args.out, "00_hvi_channels.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    # 2) Đặc trưng từng khối, và so sánh nhánh I vs HV
    summary = {"I": [], "HV": []}
    for name, fm in feats.items():
        if fm is None or fm.dim() != 4:
            continue
        m = save_map(fm[0], (x.shape[-2], x.shape[-1]),
                     os.path.join(args.out, f"feat_{name}.png"),
                     f"{name}  shape={tuple(fm.shape[1:])}")
        summary[branch_of(name)].append((name, m))

    for br, items in summary.items():
        if not items:
            continue
        fig, ax = plt.subplots(1, len(items), figsize=(3 * len(items), 3))
        ax = np.atleast_1d(ax)
        for a, (n, m) in zip(ax, items):
            a.imshow(m[:h, :w], cmap="inferno"); a.set_title(n, fontsize=8); a.axis("off")
        fig.suptitle(f"Nhánh {br}: mean|F| qua các khối")
        fig.savefig(os.path.join(args.out, f"branch_{br}_overview.png"), dpi=110, bbox_inches="tight")
        plt.close(fig)
    print("Xong. Kết quả ở:", args.out)


if __name__ == "__main__":
    main()