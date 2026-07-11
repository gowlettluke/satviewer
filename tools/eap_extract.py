from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
from urllib.parse import urlparse
from curl_cffi import requests

URLS = {
"atkinson-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0010/1619632/atkinson-eap.pdf",
"baroon-pocket-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0003/1619634/baroon-eap.pdf",
"bill-gunn-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619637/bill-gunn-eap.pdf",
"bjelke-petersen-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0007/1619638/bjelke-petersen-eap.pdf",
"boondooma-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0009/1619640/boondooma-eap.pdf",
"borumba-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0010/1619641/borumba-eap.pdf",
"burdekin-falls-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619644/burdekin-falls-eap.pdf",
"callide-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0011/1619660/callide-eap.pdf",
"cania-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619671/cania-eap.pdf",
"cedar-pocket-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0005/1619672/cedar-pocket-eap.pdf",
"clarendon-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619675/clarendon-eap.pdf",
"coolmunda-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0011/1619678/coolmunda-eap.pdf",
"cooloolabin-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0012/1619679/cooloolabin-eap.pdf",
"e-j-beardmore-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619635/beardmore-eap.pdf",
"enoggera-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0003/1619706/enoggera-eap.pdf",
"eungella-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0005/1619708/eungella-eap.pdf",
"ewen-maddock-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619709/ewen-maddock-eap.pdf",
"fairbairn-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619711/fairbairn-eap.pdf",
"fred-haigh-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0010/1619713/fred-haigh-eap.pdf",
"glenlyon-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0011/1619714/glenlyon-eap.pdf",
"gold-creek-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619716/gold-creek-eap.pdf",
"hinze-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619720/hinze-eap.pdf",
"julius-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619725/julius-eap.pdf",
"kinchant-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619727/kinchant-eap.pdf",
"kroombit-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619729/kroombit-eap.pdf",
"lake-macdonald-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619736/lake-macdonald-eap.pdf",
"lake-manchester-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0007/1619737/lake-manchester-eap.pdf",
"leslie-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0003/1619742/leslie-eap.pdf",
"leslie-harrison-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619743/leslie-harrison-eap.pdf",
"little-nerang-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619745/little-nerang-eap.pdf",
"maroon-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0009/1619748/maroon-eap.pdf",
"moogerah-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619754/moogerah-eap.pdf",
"north-pine-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0010/1619758/north-pine-eap.pdf",
"paradise-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0003/1619760/paradise-eap.pdf",
"peter-faust-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619763/peter-faust-eap.pdf",
"poona-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0007/1619764/poona-eap.pdf",
"sideling-creek-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619770/sideling-creek-eap.pdf",
"somerset-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0005/1619771/somerset-eap.pdf",
"teemburra-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0006/1619781/teemburra-eap.pdf",
"tinaroo-falls-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0008/1619783/tinaroo-falls-eap.pdf",
"wappa-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0009/1619784/wappa-eap.pdf",
"wivenhoe-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0011/1619786/wivenhoe-eap.pdf",
"wuruma-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0004/1619788/wuruma-eap.pdf",
"wyaralong-dam":"https://www.dlgwv.qld.gov.au/__data/assets/pdf_file/0005/1619789/wyaralong-eap.pdf"}
KEYS=("quick reference","flood event","flood operation","alert","lean forward","stand up","stand down","full supply","flood of record","extreme flood","dam crest","storage level","lake level","reservoir level","spillway","bureau","warning","predicted","modelling","activation level")
def focus(text):
 lines=[re.sub(r"\s+"," ",x).strip() for x in text.splitlines()]; out=[]; seen=set()
 for i,line in enumerate(lines):
  if line and any(k in line.lower() for k in KEYS):
   for v in lines[max(0,i-5):min(len(lines),i+12)]:
    if v and v not in seen: seen.add(v); out.append(v)
 return "\n".join(out[:5000])
def reader_urls(url):
 p=urlparse(url); return [f"https://r.jina.ai/http://{p.netloc}{p.path}",f"https://r.jina.ai/https://{p.netloc}{p.path}"]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--batch',type=int,required=True); ap.add_argument('--batches',type=int,default=4); a=ap.parse_args()
 root=Path(__file__).resolve().parents[1]; out=root/f'eap_batch_{a.batch}'; out.mkdir(exist_ok=True)
 items=[(k,v) for i,(k,v) in enumerate(URLS.items()) if i%a.batches==a.batch]; manifest={}
 for dam,url in items:
  rec={'dam_id':dam,'source_url':url,'status':'failed','attempts':[]}
  for reader in reader_urls(url):
   for n in range(1,5):
    att={'reader_url':reader,'attempt':n}
    try:
     r=requests.get(reader,timeout=150,allow_redirects=True,impersonate='chrome',headers={'Accept':'text/plain,text/markdown,*/*','X-Return-Format':'markdown'})
     text=r.text; att.update({'status':r.status_code,'bytes':len(r.content),'prefix':text[:250]}); rec['attempts'].append(att)
     if r.status_code<400 and len(text)>5000 and 'just a moment' not in text.lower() and 'page not found' not in text[:500].lower():
      (out/f'{dam}.txt').write_text(text,encoding='utf-8'); (out/f'{dam}.focus.txt').write_text(focus(text),encoding='utf-8'); rec.update({'status':'ok','reader_url':reader,'bytes':len(r.content)}); break
    except Exception as e: att['error']=repr(e); rec['attempts'].append(att)
    time.sleep(2*n)
   if rec['status']=='ok': break
  manifest[dam]=rec; (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); print(dam,rec['status'],flush=True)
if __name__=='__main__': main()
