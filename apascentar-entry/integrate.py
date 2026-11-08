import hashlib,json,struct,urllib.request,zipfile
from pathlib import Path
BASE_URL="https://github.com/caiofernandoba-glitch/projeto-patrono-apk/releases/download/apascentar-v1.0.32-hero-ampliado/Apascentar-hero-ampliado-estudos-validado-1.0.32-code33.apk"
EXPECTED="db7bff57863ae01c2e18bc6460e4f18ab8291e6f3437c4f0b54191b57fe30c9d"
out=Path("build-entry");out.mkdir(exist_ok=True)
raw=urllib.request.urlopen(BASE_URL,timeout=90).read()
assert hashlib.sha256(raw).hexdigest()==EXPECTED,"base integrity"
(out/"base.apk").write_bytes(raw)
with zipfile.ZipFile(out/"base.apk") as z:
    original={i.filename:z.read(i.filename) for i in z.infolist() if not i.is_dir()}
assets=out/"assets";assets.mkdir(exist_ok=True)
for k,v in original.items():
    if k.startswith("assets/"):
        p=out/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
for name in ["entry.js","entry.css"]:
    (assets/name).write_bytes((Path("apascentar-entry")/name).read_bytes())
s=(assets/"index.html").read_text()
assert "entry.js" not in s
injection="<link rel=\"stylesheet\" href=\"entry.css\"><script>document.documentElement.classList.add(\"ap-entry-pending\");</script><script src=\"entry.js\" defer></script>"
assert "</head>" in s
(assets/"index.html").write_text(s.replace("</head>",injection+"</head>",1))
manifest=bytearray(original["AndroidManifest.xml"])
# versionCode is an Android resource attribute, not an arbitrary integer scan.
code_offsets=[]
# Resource map maps string-pool attribute indexes to resource IDs.
size=len(manifest);pos=8;resource_map=[]
while pos<size:
    typ,header,total=struct.unpack_from("<HHI",manifest,pos)
    assert total>=header and total>0
    if typ==0x0180:resource_map=list(struct.unpack_from("<"+"I"*((total-header)//4),manifest,pos+header))
    if typ==0x0102:
        start,attrsize,count=struct.unpack_from("<HHH",manifest,pos+24)
        for i in range(count):
            a=pos+16+start+i*attrsize
            name=struct.unpack_from("<I",manifest,a+4)[0]
            if name<len(resource_map) and resource_map[name]==0x0101021b:
                assert manifest[a+15]==0x10
                assert struct.unpack_from("<I",manifest,a+16)[0]==33
                struct.pack_into("<I",manifest,a+16,34);code_offsets.append(a+16)
    pos+=total
assert len(code_offsets)==1,"exactly one versionCode"
changed={"AndroidManifest.xml":bytes(manifest),"assets/index.html":(assets/"index.html").read_bytes(),"assets/entry.js":(assets/"entry.js").read_bytes(),"assets/entry.css":(assets/"entry.css").read_bytes()}
def signature(n):
    return n.startswith("META-INF/") and (n.endswith((".RSA",".DSA",".EC",".SF")) or n=="META-INF/MANIFEST.MF")
with zipfile.ZipFile(out/"Apascentar-entry-code34-UNSIGNED.apk","w",zipfile.ZIP_DEFLATED) as z:
    for n,b in original.items():
        if not signature(n):z.writestr(n,changed.get(n,b))
    for n,b in changed.items():
        if n not in original:z.writestr(n,b)
with zipfile.ZipFile(out/"Apascentar-entry-code34-UNSIGNED.apk") as z:
    assert z.testzip() is None
    differences=[n for n,b in original.items() if not signature(n) and z.read(n)!=b]
    assert sorted(differences)==["AndroidManifest.xml","assets/index.html"]
report={"baseIntegrity":True,"onlyModifiedExisting":differences,"added":["assets/entry.js","assets/entry.css"],"versionCode":34,"signed":False,"installableUpdate":False,"note":"Same original signing key required; do not distribute unsigned APK."}
(out/"integration-report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report))
