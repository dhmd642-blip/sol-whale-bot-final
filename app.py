import os, time, threading, requests
from flask import Flask
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
MIN_SOL = float(os.getenv("MIN_SOL", "1000"))
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
last_sigs = set()

def send_telegram(text):
    if not BOT_TOKEN or not CHANNEL_ID:
        print(f"[MOCK] {text}"); return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode":"HTML"}, timeout=10)
    except Exception as e: print(e)

def whale_loop():
    print(f"Whale bot > {MIN_SOL} SOL")
    while True:
        try:
            r = requests.post(SOLANA_RPC, json={"jsonrpc":"2.0","id":1,"method":"getSlot"}, timeout=10)
            slot = r.json().get("result")
            r = requests.post(SOLANA_RPC, json={"jsonrpc":"2.0","id":1,"method":"getBlock","params":[slot, {"maxSupportedTransactionVersion":0, "transactionDetails":"full", "rewards":False}]}, timeout=15)
            block = r.json().get("result")
            if block and "transactions" in block:
                for tx in block["transactions"][:30]:
                    meta = tx.get("meta",{})
                    if meta.get("err"): continue
                    pre, post = meta.get("preBalances",[]), meta.get("postBalances",[])
                    for i in range(len(pre)):
                        diff = abs(post[i]-pre[i])/1e9
                        if diff >= MIN_SOL:
                            sig = tx["transaction"]["signatures"][0]
                            if sig in last_sigs: continue
                            last_sigs.add(sig)
                            msg = f"🐋 <b>WHALE ALERT!</b>\n\n💰 {diff:,.1f} SOL\n🔗 <a href='https://solscan.io/tx/{sig}'>Solscan</a>\n#SOL"
                            send_telegram(msg)
            time.sleep(10)
        except Exception as e:
            print(e); time.sleep(15)

@app.route("/")
def home():
    return f"<h1>🐋 Bot Running > {MIN_SOL} SOL</h1><p>Token: {'OK' if BOT_TOKEN else 'NOT SET'}</p>"

threading.Thread(target=whale_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
