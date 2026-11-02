#!/usr/bin/env python3
"""扫描 ops_videos，生成 videos/ 与 manifest.json。重复运行即可加入新视频。"""
import json, re, shutil, subprocess, os
from pathlib import Path as _P
PENDING={l.strip().lstrip('q').lstrip('0') for l in (_P(__file__).parent/'pending_review.txt').read_text().split() } if (_P(__file__).parent/'pending_review.txt').exists() else set()
from pathlib import Path
SRC = Path('/workspace/excel/ops_videos'); SITE = Path(__file__).resolve().parent
VID = SITE/'videos'; VID.mkdir(exist_ok=True)
LIMIT = 50*1024*1024
SEC_OVERRIDE = {q:'4.3' for q in ('15','16','17','18','19')}  # md lists these under 4.2
SEC_NAME = {'4.2':'4.2 工作表与单元格操作','4.3':'4.3 格式设置','4.4':'4.4 公式与函数','4.5':'4.5 数据管理','4.6':'4.6 图表'}
def key(qid):
    m = re.match(r'(\d+)([a-z]?)', qid); return (int(m[1]), m[2])
def ok(p):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],capture_output=True,text=True,timeout=30)
        return float(r.stdout.strip() or 0)
    except Exception: return 0
items = []
for line in (SRC/'选项卡组别汇总.md').read_text(encoding='utf-8').splitlines():
    m = re.match(r'\|\s*(\d+[a-z]?)\s*\|\s*(4\.\d)\s*\|\s*([^|]+)\|', line)
    if not m: continue
    qid, sec, title = m[1], m[2], m[3].strip().replace('**','')
    sec = SEC_OVERRIDE.get(qid, sec)
    title = re.sub(r'^例\s*\d*[:：]\s*', '例：', title)
    fid = f'q{int(re.match(r"\d+",qid)[0]):02d}{re.sub(r"^\d+","",qid)}'
    src, dst = SRC/f'{fid}.mp4', VID/f'{fid}.mp4'
    dur = ok(src) if src.exists() else 0
    if dur > 0:
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            if src.stat().st_size > LIMIT:
                subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-c:v','libx264','-crf','28','-preset','medium','-c:a','aac','-b:a','96k','-movflags','+faststart',str(dst)],check=True)
            else: shutil.copy2(src, dst)
    elif dst.exists(): dst.unlink()
    items.append({'id':qid,'file':f'videos/{fid}.mp4' if dur>0 else None,'section':sec,'title':title,'duration':round(dur),'review':str(qid) in PENDING})
items.sort(key=lambda x:(x['section'], key(x['id'])))
secs=[]
for it in items:
    if not secs or secs[-1]['id']!=it['section']: secs.append({'id':it['section'],'name':SEC_NAME.get(it['section'],it['section']),'items':[]})
    secs[-1]['items'].append(it)
(SITE/'manifest.json').write_text(json.dumps({'sections':secs},ensure_ascii=False,indent=1),encoding='utf-8')
print('live:', [i['id'] for i in items if i['file']])
