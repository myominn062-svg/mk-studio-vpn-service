# MK Studio VPN Service — Free Public V2Ray Config List

[🇲🇲 မြန်မာ](#-မြန်မာ) | [🇺🇸 English](#-english)

Free, auto-updated public proxy configs for **SS / SSR / Trojan / VLESS / VMess / Hysteria2 / TUIC**.  
Copy → paste → connect. No signup. No payment.

**Updated every 15 minutes** via GitHub Actions.

> Aggregates publicly shared free configs from multiple open sources.  
> Each update **TCP health-checks** endpoints and drops dead hosts (port closed).  
> Free public nodes are still shared & unstable — do **not** use for banking or sensitive logins.  
> TCP-alive ≠ full proxy guarantee (some open ports may still fail in-app).

---

## 🇺🇸 English

### Recommended apps
| Platform | Apps |
|----------|------|
| Windows / Linux | [v2rayN](https://github.com/2dust/v2rayN), [Nekoray](https://github.com/MatsuriDayo/nekoray) |
| Android | [v2rayNG](https://github.com/2dust/v2rayNG), [Hiddify](https://github.com/hiddify/Hiddify-Next), [NekoBox](https://github.com/MatsuriDayo/NekoBoxForAndroid) |
| iOS / macOS | [Streisand](https://apps.apple.com/app/streisand/id6450534064), [Shadowrocket](https://apps.apple.com/app/shadowrocket/id932747118), [V2BOX](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |

### How to connect
1. Copy a **subscription** or **raw** link below  
2. Open your app → **+** / **Import from Clipboard** / **Add subscription**  
3. Update & connect  

Also works with **[MK Studio VPN](https://github.com/myominn062-svg/mk-studio-vpn)**.

### Subscription links (Base64 — best for most clients)

| List | Link |
|------|------|
| All protocols | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/subscription.txt` |
| VLESS | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/subscription-vless.txt` |
| VMess | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/subscription-vmess.txt` |
| Trojan | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/subscription-trojan.txt` |
| Shadowsocks | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/subscription-ss.txt` |

### Raw config lists (one URI per line)

| File | Link |
|------|------|
| All types | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/MK-Studio-VPN-All-Type.txt` |
| All configs | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/all_configs.txt` |
| VMess | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/vmess_configs.txt` |
| VLESS | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/vless_configs.txt` |
| Trojan | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/trojan_configs.txt` |
| SS | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/ss_configs.txt` |
| SSR | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/ssr_configs.txt` |
| Hysteria2 | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/hysteria2_configs.txt` |
| TUIC | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/tuic_configs.txt` |

### By country (ISO code)

Each country has:
- Raw list: `countries/XX.txt`
- Subscription (Base64): `countries/XX.sub.txt`

Full index (auto-updated): [`countries/README.md`](./countries/README.md) · [`countries/index.json`](./countries/index.json)

| Country | Subscription |
|---------|--------------|
| Singapore (SG) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/SG.sub.txt` |
| Japan (JP) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/JP.sub.txt` |
| United States (US) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/US.sub.txt` |
| Germany (DE) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/DE.sub.txt` |
| Netherlands (NL) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/NL.sub.txt` |
| Hong Kong (HK) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/HK.sub.txt` |
| South Korea (KR) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/KR.sub.txt` |
| United Kingdom (GB) | `https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/GB.sub.txt` |

Pattern for any country code:
```
https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/<CODE>.sub.txt
```
Example: `TH` → `.../countries/TH.sub.txt`

### QR — All protocols subscription

![QR](https://quickchart.io/qr?text=https%3A%2F%2Fraw.githubusercontent.com%2Fmyominn062-svg%2Fmk-studio-vpn-service%2Fmain%2Fsubscription.txt&size=220)

### Update frequency
- Auto-refresh every **15 minutes**
- Dead hosts removed via **TCP health-check**
- Duplicate configs removed
- Split by protocol **and** by country
- Status snapshot: [`meta.json`](./meta.json)

### Local update (optional)
```bash
python3 scripts/update_configs.py
```

Edit public sources in [`sources.json`](./sources.json).

---

## 🇲🇲 မြန်မာ

### ဘာလဲ?
**MK Studio VPN Service** က free public V2Ray config တွေကို စုစည်းပြီး GitHub မှာ မျှဝေပေးတဲ့ service ပါ။  
**၁၅ မိနစ်တိုင်း** အလိုအလျောက် အပ်ဒိတ်လုပ်ပါတယ်။

### ဘယ်လိုသုံးမလဲ?
1. အပေါ်က subscription link တစ်ခုကို ကော်ပီလုပ်ပါ  
2. App ထဲမှာ **Import / Add subscription** ထည့်ပါ  
3. Update လုပ်ပြီး connect နှိပ်ပါ  

### နိုင်ငံအလိုက်
SG / JP / US စသည်ဖြင့် နိုင်ငံကုဒ်နဲ့ ခွဲထားပါတယ်။  
ဥပမာ Singapore:
`https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/SG.sub.txt`  

စာရင်းအပြည့်: [`countries/README.md`](./countries/README.md) 

### သတိပြုရန်
Free public node တွေက မတည်ငြိမ်နိုင်ပါတယ်။ ဘဏ် / အရေးကြီးအကောင့် အတွက် မသုံးပါနဲ့။

---

## Maintained by
**MK Studio VPN** · GitHub: [myominn062-svg](https://github.com/myominn062-svg)

Client app: [mk-studio-vpn](https://github.com/myominn062-svg/mk-studio-vpn)
