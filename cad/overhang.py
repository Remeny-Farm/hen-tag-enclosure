"""Report downward faces steeper than 45 deg that are not on the bed."""
import math, struct, sys
from collections import defaultdict
def tris(path):
    d = open(path, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    for i in range(n):
        o = 84 + 50 * i
        yield [struct.unpack("<3f", d[o+12+12*k:o+24+12*k]) for k in range(3)]
for path in sys.argv[1:]:
    ts = list(tris(path)); zmin = min(v[2] for t in ts for v in t)
    groups = defaultdict(lambda: [0.0, [1e9, -1e9, 1e9, -1e9]])
    for a, b, c in ts:
        u = [b[i]-a[i] for i in range(3)]; w = [c[i]-a[i] for i in range(3)]
        nx, ny, nz = u[1]*w[2]-u[2]*w[1], u[2]*w[0]-u[0]*w[2], u[0]*w[1]-u[1]*w[0]
        L = math.sqrt(nx*nx+ny*ny+nz*nz)
        if L == 0: continue
        z = min(a[2], b[2], c[2]) - zmin
        if nz / L < -0.707 and z > 0.05:
            g = groups[round(z, 1)]; g[0] += L / 2
            bb = g[1]
            for v in (a, b, c):
                bb[0] = min(bb[0], v[0]); bb[1] = max(bb[1], v[0]); bb[2] = min(bb[2], v[1]); bb[3] = max(bb[3], v[1])
    print(path.split("/")[-1])
    for z, (area, bb) in sorted(groups.items()):
        if area > 0.05:
            print(f"   z {z:5.2f}  {area:6.2f} mm2  x {bb[0]:6.1f}..{bb[1]:6.1f}  y {bb[2]:6.1f}..{bb[3]:6.1f}")
