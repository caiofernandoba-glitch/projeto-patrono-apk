from pathlib import Path
import json,os,traceback
src=Path("apascentar-entry/integrate.py").read_text()
insert="""
images=[n for n in original if n.startswith("assets/") and n.lower().endswith((".png",".jpg",".jpeg",".webp"))]
heroes=[n for n in images if "jesus" in n.lower() and "ovelh" in n.lower()]
if not heroes:heroes=[n for n in images if "hero" in n.lower()]
if not heroes:raise RuntimeError("Approved hero unavailable; image paths: "+json.dumps(images))
hero=sorted(heroes,key=lambda n:("approved" not in n,"principal" not in n,n))[0][7:]
p=Path("apascentar-entry/entry.js");p.write_text(p.read_text().replace("approved-home/jesus-ovelha-principal.jpg",hero))
"""
src=src.replace("assets=out/",insert+"\nassets=out/",1)
try:
    exec(compile(src,"integrate.py","exec"))
    summary="Integration passed. Approved image: "+hero+"\n\n"+Path("build-entry/integration-report.json").read_text()
except Exception:
    summary=traceback.format_exc()
    raise
finally:
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:f.write("\n```\n"+summary+"\n```\n")
