/* machine-made Warp — sketch 0.2 glyph engine (pen model).
   Font units, y up, em 1000. Every glyph is a set of centre-lines ("strokes").
   Each stroke is swept by a nib: a rounded rectangle `a` long and `b` thick, turned by the pen angle.
   Pressure (0..1) on each node sets the nib length between b (hairline) and A (stem), so
   a stroke can swell and taper. With the nib level (angle 0) vertical strokes come out thick
   and horizontal strokes thin: vertical stress. Serifs are short strokes of the serif pen plus a
   bracket fillet; ball terminals are where the pen rests. Nothing is an outline drawn by hand.
   The sweep is the union of convex hulls of consecutive nib positions, filled non-zero,
   so there are no offset curves to self-intersect: no spikes or stars at tight corners. */
(function(root){
"use strict";
const PI=Math.PI, TAU=2*PI;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const smooth=t=>t*t*t*(t*(6*t-15)+10);   // smootherstep: unhurried swells, no abrupt pressure changes

/* ---------- parameters ---------- */
const DEFAULTS={contrast:9, stress:0, xh:412, serif:1, bracket:0.2, ball:1, opsz:12, ital:false, stem:84};
function params(o){
  o=Object.assign({},DEFAULTS,o||{});
  const k=clamp(Math.log(o.opsz/6)/Math.log(72/6),0,1);      // 0 at 6 pt, 1 at 72 pt
  const A=o.stem*(1.06-0.12*k);                                 // stems a little lighter at display sizes
  const ratio=1+(o.contrast-1)*(0.34+0.66*Math.min(1,k/0.72));  // full contrast from opsz 36 up; text sizes stay sturdy
  const B=Math.max(A/ratio,5);
  const S=Math.max(B*1.05, A*(0.27-0.16*k));                    // serif thickness: never thinner than hairline
  return {
    o, k, A, B, S, ratio,
    ang:o.stress*PI/180,
    xh:o.xh+(1-k)*22, cap:670, asc:760, desc:-250, os:11, axis:250,
    sl:A*0.74*o.serif,                                          // serif length beyond the stem
    bk:o.bracket,                                               // bracket 0 (Didone) .. 1 (Scotch)
    bd:o.ball>0? A*(0.8+0.14*(1-k))*o.ball : 0,                // teardrop diameter
    sb:30+(1-k)*18,                                             // side bearing, opens up at small sizes
    wd:1+(1-k)*0.04,                                            // skeleton widens at small sizes
    ital:!!o.ital, slant:o.ital?0.25:0,
    key:[o.contrast,o.stress,o.xh,o.serif,o.bracket,o.ball,o.opsz,o.stem].map(v=>(+v).toFixed(3)).join(',')
  };
}

/* ---------- nib ---------- */
const NK=28;
const nibCache=new Map();
function nib(a,b,ang,ne){ // superellipse nib, CCW polygon
  const key=a.toFixed(2)+'|'+b.toFixed(2)+'|'+ang.toFixed(4)+'|'+ne;
  let v=nibCache.get(key); if(v) return v;
  v=[]; const c=Math.cos(ang), s=Math.sin(ang);
  for(let i=0;i<NK;i++){const t=i/NK*TAU, ct=Math.cos(t), st=Math.sin(t);
    const x=a/2*Math.sign(ct)*Math.pow(Math.abs(ct),2/ne), y=b/2*Math.sign(st)*Math.pow(Math.abs(st),2/ne);
    v.push([x*c-y*s, x*s+y*c]);}
  if(nibCache.size>4000) nibCache.clear();
  nibCache.set(key,v); return v;
}
function hull(P){ // monotone chain, CCW
  P.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  const cr=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lo=[],up=[];
  for(const p of P){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],p)<=0)lo.pop();lo.push(p);}
  for(let i=P.length-1;i>=0;i--){const p=P[i];while(up.length>=2&&cr(up[up.length-2],up[up.length-1],p)<=0)up.pop();up.push(p);}
  lo.pop();up.pop();return lo.concat(up);
}
function area(poly){let s=0;for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length];s+=a[0]*b[1]-b[0]*a[1];}return s/2;}
function ccw(poly){return area(poly)<0?poly.slice().reverse():poly;}

/* ---------- centre-line paths ---------- */
function sePt(cx,cy,rx,ry,t,e){const c=Math.cos(t),s=Math.sin(t);
  return [cx+rx*Math.sign(c)*Math.pow(Math.abs(c),2/e), cy+ry*Math.sign(s)*Math.pow(Math.abs(s),2/e)];}
class Path{
  constructor(g,x,y,pr){this.g=g;this.pts=[[x,y,pr==null?1:pr]];this.nodes=[[x,y]];}
  get last(){return this.pts[this.pts.length-1];}
  l(x,y,pr){const [x0,y0,p0]=this.last;pr=pr==null?p0:pr;
    const n=p0===pr?1:Math.max(2,Math.ceil(Math.hypot(x-x0,y-y0)/10));
    for(let i=1;i<=n;i++){const t=i/n,u=smooth(t);this.pts.push([lerp(x0,x,t),lerp(y0,y,t),lerp(p0,pr,u)]);}
    this.nodes.push([x,y]);return this;}
  c(x1,y1,x2,y2,x,y,pr){const [x0,y0,p0]=this.last;pr=pr==null?p0:pr;
    const len=Math.hypot(x1-x0,y1-y0)+Math.hypot(x2-x1,y2-y1)+Math.hypot(x-x2,y-y2);
    const n=Math.max(6,Math.ceil(len/7));
    for(let i=1;i<=n;i++){const t=i/n,m=1-t;
      this.pts.push([m*m*m*x0+3*m*m*t*x1+3*m*t*t*x2+t*t*t*x, m*m*m*y0+3*m*m*t*y1+3*m*t*t*y2+t*t*t*y, lerp(p0,pr,smooth(t))]);}
    this.nodes.push([x,y]);return this;}
  // continue along a superellipse from angle t0 to t1 (radians, y up); call after a start at sePt(..t0)
  arc(cx,cy,rx,ry,t0,t1,pr,e){e=e||this.g.ex;const p0=this.last[2];pr=pr==null?p0:pr;
    const n=Math.max(6,Math.ceil(Math.abs(t1-t0)*Math.max(rx,ry)/7));
    for(let i=1;i<=n;i++){const t=i/n,q=sePt(cx,cy,rx,ry,lerp(t0,t1,t),e);this.pts.push([q[0],q[1],lerp(p0,pr,smooth(t))]);}
    this.nodes.push(sePt(cx,cy,rx,ry,t1,e));return this;}
  draw(opts){this.g.strokes.push({pts:this.pts,nodes:this.nodes,o:opts||{}});return this;}
}

/* ---------- glyph builder ---------- */
function builder(p){
  const g={A:p.A,B:p.B,S:p.S,sl:p.sl,bk:p.bk,bd:p.bd,X:p.xh,C:p.cap,AS:p.asc,D:p.desc,o:p.os,ex:2.1,
    strokes:[],balls:[],drops:[],fills:[],p,lc:!!p.lc};
  g.h=g.A/2;
  g.yt=g.X+g.o-g.B/2; g.yb=-g.o+g.B/2;                     // centre-line of round tops and bottoms
  g.P=(x,y,pr)=>new Path(g,x,y,pr);
  g.E=(cx,cy,rx,ry,t0,pr,e)=>{const q=sePt(cx,cy,rx,ry,t0,e||g.ex);return new Path(g,q[0],q[1],pr);};
  g.pt=(cx,cy,rx,ry,t,e)=>sePt(cx,cy,rx,ry,t,e||g.ex);
  g.ring=(cx,cy,rx,ry,pr,e)=>g.E(cx,cy,rx,ry,0,pr==null?1:pr,e).arc(cx,cy,rx,ry,0,TAU,pr==null?1:pr,e).draw({closed:true});
  g.stem=(x,y0,y1,pr,o)=>{pr=pr==null?1:pr;return g.P(x,y0+g.B/2,pr).l(x,y1-g.B/2,pr).draw(o);};
  g.hair=(x0,y0,x1,y1,o)=>g.P(x0,y0,0).l(x1,y1,0).draw(o);
  g.bar=(x0,x1,y)=>{const a=Math.min(x0,x1),b=Math.max(x0,x1);return g.P(a+g.B/2,y,0).l(b-g.B/2,y,0).draw({role:'bar'});}; // horizontal hairline, ink x0..x1 centred on y
  g.dot=(x,y,d)=>{d=d==null?g.bd:d;if(d>0)g.balls.push([x,y,d/2]);};
  // a terminal: a teardrop that grows out of the stroke ending nearest to it (round if no stroke ends there)
  g.ball=(x,y,d)=>{d=d==null?g.bd:d;if(d>0)g.drops.push([x,y,d/2]);};
  g.fill=(pts,role)=>g.fills.push({pts,role:role||'fill'});
  // serif on a stem of width w centred at x; y = outer edge; dir=+1 foot (serif rises from y), -1 head (hangs from y)
  g.serif=(x,y,dir,side,w,len)=>{
    w=w==null?g.A:w; len=len==null?g.sl:len; if(len<=1) return; const S=g.S, hw=w/2, cy=y+dir*S/2;
    const L=side==='r'?x:x-hw-len, R=side==='l'?x:x+hw+len;
    if(dir<0&&side==='l'&&g.lc){ // lowercase head serif: a gentle wedge, thin at the tip
      const dw=len*0.3; g.P(L+S*0.3,cy-dw,0).l(x,cy,0).draw({a:S*0.9,b:S,ne:5,role:'serif'});
      g.fill([[L+S*0.2,cy-dw-S*0.3],[x,y-S*1.1],[x,y],[L+S*0.2,cy-dw+S*0.45]],'bracket');}
    else g.P(L+S/2,cy,0).l(R-S/2,cy,0).draw({a:S,b:S,ne:7,role:'serif'});
    const bh=g.bk*len*1.0, bl=g.bk*len*0.85;
    if(bh>2){
      const br=(xe,sx)=>{const pts=[[xe-sx*2,y+dir*S*0.5],[xe-sx*2,y+dir*(S+bh)]];const c=[xe,y+dir*S],e=[xe+sx*bl,y+dir*S];
        const s0=[xe,y+dir*(S+bh)];for(let i=0;i<=10;i++){const t=i/10,m=1-t;pts.push([m*m*s0[0]+2*m*t*c[0]+t*t*e[0],m*m*s0[1]+2*m*t*c[1]+t*t*e[1]]);}
        pts.push([xe+sx*bl,y+dir*S*0.5]);g.fill(pts,'bracket');};
      if(side!=='r') br(x-hw,-1); if(side!=='l') br(x+hw,1);
    }
  };
  // vertical beak serif (Modern capitals): hairline spur hanging from a horizontal arm end
  g.beak=(x,y,dir,len)=>{len=len==null?g.A*1.25:len;const S=g.S*0.95;g.P(x-S/2,y,0.15).l(x-S/2,y+dir*len,0).draw({a:S*1.05,b:S,ne:4,role:'serif'});};
  return g;
}

/* ---------- glyph tables ---------- */
const G={}, GI={};   // roman, italic overrides
const flags=ch=>({cap:/^[A-ZΓΔΣΩ]$/.test(ch),lc:/^[a-zﬁﬂﬀ]$/.test(ch)});
function def(ch,fn,o){G[ch]=Object.assign({fn},flags(ch),o||{});}
function idef(ch,fn,o){GI[ch]=Object.assign({fn},flags(ch),o||{});}

/* =====================================================================
   ROMAN LOWERCASE. Coordinates are centre-lines. g.h = half stem.
   g.yt / g.yb = centre-line of round tops / bottoms (ink reaches x-height + overshoot).
   ===================================================================== */
function arch(g,x0,x1,top){ // hairline branch out of the stem, over the shoulder, down the right stem
  const {B,h}=g, yt=top+g.o-B/2, xm=(x0+x1)/2+12;
  g.P(x0+h*0.3,top*0.6,0).c(x0+h*0.3+30,top*0.88,xm-(xm-x0)*0.55,yt,xm,yt,0.55)
   .c(xm+(x1-xm)*0.6,yt,x1,top*0.9,x1,top*0.6,1).l(x1,B/2,1).draw();
  g.serif(x1,0,1,'b');
}
function bowlRight(g,x0){ // b, p: bowl hanging off a left stem
  const {X,o,B}=g, rx=205, cx=x0+rx, cy=X/2, ry=X/2+o-B/2, t0=0.84*PI;
  g.E(cx,cy,rx,ry,t0,0).arc(cx,cy,rx,ry,t0,0.5*PI,0.6).arc(cx,cy,rx,ry,0.5*PI,0,1)
   .arc(cx,cy,rx,ry,0,-0.5*PI,0.6).arc(cx,cy,rx,ry,-0.5*PI,-t0,0).draw();
}
function bowlLeft(g,x1){ // d, q
  const {X,o,B}=g, rx=205, cx=x1-rx, cy=X/2, ry=X/2+o-B/2, t0=0.16*PI;
  g.E(cx,cy,rx,ry,t0,0).arc(cx,cy,rx,ry,t0,0.5*PI,0.6).arc(cx,cy,rx,ry,0.5*PI,PI,1)
   .arc(cx,cy,rx,ry,PI,1.5*PI,0.6).arc(cx,cy,rx,ry,1.5*PI,2*PI-t0,0).draw();
}
const dotD=g=>g.A*1.16;

def('n',g=>{const {X}=g; g.stem(0,0,X); g.serif(0,X,-1,'l'); g.serif(0,0,1,'b'); arch(g,0,330,X);});
def('m',g=>{const {X}=g; g.stem(0,0,X); g.serif(0,X,-1,'l'); g.serif(0,0,1,'b'); arch(g,0,290,X); arch(g,290,580,X);});
def('h',g=>{const {X,AS}=g; g.stem(0,0,AS); g.serif(0,AS,-1,'l'); g.serif(0,0,1,'b'); arch(g,0,330,X);});
def('u',g=>{const {B,X,yb,h}=g, x0=0, x1=330, xm=(x0+x1)/2-12;
  g.P(x0,X-B/2,1).l(x0,X*0.36,1).c(x0,X*0.08,xm-(xm-x0)*0.6,yb,xm,yb,0.55)
   .c(xm+(x1-xm)*0.55,yb,x1-h*0.3-30,X*0.12,x1-h*0.3,X*0.4,0).draw();
  g.serif(x0,X,-1,'l'); g.stem(x1,0,X); g.serif(x1,X,-1,'l'); g.serif(x1,0,1,'r');});
def('o',g=>{const {X,o,B,h}=g; g.ring(220,X/2,220-h,X/2+o-B/2);},{l:0.82,r:0.82});
def('c',g=>{const {X,o,B,h,bd}=g, cx=220, rx=220-h, cy=X/2, ry=X/2+o-B/2, t0=0.2*PI, s=g.pt(cx,cy,rx,ry,t0);
  g.E(cx,cy,rx,ry,t0,0.3).arc(cx,cy,rx,ry,t0,0.5*PI,0.55).arc(cx,cy,rx,ry,0.5*PI,PI,1)
   .arc(cx,cy,rx,ry,PI,1.5*PI,0.7).arc(cx,cy,rx,ry,1.5*PI,1.84*PI,0).draw();
  g.ball(s[0]-bd*0.2,s[1]-bd*0.12);},{l:0.82,r:0.7});
def('e',g=>{const {X,o,B,h}=g, cx=222, rx=222-h, cy=X/2, ry=X/2+o-B/2, yc=X*0.56;
  const t0=Math.asin(Math.pow((yc-cy)/ry,g.ex/2));
  g.bar(cx-rx-h*0.5,cx+rx+h*0.5,yc);
  g.E(cx,cy,rx,ry,t0,0.9).arc(cx,cy,rx,ry,t0,0.5*PI,0.7).arc(cx,cy,rx,ry,0.5*PI,PI,1)
   .arc(cx,cy,rx,ry,PI,1.5*PI,0.7).arc(cx,cy,rx,ry,1.5*PI,1.86*PI,0).draw();},{l:0.82,r:0.75});
def('a',g=>{const {X,B,h,yt,yb,bd}=g, xr=320, xq=h+4, xb=h+Math.max(bd,g.A)*0.42, yB=X*0.7;
  g.P(xb,yB,0.25).c(xb+6,X*0.94,xr-205,yt,xr-115,yt,0.55).c(xr-28,yt,xr,X*0.86,xr,X*0.62,1).l(xr,X*0.13,1)
   .c(xr,X*0.03,xr+22,yb,xr+56,yb,0.25).c(xr+78,yb,xr+92,16,xr+96,40,0).draw();
  g.P(xr-h*0.3,X*0.57,0).c(xr-110,X*0.53,xq,X*0.45,xq,X*0.23,1).c(xq,X*0.05,xq+48,yb,xq+108,yb,0.6)
   .c(xq+185,yb,xr-40,X*0.06,xr-h*0.3,X*0.22,0).draw();
  g.ball(xb,yB);},{r:0.6});
def('b',g=>{const {AS}=g; g.stem(0,0,AS); g.serif(0,AS,-1,'l'); bowlRight(g,0);},{r:0.82});
def('p',g=>{const {X,D}=g; g.stem(0,D,X); g.serif(0,X,-1,'l'); g.serif(0,D,1,'b'); bowlRight(g,0);},{r:0.82});
def('d',g=>{const {AS}=g, x1=410; g.stem(x1,0,AS); g.serif(x1,AS,-1,'l'); g.serif(x1,0,1,'r'); bowlLeft(g,x1);},{l:0.82});
def('q',g=>{const {X,D}=g, x1=410; g.stem(x1,D,X); g.serif(x1,D,1,'b'); bowlLeft(g,x1);},{l:0.82});
def('i',g=>{const {X,AS}=g; g.stem(0,0,X); g.serif(0,X,-1,'l'); g.serif(0,0,1,'b'); g.dot(-g.A*0.04,X+(AS-X)*0.66,dotD(g));});
def('j',g=>{const {X,AS,D,B,bd,o}=g, x0=0, yb=D-o+B/2;
  g.P(x0,X-B/2,1).l(x0,D+150,1).c(x0,D+50,x0-40,yb,x0-105,yb,0.5).c(x0-150,yb,x0-182,D+22,x0-190,D+bd*0.55+8,0.25).draw();
  g.ball(x0-190,D+bd*0.55+8); g.serif(x0,X,-1,'l'); g.dot(-g.A*0.04,X+(AS-X)*0.66,dotD(g));},{l:0.5});
def('k',g=>{const {X,AS,A,B,h}=g, x0=0, ax=x0+262;
  g.stem(x0,0,AS); g.serif(x0,AS,-1,'l'); g.serif(x0,0,1,'b');
  g.P(x0+h-4,X*0.26,0).l(ax,X-B/2,0).draw(); g.serif(ax,X,-1,'b',B*1.6,g.sl*0.8);
  g.P(x0+128,X*0.55,0.85).l(x0+292,B/2,1).draw(); g.serif(x0+292,0,1,'b',A*0.95);},{r:0.6});
def('l',g=>{const {AS}=g; g.stem(0,0,AS); g.serif(0,AS,-1,'l'); g.serif(0,0,1,'b');});
def('r',g=>{const {X,B,h,yt,bd,A}=g, x0=0, xe=x0+228, ye=X-Math.max(bd,A*0.6)*0.45-8;
  g.stem(x0,0,X); g.serif(x0,X,-1,'l'); g.serif(x0,0,1,'b',A,g.sl*1.15);
  g.P(x0+h*0.3,X*0.6,0).c(x0+h*0.3+28,X*0.88,x0+98,yt,x0+158,yt,0.5).c(x0+200,yt,xe,X*0.96,xe,ye,0.25).draw();
  g.ball(xe-bd*0.05,ye);},{r:0.5});
def('s',g=>{const {X,B,yt,yb,h,S}=g, W=330;
  g.P(W-14,X*0.79,0.12).c(W-28,X*0.95,W*0.68,yt,W*0.5,yt,0.5).c(W*0.24,yt,h+2,X*0.92,h+2,X*0.74,1)
   .c(h+2,X*0.5,W-h-2,X*0.52,W-h-2,X*0.27,1).c(W-h-2,X*0.08,W*0.76,yb,W*0.5,yb,0.5)
   .c(W*0.27,yb,30,X*0.06,12,X*0.21,0.12).draw();
  g.P(W-14,X*0.66,0).l(W-14,X*0.9,0).draw({a:S*1.4,b:S,role:'serif'});
  g.P(12,X*0.1,0).l(12,X*0.34,0).draw({a:S*1.4,b:S,role:'serif'});},{l:0.8,r:0.8});
def('t',g=>{const {X,B,yb,h}=g, x0=0;
  g.P(x0,X+118,0.45).l(x0,X*0.8,1).l(x0,X*0.25,1).c(x0,X*0.04,x0+40,yb,x0+100,yb,0.45).c(x0+150,yb,x0+186,X*0.06,x0+196,X*0.2,0).draw();
  g.bar(x0-h-82,x0+h+108,X-B/2);},{l:0.7,r:0.6});
def('v',g=>{const {X,A,B,o}=g, xl=0, xm=225, xr=445;
  g.P(xl,X-B/2,1).l(xm-A*0.2,B/2-o,0.9).draw(); g.P(xm+A*0.1,B/2-o,0).l(xr,X-B/2,0).draw();
  g.serif(xl,X,-1,'b',A); g.serif(xr,X,-1,'b',B*1.6,g.sl*0.85);},{l:0.5,r:0.5});
def('w',g=>{const {X,A,B,o}=g, a=0, b=172, c=318, d=490, e=640;
  g.P(a,X-B/2,1).l(b-A*0.2,B/2-o,0.9).draw(); g.P(b+A*0.1,B/2-o,0).l(c,X-B/2,0).draw();
  g.P(c,X-B/2,1).l(d-A*0.2,B/2-o,0.9).draw(); g.P(d+A*0.1,B/2-o,0).l(e,X-B/2,0).draw();
  g.serif(a,X,-1,'b',A); g.serif(c,X,-1,'b',A*1.1,g.sl*0.7); g.serif(e,X,-1,'b',B*1.6,g.sl*0.85);},{l:0.5,r:0.5});
def('x',g=>{const {X,A,B}=g, xl=0, xr=410;
  g.P(xl+8,X-B/2,1).l(xr-8,B/2,1).draw(); g.P(xl+12,B/2,0).l(xr-12,X-B/2,0).draw();
  g.serif(xl+8,X,-1,'b',A); g.serif(xr-8,0,1,'b',A); g.serif(xl+12,0,1,'b',B*1.6,g.sl*0.85); g.serif(xr-12,X,-1,'b',B*1.6,g.sl*0.85);},{l:0.6,r:0.6});
def('y',g=>{const {X,A,B,D,bd,o}=g, xl=0, xm=225, xr=445;
  g.P(xl,X-B/2,1).l(xm-A*0.15,B/2-o,0.85).draw();
  const k=(xr-xm)/X, xb=xm-k*(-D*0.55);
  g.P(xr,X-B/2,0).l(xb,D*0.55,0.1).c(xb-k*60,D*0.55-60,xm-150,D+bd*0.55+6,xm-205,D+bd*0.55+6,0.35).draw();
  g.ball(xm-205,D+bd*0.55+6);
  g.serif(xl,X,-1,'b',A); g.serif(xr,X,-1,'b',B*1.6,g.sl*0.85);},{l:0.5,r:0.5});
def('z',g=>{const {X,A,B,S}=g, x0=0, x1=370;
  g.bar(x0,x1,X-B/2); g.bar(x0,x1,B/2);
  g.P(x1-A*0.5,X-B,1).l(x0+A*0.5,B,1).draw();
  g.P(x0+S*0.7,X,0).l(x0+S*0.7,X-115,0).draw({a:S*1.4,b:S,role:'serif'});
  g.P(x1-S*0.7,0,0).l(x1-S*0.7,125,0).draw({a:S*1.4,b:S,role:'serif'});},{l:0.7,r:0.7});
def('f',g=>{const {X,AS,B,h,bd,A,o}=g, x0=0, yt2=AS+o-B/2, xe=x0+232, ye=AS-Math.max(bd,A*0.6)*0.5-12;
  g.P(x0,B/2,1).l(x0,AS-175,1).c(x0,AS-45,x0+62,yt2,x0+150,yt2,0.5).c(x0+205,yt2,xe,AS-25,xe,ye,0.25).draw();
  g.ball(xe,ye); g.bar(x0-h-78,x0+h+118,X-B/2); g.serif(x0,0,1,'b',A,g.sl*1.2);},{r:-0.7});

/* =====================================================================
   ROMAN CAPITALS. Thick stems, hairline arms, beaks on arm ends.
   ===================================================================== */
function vbeak(g,x,y0,y1){g.P(x,y0,0).l(x,y1,0).draw({a:g.S*1.4,b:g.S,role:'serif'});}
function dBowl(g,x0,y0,y1,xr,xf){ // flat hairline top and bottom, round thick right side
  const {B}=g, r=(y1-y0)/2, ym=(y0+y1)/2, a=y1-B/2, b=y0+B/2;
  g.P(x0,a,0).l(xf,a,0).c(xf+(xr-xf)*0.62,a,xr,ym+r*0.55,xr,ym,1).c(xr,ym-r*0.55,xf+(xr-xf)*0.62,b,xf,b,0).l(x0,b,0).draw();
}
def('H',g=>{const {C,B}=g, x1=470; g.stem(0,0,C); g.stem(x1,0,C); g.bar(0,x1,C*0.5);
  for(const x of [0,x1]){g.serif(x,C,-1,'b'); g.serif(x,0,1,'b');}});
def('I',g=>{const {C}=g; g.stem(0,0,C); g.serif(0,C,-1,'b'); g.serif(0,0,1,'b');});
def('E',g=>{const {C,B,h}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'l');
  g.bar(-h,385,C-B/2); vbeak(g,385-g.S*0.7,C,C-118);
  g.bar(-h,330,C*0.51); vbeak(g,330-g.S*0.7,C*0.51-60,C*0.51+60);
  g.bar(-h,405,B/2); vbeak(g,405-g.S*0.7,0,128);},{r:0.6});
def('F',g=>{const {C,B,h}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'b');
  g.bar(-h,385,C-B/2); vbeak(g,385-g.S*0.7,C,C-118);
  g.bar(-h,325,C*0.5); vbeak(g,325-g.S*0.7,C*0.5-60,C*0.5+60);},{r:0.5});
def('L',g=>{const {C,B,h}=g; g.stem(0,0,C); g.serif(0,C,-1,'b'); g.serif(0,0,1,'l');
  g.bar(-h,395,B/2); vbeak(g,395-g.S*0.7,0,135);},{r:0.6});
def('T',g=>{const {C,B}=g, W=540; g.bar(0,W,C-B/2); vbeak(g,g.S*0.7,C,C-130); vbeak(g,W-g.S*0.7,C,C-130);
  g.stem(W/2,0,C); g.serif(W/2,0,1,'b');},{l:0.5,r:0.5});
def('D',g=>{const {C}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'l'); dBowl(g,0,0,C,500,200);},{r:0.85});
def('B',g=>{const {C}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'l');
  dBowl(g,0,C*0.52-g.B,C,385,170); dBowl(g,0,0,C*0.52,440,190);},{r:0.8});
def('P',g=>{const {C}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'b'); dBowl(g,0,C*0.44,C,420,190);},{r:0.7});
function roundC(g,cx,rx,t0,t1){const {C,o,B}=g, cy=C/2, ry=C/2+o-B/2;
  const p=g.E(cx,cy,rx,ry,t0,0.2).arc(cx,cy,rx,ry,t0,0.5*PI,0.6).arc(cx,cy,rx,ry,0.5*PI,PI,1).arc(cx,cy,rx,ry,PI,1.5*PI,0.6).arc(cx,cy,rx,ry,1.5*PI,t1,0.15).draw();
  return [g.pt(cx,cy,rx,ry,t0),g.pt(cx,cy,rx,ry,t1)];}
def('C',g=>{const {C,h}=g, cx=300; const [s,e]=roundC(g,cx,cx-h,0.2*PI,1.8*PI);
  vbeak(g,s[0]-2,s[1]-110,s[1]+30); vbeak(g,e[0]-2,e[1]-20,e[1]+100);},{l:0.82,r:0.6});
def('O',g=>{const {C,o,B,h}=g; g.ring(330,C/2,330-h,C/2+o-B/2);},{l:0.82,r:0.82});
def('S',g=>{const {C,B,o,h,S}=g, W=420, yt=C+o-B/2, yb=-o+B/2;
  g.P(W-16,C*0.78,0.15).c(W-30,C*0.95,W*0.68,yt,W*0.5,yt,0.5).c(W*0.22,yt,h+2,C*0.92,h+2,C*0.75,1)
   .c(h+2,C*0.5,W-h-2,C*0.52,W-h-2,C*0.26,1).c(W-h-2,C*0.08,W*0.76,yb,W*0.5,yb,0.5)
   .c(W*0.24,yb,26,C*0.06,12,C*0.2,0.15).draw();
  vbeak(g,W-16,C*0.68,C*0.92); vbeak(g,12,C*0.08,C*0.33);},{l:0.8,r:0.8});
def('U',g=>{const {C,B,o,h,A}=g, x0=0, x1=480, yb=-o+B/2, xm=(x0+x1)/2;
  g.P(x0,C-B/2,1).l(x0,C*0.32,1).c(x0,C*0.08,xm-150,yb,xm,yb,0.5).c(xm+150,yb,x1,C*0.08,x1,C*0.32,0).l(x1,C-B/2,0).draw();
  g.serif(x0,C,-1,'b'); g.serif(x1,C,-1,'b',B*1.6,g.sl*0.9);});
def('V',g=>{const {C,A,B,o}=g, xl=0, xm=275, xr=550;
  g.P(xl,C-B/2,1).l(xm-A*0.22,B/2-o,0.9).draw(); g.P(xm+A*0.1,B/2-o,0).l(xr,C-B/2,0).draw();
  g.serif(xl,C,-1,'b'); g.serif(xr,C,-1,'b',B*1.6);},{l:0.45,r:0.45});
def('W',g=>{const {C,A,B,o}=g, a=0, b=200, c=395, d=600, e=800;
  g.P(a,C-B/2,1).l(b-A*0.2,B/2-o,0.9).draw(); g.P(b+A*0.1,B/2-o,0).l(c,C-B/2,0).draw();
  g.P(c,C-B/2,1).l(d-A*0.2,B/2-o,0.9).draw(); g.P(d+A*0.1,B/2-o,0).l(e,C-B/2,0).draw();
  g.serif(a,C,-1,'b'); g.serif(c,C,-1,'b',A*1.1,g.sl*0.7); g.serif(e,C,-1,'b',B*1.6);},{l:0.45,r:0.45});
def('X',g=>{const {C,A,B}=g, xl=0, xr=500;
  g.P(xl+8,C-B/2,1).l(xr-8,B/2,1).draw(); g.P(xl+14,B/2,0).l(xr-14,C-B/2,0).draw();
  g.serif(xl+8,C,-1,'b'); g.serif(xr-8,0,1,'b'); g.serif(xl+14,0,1,'b',B*1.6); g.serif(xr-14,C,-1,'b',B*1.6);},{l:0.55,r:0.55});
def('Y',g=>{const {C,A,B}=g, xl=0, xm=260, xr=520, yj=C*0.44;
  g.P(xl,C-B/2,1).l(xm,yj,1).draw(); g.P(xr,C-B/2,0).l(xm+A*0.2,yj,0).draw(); g.stem(xm,0,yj+B);
  g.serif(xl,C,-1,'b'); g.serif(xr,C,-1,'b',B*1.6); g.serif(xm,0,1,'b');},{l:0.45,r:0.45});
def('Z',g=>{const {C,A,B,S}=g, x0=0, x1=470;
  g.bar(x0,x1,C-B/2); g.bar(x0,x1,B/2); g.P(x1-A*0.5,C-B,1).l(x0+A*0.5,B,1).draw();
  vbeak(g,x0+S*0.7,C,C-140); vbeak(g,x1-S*0.7,0,150);},{l:0.7,r:0.7});
def('K',g=>{const {C,A,B,h}=g, x0=0;
  g.stem(x0,0,C); g.serif(x0,C,-1,'b'); g.serif(x0,0,1,'b');
  g.P(x0+h-4,C*0.3,0).l(x0+410,C-B/2,0).draw(); g.serif(x0+410,C,-1,'b',B*1.6,g.sl*0.9);
  g.P(x0+180,C*0.53,0.85).l(x0+452,B/2,1).draw(); g.serif(x0+452,0,1,'b',A*0.95);},{r:0.5});
def('M',g=>{const {C,A,B}=g, x0=0, xm=330, x1=660;
  g.stem(x0,0,C,0); g.P(x0+A*0.05,C-B/2,1).l(xm-A*0.2,B/2-g.o,0.9).draw(); g.P(xm+A*0.1,B/2-g.o,0).l(x1-A*0.3,C-B/2,0).draw(); g.stem(x1,0,C);
  g.serif(x0,C,-1,'l',B*1.6); g.serif(x0,0,1,'b',B*1.6); g.serif(x1,C,-1,'r'); g.serif(x1,0,1,'b');});
def('N',g=>{const {C,A,B,o}=g, x0=0, x1=500;
  g.stem(x0,0,C,0); g.P(x0+A*0.1,C-B/2,1).l(x1-A*0.15,B/2-o*2,1).draw(); g.P(x1,C-B/2,0).l(x1,-o*2,0).draw();
  g.serif(x0,C,-1,'l',B*1.6); g.serif(x0,0,1,'b',B*1.6); g.serif(x1,C,-1,'b',B*1.6);});
def('A',g=>{const {C,A,B,o}=g, xl=0, xm=280, xr=560;
  g.P(xl,B/2,0).l(xm-A*0.15,C+o-B/2,0).draw(); g.P(xm-A*0.25,C+o-B/2,0.9).l(xr,B/2,1).draw();
  g.bar(xl+95,xr-85,C*0.3); g.serif(xl,0,1,'b',B*1.6); g.serif(xr,0,1,'b');},{l:0.45,r:0.45});

/* ---------- 0.2: refined forms ---------- */
def('g',g=>{const {X,B,D,o,bd,h}=g, cx=198, rx=138, cy=X*0.655, ry=X*0.345-B/2+o*0.5, yb2=D-o+B/2;
  g.ring(cx,cy,rx,ry);
  const e=g.pt(cx,cy,rx,ry,0.3*PI);
  g.P(e[0],e[1],0).c(e[0]+26,X+2,cx+rx+18,X+16,cx+rx+66,X+12,0.12).draw();          // ear: a hairline with a small drop
  g.ball(cx+rx+70,X+2,bd*0.62);
  const s=g.pt(cx,cy,rx,ry,1.22*PI);
  g.P(s[0],s[1],0.3).c(s[0]-34,s[1]-50,46,46,140,34,0).l(300,32,0)               // link: thin, then level
   .c(398,32,436,-12,436,-80,1).c(436,-178,342,yb2,228,yb2,0.5)                    // lower loop, right and bottom
   .c(108,yb2,22,-188,22,-130,1).c(22,-82,62,-54,118,-46,0).draw();},{r:0.7});    // left side, left open
def('G',g=>{const {C,A,B,h}=g, cx=300, rx=cx-h; const [s]=roundC(g,cx,rx,0.2*PI,1.88*PI);
  vbeak(g,s[0]-2,s[1]-100,s[1]+24); const xr=cx+rx*0.99, yS=C*0.44;
  g.P(xr,yS-B/2,1).l(xr,C*0.12,1).l(xr,-4,0.35).draw();                            // stem with a fine spur below
  g.serif(xr,yS,-1,'b',A,g.sl*0.7);},{l:0.82,r:0.6});
def('R',g=>{const {C,A,B,o}=g, yb=-o+B/2; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'b'); dBowl(g,0,C*0.47,C,405,180);
  g.P(170,C*0.47+B/2,0.1).c(298,C*0.45,352,C*0.36,360,C*0.2,1).l(363,C*0.1,1)
   .c(365,C*0.02,392,yb,428,yb,0.35).c(458,yb,476,16,482,44,0).draw();},{r:0.5});  // curved leg, fine exit
def('Q',g=>{const {C,o,B,h}=g, cx=325; g.ring(cx,C/2,cx-h,C/2+o-B/2);
  g.P(cx-40,-o+B/2+8,0.25).c(cx+10,-62,cx+110,-122,cx+235,-120,0.8).c(cx+305,-119,cx+350,-102,cx+390,-82,0).draw();},{l:0.82,r:0.45});
def('J',g=>{const {C,B,bd,D}=g, x0=230, yb=D*0.62;
  g.P(x0,C-B/2,1).l(x0,C*0.04,1).c(x0,yb*0.55,x0-40,yb,x0-108,yb,0.5).c(x0-162,yb,x0-196,yb*0.76,x0-204,yb*0.5,0.25).draw();
  g.ball(x0-204,yb*0.5); g.serif(x0,C,-1,'b');},{l:0.6});
def('&',g=>{const {C,B,o,h}=g, yt=C+o-B/2, yb=-o+B/2;
  g.P(615,yb,0).c(540,yb,470,30,410,C*0.18,0.9).c(330,C*0.36,215,C*0.5,215,C*0.73,1)
   .c(215,C*0.9,255,yt,305,yt,0.5).c(360,yt,392,C*0.92,392,C*0.82,1).c(392,C*0.67,300,C*0.6,215,C*0.52,0.3)
   .c(110,C*0.44,h+4,C*0.34,h+4,C*0.22,1).c(h+4,C*0.06,120,yb,232,yb,0.5).c(362,yb,458,C*0.18,508,C*0.41,0.2).draw();
  g.bar(470,620,C*0.42);},{l:0.7,r:0.55});

/* ---------- ligatures ---------- */
function fTop(g,x0,xe){const {AS,B,o,bd,A}=g, yt2=AS+o-B/2, ye=AS-Math.max(bd,A*0.6)*0.5-14;
  return g.P(x0,B/2,1).l(x0,AS-178,1).c(x0,AS-45,x0+66,yt2,x0+(xe-x0)*0.62,yt2,0.5).c(x0+(xe-x0)*0.88,yt2,xe,AS-28,xe,ye,0.25);}
def('ﬁ',g=>{const {X,AS,B,h,bd,A}=g, x0=0, xi=292, ye=AS-Math.max(bd,A*0.6)*0.5-14;
  fTop(g,x0,xi).draw(); g.ball(xi,ye); g.stem(xi,0,X); g.bar(x0-h-78,xi,X-B/2);
  g.serif(x0,0,1,'b',A,g.sl*1.2); g.serif(xi,0,1,'b');});
def('ﬂ',g=>{const {X,AS,B,o,h,A}=g, x0=0, xl=292, yt2=AS+o-B/2;
  g.P(x0,B/2,1).l(x0,AS-178,1).c(x0,AS-45,x0+66,yt2,x0+160,yt2,0.5).c(x0+240,yt2,xl,AS-20,xl,AS-110,1).l(xl,B/2,1).draw();
  g.bar(x0-h-78,xl,X-B/2); g.serif(x0,0,1,'b',A,g.sl*1.2); g.serif(xl,0,1,'b');});
def('ﬀ',g=>{const {X,AS,B,o,h,bd,A}=g, x0=0, x2=262, yt2=AS+o-B/2, ye=AS-Math.max(bd,A*0.6)*0.5-14;
  g.P(x0,B/2,1).l(x0,AS-178,1).c(x0,AS-45,x0+60,yt2,x0+140,yt2,0.5).c(x0+200,yt2,x2-h-6,AS-30,x2-h*0.4,AS-82,0.05).draw();
  fTop(g,x2,x2+232).draw(); g.ball(x2+232,ye); g.bar(x0-h-78,x2+h+118,X-B/2);
  g.serif(x0,0,1,'b',A,g.sl*1.2); g.serif(x2,0,1,'b',A,g.sl*1.2);},{r:-0.7});

/* ---------- figures: lining, tabular ---------- */
const FIG={adv:520};
def('0',g=>{const {C,o,B,h}=g; g.ring(250,C/2,200-h,C/2+o-B/2,1,2.05);},FIG);
def('1',g=>{const {C,B,A}=g, x=260; g.stem(x,0,C); g.P(x-g.h+6,C-B*0.7,0.35).l(x-125,C*0.8,0).draw(); g.serif(x,0,1,'b',A,g.sl*1.35);},FIG);
def('2',g=>{const {C,B,o,bd,S}=g, yt=C+o-B/2;
  g.P(95,C*0.71,0.25).c(98,C*0.93,170,yt,255,yt,0.5).c(360,yt,420,C*0.86,420,C*0.68,1).c(420,C*0.46,235,C*0.3,72,B,0.85).draw();
  g.ball(95,C*0.71); g.bar(52,448,B/2); vbeak(g,448-S*0.7,0,125);},FIG);
def('3',g=>{const {C,B,o,bd}=g, yt=C+o-B/2, yb=-o+B/2;
  g.P(92,C*0.75,0.25).c(98,C*0.95,170,yt,248,yt,0.5).c(350,yt,402,C*0.88,402,C*0.76,1).c(402,C*0.62,322,C*0.545,205,C*0.545,0).draw();
  g.P(205,C*0.545,0).c(352,C*0.545,432,C*0.45,432,C*0.28,1).c(432,C*0.08,342,yb,240,yb,0.5).c(150,yb,82,C*0.06,78,C*0.21,0.25).draw();
  g.ball(92,C*0.75); g.ball(80,C*0.2);},FIG);
def('4',g=>{const {C,B,A}=g, x=345; g.P(x-A*0.2,C-B/2,0).l(38,C*0.28,0).draw(); g.stem(x,0,C);
  g.bar(30,462,C*0.27); g.serif(x,0,1,'b',A,g.sl*1.1);},FIG);
def('5',g=>{const {C,B,o}=g, yb=-o+B/2;
  g.bar(118,415,C-B/2); g.P(124,C-B/2,0.45).l(124,C*0.53,0.45).draw();
  g.P(124,C*0.54,0).c(170,C*0.62,215,C*0.635,260,C*0.635,0.4).c(380,C*0.635,438,C*0.5,438,C*0.32,1)
   .c(438,C*0.1,345,yb,245,yb,0.5).c(150,yb,82,C*0.06,78,C*0.21,0.25).draw(); g.ball(80,C*0.2);},FIG);
function six(g,M){const {C,B,o}=g, yt=C+o-B/2, ry=C*0.32+o-B/2-6;
  const T=(x,y)=>M?[500-x,C-y]:[x,y], P=(x,y,pr)=>{const q=T(x,y);return g.P(q[0],q[1],pr);};
  const p=P(405,C*0.82,0.25); const c=(a,b,c2,d,e,f,pr)=>{const q1=T(a,b),q2=T(c2,d),q3=T(e,f);p.c(q1[0],q1[1],q2[0],q2[1],q3[0],q3[1],pr);};
  c(398,C*0.96,330,yt,262,yt,0.5); c(140,yt,75,C*0.75,75,C*0.36,1); p.draw();
  const q=T(250,C*0.32-6); g.ring(q[0],q[1],175,ry); const b=T(405,C*0.82); g.ball(b[0],b[1]);}
def('6',g=>six(g,false),FIG);
def('9',g=>six(g,true),FIG);
def('7',g=>{const {C,B,A}=g; g.bar(48,452,C-B/2); vbeak(g,48+g.S*0.7,C,C-130);
  g.P(452-A*0.5,C-B,0.9).c(390,C*0.6,240,C*0.38,222,B/2,1).draw();},FIG);
def('8',g=>{const {C,o,B}=g; const yj=C*0.535; g.ring(250,(yj+C+o-B/2)/2,148,(C+o-B/2-yj)/2); g.ring(250,(yj-o+B/2)/2,176,(yj+o-B/2)/2);},FIG);

/* ---------- punctuation and delimiters ---------- */
function paren(g,x0,w,top,bot,dir){const m=(top+bot)/2,H=top-bot, xr=x0+w*dir, B=g.B;
  g.P(xr,top-B/2,0).c(xr-dir*w*0.82,top-H*0.2,x0,m+H*0.26,x0,m,1).c(x0,m-H*0.26,xr-dir*w*0.82,bot+H*0.2,xr,bot+B/2,0).draw();}
function brack(g,x,top,bot,dir){const {B}=g; g.stem(x,bot,top,1); g.bar(x-dir*g.h,x+dir*130,top-B/2); g.bar(x-dir*g.h,x+dir*130,bot+B/2);
  if(dir<0){} }
def(' ',g=>{},{adv:270,empty:true});
def('.',g=>{g.dot(0,dotD(g)/2,dotD(g));},{l:0.9,r:0.9});
def(',',g=>{const d=dotD(g); g.ball(0,d/2,d); g.P(d*0.22,d*0.32,0.85).c(d*0.3,-d*0.3,0,-d*0.9,-d*0.45,-d*1.25,0).draw();},{l:0.9,r:0.9});
def(':',g=>{const d=dotD(g); g.dot(0,d/2,d); g.dot(0,g.X-d/2,d);},{l:0.9,r:0.9});
def(';',g=>{const d=dotD(g); g.dot(0,g.X-d/2,d); g.ball(0,d/2,d); g.P(d*0.22,d*0.32,0.85).c(d*0.3,-d*0.3,0,-d*0.9,-d*0.45,-d*1.25,0).draw();},{l:0.9,r:0.9});
def('!',g=>{const d=dotD(g),{C,B}=g; g.P(0,C-B/2,1).l(0,C*0.6,0.85).l(0,d+70,0.15).draw(); g.dot(0,d/2,d);},{l:0.9,r:0.9});
def('?',g=>{const d=dotD(g),{C,B,o}=g, yt=C+o-B/2;
  g.P(48,C*0.72,0.25).c(52,C*0.94,120,yt,190,yt,0.5).c(280,yt,325,C*0.86,325,C*0.73,1).c(325,C*0.55,190,C*0.5,190,C*0.33,0.6).l(190,d+80,0.2).draw();
  g.ball(48,C*0.72); g.dot(190,d/2,d);},{l:0.8,r:0.8});
def("'",g=>{const {C}=g; g.P(0,C-g.B/2,1).l(0,C*0.66,0.15).draw();},{l:0.9,r:0.9});
def('’',g=>{const d=dotD(g),{C}=g; g.ball(0,C-d/2,d); g.P(d*0.22,C-d*0.68,0.85).c(d*0.3,C-d*1.3,0,C-d*1.9,-d*0.45,C-d*2.25,0).draw();},{l:0.9,r:0.9});
def('-',g=>{const {X}=g; g.P(0,X*0.56,0).l(170,X*0.56,0).draw({b:g.A*0.5,a:g.A*0.5,ne:5});},{l:0.8,r:0.8});
def('–',g=>{const {X}=g; g.P(0,X*0.56,0).l(500,X*0.56,0).draw({b:g.B*1.5,a:g.B*1.5,ne:5});},{l:0.4,r:0.4});
def('—',g=>{const {X}=g; g.P(0,X*0.56,0).l(940,X*0.56,0).draw({b:g.B*1.5,a:g.B*1.5,ne:5});},{l:0.2,r:0.2});
def('/',g=>{const {C}=g; g.P(330,C+60,0.55).l(0,-120,0.55).draw();},{l:0.5,r:0.5});
def('(',g=>paren(g,0,150,770,-250,1),{l:0.9,r:0.6});
def(')',g=>paren(g,150,150,770,-250,-1),{l:0.6,r:0.9});
def('[',g=>brack(g,0,770,-250,1),{l:0.9,r:0.6});
def(']',g=>brack(g,130,770,-250,-1),{l:0.6,r:0.9});
function h2(g){return g.h+4;}

/* =====================================================================
   GREEK. One continuous pen line where the hand would make one; no slab
   serifs on the lowercase, entries and exits are pen pressure.
   ===================================================================== */
def('α',g=>{const {X,yt,yb,h}=g;
  g.P(448,X+8,0.1).c(425,X*0.58,335,yb,215,yb,0.6).c(92,yb,h+2,X*0.24,h+2,X*0.5,1)
   .c(h+2,X*0.78,100,yt,212,yt,0.6).c(318,yt,392,X*0.42,478,4,0.05).draw();},{l:0.8,r:0.5});
def('β',g=>{const {X,AS,D,B,o,h}=g, x0=0, yt2=AS+o-B/2, yb=-o+B/2;
  g.P(x0,D,0.7).l(x0,D+50,1).l(x0,AS*0.66,1).c(x0,AS-12,95,yt2,190,yt2,0.5).c(290,yt2,345,AS*0.9,345,AS*0.79,1)
   .c(345,X*1.18,268,X+16,165,X+16,0).c(335,X+16,412,X*0.78,412,X*0.42,1)
   .c(412,X*0.1,322,yb,215,yb,0.5).c(118,yb,x0+30,X*0.08,x0+h*0.3,X*0.22,0).draw();},{r:0.8});
def('γ',g=>{const {X,D,B}=g;
  g.P(0,X*0.72,0.15).c(10,X+4,92,X+6,128,X*0.76,0.9).l(232,-30,1).c(262,-95,262,D+70,226,D+70,0.45)
   .c(190,D+70,190,-95,226,-30,0.15).draw();
  g.P(450,X-B/2,0).l(232,-30,0).draw();},{l:0.6,r:0.5});
def('δ',g=>{const {X,AS,B,o,h,bd}=g, cx=225, cy=X*0.46, rx=225-h, ry=X*0.46+o-B/2, yt2=AS+o-B/2;
  g.ring(cx,cy,rx,ry);
  const e=g.pt(cx,cy,rx,ry,0.36*PI);
  g.P(372,AS-bd*0.45-10,0.2).c(366,AS+2,300,yt2,232,yt2,0.45).c(150,yt2,108,AS*0.94,108,AS*0.86,0.8)
   .c(108,AS*0.72,e[0]-40,X*1.04,e[0],e[1],1).draw();
  g.ball(372,AS-bd*0.45-10,bd*0.9);},{l:0.82,r:0.8});
def('ε',g=>{const {X,yt,yb,h,bd}=g;
  g.P(352,X*0.79,0.2).c(345,X*0.97,282,yt,218,yt,0.4).c(122,yt,h+28,X*0.9,h+28,X*0.76,1).c(h+28,X*0.6,128,X*0.53,232,X*0.53,0).draw();
  g.P(232,X*0.53,0).c(108,X*0.53,h,X*0.42,h,X*0.25,1).c(h,X*0.06,108,yb,218,yb,0.5).c(318,yb,366,X*0.06,385,X*0.17,0).draw();
  g.ball(352,X*0.79,bd*0.85);},{l:0.82,r:0.7});
def('θ',g=>{const {AS,o,B,h}=g, cy=AS/2-o; g.ring(215,cy,215-h,AS/2+o-B/2,1,2.0); g.bar(h*0.6,430-h*0.6,cy);},{l:0.82,r:0.82});
def('λ',g=>{const {X,AS,B}=g, yb=-g.o+B/2;
  g.P(12,AS-38,0.1).c(38,AS+4,95,AS,122,AS-72,0.9).l(390,62,1).c(400,22,422,yb,452,yb,0.3).draw();
  g.P(290,X*0.62,0).l(12,B/2,0.25).draw();},{l:0.6,r:0.55});
def('μ',g=>{const {X,D,B,yb,h}=g, x0=0, x1=330;
  g.P(x0,X-B/2,0.5).l(x0,X-60,1).l(x0,D+40,1).l(x0,D+B/2,0.7).draw();
  g.P(x0+h*0.3,X*0.34,0).c(x0+28,X*0.06,100,yb,165,yb,0.55).c(250,yb,x1-30,X*0.12,x1-h*0.3,X*0.38,0).draw();
  g.P(x1,X-B/2,0.5).l(x1,X-60,1).l(x1,70,1).c(x1,22,x1+22,yb,x1+60,yb,0.3).c(x1+80,yb,x1+93,18,x1+96,42,0).draw();},{r:0.55});
def('π',g=>{const {X,A,B,o}=g, yb=-o+B/2, bb=A*0.36, yb2=X-bb/2;
  g.P(-12,X*0.76,0.4).c(0,X*0.92,40,yb2,110,yb2,0.6).l(540,yb2,0.3).draw({b:bb});
  g.P(165,X-bb,0.8).c(165,X*0.45,138,X*0.18,72,26,0.35).draw();
  g.P(398,X-bb,1).l(398,78,1).c(398,25,418,yb,452,yb,0.3).c(478,yb,492,20,495,46,0).draw();},{l:0.5,r:0.5});
def('ρ',g=>{const {X,D,o,B,h}=g, cx=225, rx=225-h, cy=X/2, ry=X/2+o-B/2;
  g.ring(cx,cy,rx,ry); g.P(h,X*0.48,1).l(h,D+40,1).l(h,D+B/2,0.7).draw();},{l:0.8,r:0.82});
def('σ',g=>{const {X,o,B,h}=g, cx=212, cy=X*0.47, rx=212-h, ry=X*0.47+o-B/2, bb=B*2.1;
  g.ring(cx,cy,rx,ry); g.P(cx,cy+ry+B/2-bb/2,0).l(470,cy+ry+B/2-bb/2,0).draw({b:bb,a:bb,ne:3});},{l:0.82,r:0.5});
def('φ',g=>{const {X,AS,D,o,B}=g, cx=245;
  g.ring(cx,X/2,245-g.h,X/2+o-B/2,1,2.1);
  g.P(cx,D,0.7).l(cx,D+45,1).l(cx,AS-80,1).l(cx,AS-30,0.7).draw();},{l:0.82,r:0.82});
def('ψ',g=>{const {X,AS,D,B}=g, cx=250;
  g.P(cx,D,0.7).l(cx,D+45,1).l(cx,AS-80,1).l(cx,AS-30,0.7).draw();
  g.P(18,X,0.3).l(18,X-50,1).l(18,X*0.55,1).c(18,X*0.12,110,40,cx,40,0.4).c(390,40,482,X*0.12,482,X*0.55,1).l(482,X-50,1).l(482,X,0.3).draw();},{l:0.6,r:0.6});
def('ω',g=>{const {X,yb,h}=g, W=600;
  g.P(118,X+4,0.15).c(48,X*0.82,h,X*0.6,h,X*0.36,1).c(h,X*0.08,92,yb,165,yb,0.5).c(238,yb,282,X*0.15,300,X*0.52,0.15)
   .c(318,X*0.15,362,yb,435,yb,0.5).c(508,yb,W-h,X*0.08,W-h,X*0.36,1).c(W-h,X*0.6,W-48,X*0.82,W-118,X+4,0.15).draw();},{l:0.75,r:0.75});
def('Γ',g=>{const {C,B,h}=g; g.stem(0,0,C); g.serif(0,C,-1,'l'); g.serif(0,0,1,'b'); g.bar(-h,395,C-B/2); vbeak(g,395-g.S*0.7,C,C-128);},{r:0.5});
def('Δ',g=>{const {C,A,B,o}=g, xl=0, xm=290, xr=580;
  g.P(xl+20,B,0).l(xm-A*0.15,C+o-B/2,0).draw(); g.P(xm-A*0.25,C+o-B/2,0.9).l(xr-A*0.35,B,1).draw(); g.bar(xl,xr,B/2);},{l:0.45,r:0.45});
def('Σ',g=>{const {C,A,B,S}=g, W=480;
  g.bar(0,W,C-B/2); vbeak(g,W-S*0.7,C,C-130); g.P(30,C-B,1).l(255,C*0.5,1).draw(); g.P(255,C*0.5,0).l(25,B,0).draw();
  g.bar(0,W+20,B/2); vbeak(g,W+20-S*0.7,0,140);},{l:0.6,r:0.6});
def('Ω',g=>{const {C,B,A,o}=g, cx=330, cy=C*0.56, rx=330-g.h-30, ry=C*0.44+o-B/2, t0=1.37*PI, t1=-0.37*PI;
  const s=g.pt(cx,cy,rx,ry,t0), e=g.pt(cx,cy,rx,ry,t1);
  g.P(s[0]+40,B,0.5).c(s[0]+15,s[1]*0.5,s[0],s[1],s[0],s[1],0.7).arc(cx,cy,rx,ry,t0,PI,1).arc(cx,cy,rx,ry,PI,0.5*PI,0.6)
   .arc(cx,cy,rx,ry,0.5*PI,0,1).arc(cx,cy,rx,ry,0,t1,0.7).c(e[0],e[1],e[0]-15,e[1]*0.5,e[0]-40,B,0.5).draw();
  g.bar(s[0]-130,s[0]+60,B/2); g.bar(e[0]-60,e[0]+130,B/2);},{l:0.6,r:0.6});

/* =====================================================================
   MATHS. Operators use the rule pen: a square nib, R thick.
   The math axis is at 250; big operators are centred on it.
   ===================================================================== */
function R(g){return Math.max(g.B*1.35,g.A*0.44);}
function rule(g,x0,y0,x1,y1,ne){const r=R(g);g.P(x0,y0,0).l(x1,y1,0).draw({a:r,b:r,ne:ne||8,role:'rule'});}
const AX=250, OPW={l:1.4,r:1.4,upright:true};
def('+',g=>{rule(g,0,AX,560,AX); rule(g,280,AX-280,280,AX+280);},OPW);
def('−',g=>{rule(g,0,AX,560,AX);},OPW);
def('=',g=>{rule(g,0,AX+108,560,AX+108); rule(g,0,AX-108,560,AX-108);},OPW);
def('×',g=>{const d=200; rule(g,280-d,AX-d,280+d,AX+d,3); rule(g,280-d,AX+d,280+d,AX-d,3);},OPW);
def('<',g=>{const r=R(g); g.P(500,AX+250,0).l(0,AX,0).l(500,AX-250,0).draw({a:r,b:r,ne:2.6,role:'rule'});},OPW);
def('>',g=>{const r=R(g); g.P(0,AX+250,0).l(500,AX,0).l(0,AX-250,0).draw({a:r,b:r,ne:2.6,role:'rule'});},OPW);
def('·',g=>{g.dot(0,AX,g.A*0.95);},{l:1.2,r:1.2,upright:true});
def('∑',g=>{const {A,B,S}=g, top=AX+520, bot=AX-520, W=820;
  g.bar(0,W,top-B/2); vbeak(g,W-S*0.7,top,top-160); g.P(40,top-B,1).l(430,AX,1).draw(); g.P(430,AX,0).l(30,bot+B,0).draw();
  g.bar(0,W+30,bot+B/2); vbeak(g,W+30-S*0.7,bot,bot+170);},{l:0.6,r:0.6,bigop:true,upright:true});
def('∫',g=>{const {bd,A}=g, d=Math.max(bd,A*0.9)*0.92;
  g.P(352,AX+600,0.25).c(352,AX+655,315,AX+680,280,AX+680,0.35).c(232,AX+680,212,AX+630,205,AX+520,1)
   .l(150,AX-520,1).c(143,AX-630,123,AX-680,75,AX-680,0.35).c(40,AX-680,3,AX-655,3,AX-600,0.25).draw();
  g.ball(352,AX+600,d); g.ball(3,AX-600,d);},{l:0.6,r:0.6,bigop:true,slant:0.2,yc:AX});
def('∞',g=>{const a=360, b=150, cx=a, cy=AX; const p=g.P(cx,cy,1);
  for(let i=1;i<=200;i++){const t=i/200*TAU; p.l(cx+a*0.9*Math.sin(t)/(1+0.18*Math.cos(2*t)), cy+b*Math.sin(2*t)/(1+0.18*Math.cos(2*t))*1.05,1);}
  p.draw();},{l:0.8,r:0.8});
def('∂',g=>{const {yb,bd,X,B,o}=g, yt=700+o-B/2;
  g.P(112,600,0.2).c(112,672,180,yt,252,yt,0.5).c(352,yt,392,600,392,420,1).l(392,260,1)
   .c(392,80,305,yb,212,yb,0.6).c(112,yb,62,90,62,195,1).c(62,312,145,382,236,382,0.5).c(305,382,362,345,392,288,0.1).draw();
  g.ball(112,600,bd*0.9);},{l:0.8,r:0.8});
def('∇',g=>{const {C,A,B}=g, W=600; g.bar(0,W,C-B/2); g.P(30,C-B,1).l(W/2-A*0.1,-g.o+B/2,0.9).draw(); g.P(W/2+A*0.2,-g.o+B/2,0).l(W-25,C-B,0).draw();},{l:0.5,r:0.5,upright:true});
def('√',g=>radical(g,770,-240,40),{l:0.5,r:0.2,upright:true});
def('′',g=>{g.P(150,720,1).l(40,440,0.1).draw();},{l:0.4,r:0.4});
function radical(g,top,bot,bar){const {A,B}=g, r=R(g), mid=bot+(top-bot)*0.42, H=top-bot;
  const xb=165+H*0.05, xt=xb+H*0.26;
  g.P(0,mid-12,0).l(62,mid+30,0.2).draw({a:r*0.9,b:r*0.9,ne:3});
  g.P(62,mid+30,0.9).l(xb,bot+B/2,1).draw();
  g.P(xb,bot+B/2,0).l(xt,top-r/2,0).draw();
  rule(g,xt,top-r/2,xt+bar,top-r/2);
  return xt;}

/* =====================================================================
   ITALIC. A true cursive: entry hooks, exit tails, single-storey a and g,
   a descending f, round-bottomed v and w. Drawn upright; the engine slants
   the centre-lines but not the pen, so the stress stays vertical.
   ===================================================================== */
function entry(g,x,top){const {B}=g; return g.P(x-72,top-88,0).c(x-50,top-36,x-26,top-B/2,x-6,top-B/2,0.4).c(x,top-B/2,x,top-34,x,top-64,1);}
function exitT(p,g,x){const {yb}=g; return p.l(x,112,1).c(x,34,x+22,yb,x+62,yb,0.4).c(x+96,yb,x+118,30,x+130,76,0);}
function iarch(g,x0,x1,top){const {B,h}=g, yt=top+g.o-B/2, xm=(x0+x1)/2+20;
  return g.P(x0+h*0.3,top*0.46,0).c(x0+30,top*0.84,xm-(xm-x0)*0.6,yt,xm,yt,0.5).c(xm+(x1-xm)*0.65,yt,x1,top*0.86,x1,top*0.6,1);}
function ibowl(g,xr){const {X,yt,yb,h}=g; // the a, d, g, q bowl: open at the right, joins the stem
  g.P(xr-h*0.2,X*0.8,0.1).c(xr-30,X+4,xr-80,yt,xr-122,yt,0.4).c(xr-232,yt,h,X*0.64,h,X*0.36,1)
   .c(h,X*0.1,62,yb,128,yb,0.5).c(200,yb,xr-30,X*0.25,xr-h*0.25,X*0.47,0).draw();}
idef('i',g=>{const {X,AS}=g; exitT(entry(g,0,X),g,0).draw(); g.dot(18,X+(AS-X)*0.66,dotD(g));},{l:0.7,r:0.5});
idef('l',g=>{const {AS}=g; exitT(entry(g,0,AS),g,0).draw();},{l:0.7,r:0.5});
idef('j',g=>{const {X,AS,D,B,bd,o}=g, yb=D-o+B/2;
  entry(g,0,X).l(0,D+150,1).c(0,D+50,-40,yb,-105,yb,0.5).c(-150,yb,-182,D+22,-190,D+bd*0.5+8,0.25).draw();
  g.ball(-190,D+bd*0.5+8); g.dot(18,X+(AS-X)*0.66,dotD(g));},{l:0.5,r:0.6});
idef('n',g=>{const {X,B}=g; entry(g,0,X).l(0,B/2,1).draw(); exitT(iarch(g,0,300,X),g,300).draw();},{l:0.7,r:0.5});
idef('m',g=>{const {X,B}=g; entry(g,0,X).l(0,B/2,1).draw(); iarch(g,0,270,X).l(270,B/2,1).draw(); exitT(iarch(g,270,540,X),g,540).draw();},{l:0.7,r:0.5});
idef('h',g=>{const {X,AS,B}=g; entry(g,0,AS).l(0,B/2,1).draw(); exitT(iarch(g,0,300,X),g,300).draw();},{l:0.7,r:0.5});
idef('u',g=>{const {X,B,yb,h}=g, x1=300;
  entry(g,0,X).l(0,X*0.34,1).c(0,X*0.08,60,yb,128,yb,0.5).c(200,yb,x1-28,X*0.22,x1-h*0.25,X*0.48,0).draw();
  exitT(g.P(x1,X,0.5).l(x1,X-44,1),g,x1).draw();},{l:0.7,r:0.5});
idef('a',g=>{const {X}=g, x1=300; ibowl(g,x1); exitT(g.P(x1,X,0.5).l(x1,X-44,1),g,x1).draw();},{l:0.8,r:0.5});
idef('d',g=>{const {AS}=g, x1=300; ibowl(g,x1); exitT(g.P(x1,AS,0.5).l(x1,AS-44,1),g,x1).draw();},{l:0.8,r:0.5});
idef('q',g=>{const {X,D}=g, x1=300; ibowl(g,x1); g.P(x1,X,0.5).l(x1,X-44,1).l(x1,D+g.B/2,1).draw(); g.serif(x1,D,1,'b');},{l:0.8,r:0.6});
idef('g',g=>{const {X,D,B,bd,o}=g, x1=300, yb=D-o+B/2; ibowl(g,x1);
  g.P(x1,X,0.5).l(x1,X-44,1).l(x1,D+160,1).c(x1,D+55,x1-48,yb,x1-130,yb,0.5).c(x1-205,yb,x1-245,D+40,x1-250,D+bd*0.5+10,0.25).draw();
  g.ball(x1-250,D+bd*0.5+10);},{l:0.8,r:0.6});
idef('e',g=>{const {X,yt,yb,h}=g;
  g.P(h*0.5,X*0.36,0).c(110,X*0.4,268,X*0.52,268,X*0.77,0.35).c(268,X*0.95,218,yt,160,yt,0.4)
   .c(62,yt,h,X*0.62,h,X*0.36,1).c(h,X*0.1,80,yb,150,yb,0.5).c(212,yb,252,30,278,82,0).draw();},{l:0.8,r:0.5});
idef('c',g=>{const {X,yt,yb,h,bd}=g;
  g.P(258,X*0.74,0.2).c(255,X*0.95,212,yt,165,yt,0.4).c(62,yt,h,X*0.62,h,X*0.36,1).c(h,X*0.1,80,yb,150,yb,0.5).c(212,yb,252,30,278,82,0).draw();
  g.ball(258,X*0.74,bd*0.8);},{l:0.8,r:0.5});
idef('o',g=>{const {X,yt,yb,h}=g, cx=200, rx=200-h;
  g.ring(cx,X/2,rx,X/2+g.o-g.B/2);},{l:0.8,r:0.8});
function itF(g,x,xd){const {X,AS,D,B,bd,o,A}=g, yt2=AS+o-B/2, yb=D-o+B/2, ye=AS-Math.max(bd,A*0.6)*0.5-12;
  g.P(xd,ye,0.25).c(xd,AS-4,x+(xd-x)*0.7,yt2,x+70,yt2,0.4).c(x+20,yt2,x,AS-60,x,AS-160,1).l(x,D+150,1)
   .c(x,D+55,x-35,yb,x-90,yb,0.4).c(x-140,yb,x-170,D+40,x-172,D+bd*0.45+12,0.25).draw();
  g.ball(xd,ye); g.ball(x-172,D+bd*0.45+12,bd*0.85);}
idef('f',g=>{const {X,B}=g, x=190; itF(g,x,x+150); g.bar(x-130,x+125,X-B/2);},{l:0.3,r:0.2});
idef('ﬁ',g=>{const {X,B}=g, x=190, xi=x+250; itF(g,x,xi+12); exitT(entry(g,xi,X),g,xi).draw(); g.bar(x-130,xi-40,X-B/2);},{l:0.3,r:0.5});
idef('ﬂ',g=>{const {X,AS,B}=g, x=190, xl=x+262; itF(g,x,x+150); exitT(entry(g,xl,AS),g,xl).draw(); g.bar(x-130,xl-30,X-B/2);},{l:0.3,r:0.5});
idef('ﬀ',g=>{const {X,B}=g, x=190, x2=x+215; itF(g,x,x+128); itF(g,x2,x2+150); g.bar(x-130,x2+125,X-B/2);},{l:0.3,r:0.2});
/* italic capitals: their own forms (curled feet, entry hooks, drops), not slanted roman */
function iFoot(g,x,y1){const {B,o}=g, yb=-o+B/2; return g.P(x-62,52,0).c(x-50,10,x-22,yb,x+4,20,0.05);}
function iExit(p,g,x){const {B,o}=g, yb=-o+B/2; return p.l(x,78,1).c(x,24,x+20,yb,x+56,yb,0.35).c(x+84,yb,x+100,18,x+104,44,0);}
idef('A',g=>{const {C,B,o,A}=g;
  iFoot(g,0).l(300,C+o-B/2,0).draw();
  iExit(g.P(300-A*0.2,C+o-B/2,0.85).l(408,120,1),g,412).draw(); g.bar(105,400,C*0.31);},{l:0.45,r:0.4});
idef('V',g=>{const {C,B,A,bd}=g;
  g.P(-58,C-82,0).c(-44,C-20,-4,C-B/2,26,C-B/2,0.4).c(52,C-B/2,60,C-40,62,C-82,1).l(255,24,1).draw();
  g.P(255+A*0.1,24,0).l(452,C-130,0.05).c(462,C-70,474,C-34,500,C-24,0.3).draw(); g.ball(506,C-28,bd*0.8);},{l:0.45,r:0.45});
idef('W',g=>{const {C,B,A,bd}=g;
  g.P(-58,C-82,0).c(-44,C-20,-4,C-B/2,26,C-B/2,0.4).c(52,C-B/2,60,C-40,62,C-82,1).l(220,24,1).draw();
  g.P(220+A*0.1,24,0).l(390,C-B/2,0).draw(); g.P(390,C-B/2,0.8).l(560,24,1).draw();
  g.P(560+A*0.1,24,0).l(732,C-130,0.05).c(742,C-70,754,C-34,780,C-24,0.3).draw(); g.ball(786,C-28,bd*0.8);},{l:0.45,r:0.45});
idef('M',g=>{const {C,B,A}=g;
  iFoot(g,10).l(70,C-B/2,0).draw(); g.P(70,C-B/2,1).l(320,12,0.95).draw(); g.P(320+A*0.1,12,0).l(600,C-B/2,0).draw();
  iExit(g.P(600,C-B/2,1),g,600).draw(); g.serif(600,C,-1,'r',A,g.sl*0.6);},{l:0.5,r:0.4});
idef('N',g=>{const {C,B,A,bd}=g;
  iFoot(g,10).l(40,C-B/2,0).draw(); g.P(40,C-B/2,1).l(470,12,1).draw();
  g.P(470,12,0).l(476,C-110,0).c(478,C-50,500,C-B/2,532,C-B/2,0.25).draw(); g.ball(540,C-34,bd*0.75);},{l:0.45,r:0.45});
idef('O',g=>{const {C,o,B,h}=g; g.ring(290,C/2,290-h,C/2+o-B/2,1,2.0);},{l:0.8,r:0.8});
function roundCi(g,cx,t1,endPr){const {C,o,B,h,bd}=g, rx=cx-h, cy=C/2, ry=C/2+o-B/2, t0=0.2*PI, s=g.pt(cx,cy,rx,ry,t0,2.0);
  g.E(cx,cy,rx,ry,t0,0.25,2.0).arc(cx,cy,rx,ry,t0,0.5*PI,0.6,2.0).arc(cx,cy,rx,ry,0.5*PI,PI,1,2.0).arc(cx,cy,rx,ry,PI,1.5*PI,0.6,2.0).arc(cx,cy,rx,ry,1.5*PI,t1,endPr,2.0).draw();
  g.ball(s[0],s[1]); return [cx,rx];}
idef('C',g=>{roundCi(g,280,1.84*PI,0);},{l:0.8,r:0.55});
idef('G',g=>{const {C,B}=g; const [cx,rx]=roundCi(g,285,1.9*PI,0.15); const xr=cx+rx*0.99;
  iExit(g.P(xr,C*0.42,0.5).l(xr,C*0.38,1),g,xr).draw();},{l:0.8,r:0.5});
idef('Q',g=>{const {C,o,B,h}=g; g.ring(290,C/2,290-h,C/2+o-B/2,1,2.0);
  g.P(200,-4,0.2).c(250,-70,360,-112,470,-100,0.75).c(530,-94,566,-74,596,-52,0).draw();},{l:0.8,r:0.45});
idef('r',g=>{const {X,B,yt,bd,h}=g, ye=X-bd*0.45-6;
  entry(g,0,X).l(0,B/2,1).draw();
  g.P(h*0.3,X*0.48,0).c(32,X*0.84,110,yt,170,yt,0.4).c(212,yt,236,X*0.95,236,ye,0.2).draw(); g.ball(232,ye,bd*0.9);},{l:0.7,r:0.4});
idef('t',g=>{const {X,B}=g; exitT(g.P(0,X+112,0.45).l(0,X*0.8,1),g,0).draw(); g.bar(-g.h-62,g.h+110,X-B/2);},{l:0.7,r:0.4});
idef('v',g=>{const {X,yb,bd}=g, x1=310;
  entry(g,0,X).l(0,X*0.4,1).c(0,X*0.1,60,yb,140,yb,0.5).c(232,yb,x1,X*0.32,x1,X*0.62,0.35).c(x1,X*0.8,x1-14,X*0.86,x1-38,X*0.9,0.2).draw();
  g.ball(x1-36,X*0.86,bd*0.8);},{l:0.7,r:0.5});
idef('w',g=>{const {X,yb,bd,B}=g, m=250, x1=520;
  entry(g,0,X).l(0,X*0.4,1).c(0,X*0.1,52,yb,118,yb,0.5).c(190,yb,m-16,X*0.22,m-g.h*0.25,X*0.5,0).draw();
  g.P(m,X,0.5).l(m,X-44,1).l(m,X*0.4,1).c(m,X*0.1,m+52,yb,m+120,yb,0.5).c(m+212,yb,x1,X*0.32,x1,X*0.62,0.35).c(x1,X*0.8,x1-14,X*0.86,x1-38,X*0.9,0.2).draw();
  g.ball(x1-36,X*0.86,bd*0.8);},{l:0.7,r:0.5});
idef('y',g=>{const {X,D,B,yb,bd,o,h}=g, x1=300, yd=D-o+B/2;
  entry(g,0,X).l(0,X*0.34,1).c(0,X*0.08,60,yb,128,yb,0.5).c(200,yb,x1-28,X*0.22,x1-h*0.25,X*0.48,0).draw();
  g.P(x1,X,0.5).l(x1,X-44,1).l(x1,D+160,1).c(x1,D+55,x1-48,yd,x1-130,yd,0.5).c(x1-205,yd,x1-245,D+40,x1-250,D+bd*0.5+10,0.25).draw();
  g.ball(x1-250,D+bd*0.5+10);},{l:0.7,r:0.6});
idef('p',g=>{const {X,D}=g; entry(g,0,X).l(0,D+g.B/2,1).draw(); g.serif(0,D,1,'b');
  iarch(g,0,330,X).l(330,X*0.4,1).c(330,X*0.1,270,g.yb,190,g.yb,0.5).c(120,g.yb,40,X*0.08,g.h*0.3,X*0.25,0).draw();},{l:0.7,r:0.8});
idef('b',g=>{const {X,AS}=g; entry(g,0,AS).l(0,X*0.3,1).c(0,X*0.08,80,g.yb,165,g.yb,0.5).c(270,g.yb,330,X*0.2,330,X*0.5,1)
  .c(330,X*0.82,280,g.yt,215,g.yt,0.5).c(140,g.yt,60,X*0.78,g.h*0.3,X*0.5,0).draw();},{l:0.7,r:0.8});
idef('k',g=>{const {X,AS,B,h}=g; entry(g,0,AS).l(0,B/2,1).draw();
  g.P(h*0.3,X*0.32,0).c(80,X*0.6,170,X+6,235,X*0.86,0.4).c(270,X*0.74,200,X*0.56,90,X*0.5,0.6).draw();
  exitT(g.P(120,X*0.52,0.5).c(190,X*0.45,220,X*0.3,220,X*0.2,1),g,220).draw();},{l:0.7,r:0.5});
idef('s',g=>{const {X,B,yt,yb,h,bd}=g, W=290;
  g.P(W-20,X*0.78,0.2).c(W-28,X*0.95,W*0.68,yt,W*0.5,yt,0.5).c(W*0.24,yt,h+2,X*0.92,h+2,X*0.74,1)
   .c(h+2,X*0.5,W-h-2,X*0.52,W-h-2,X*0.27,1).c(W-h-2,X*0.08,W*0.76,yb,W*0.5,yb,0.5).c(W*0.27,yb,22,X*0.06,8,X*0.2,0.2).draw();
  g.ball(W-22,X*0.78,bd*0.75); g.ball(10,X*0.22,bd*0.75);},{l:0.8,r:0.8});
idef('x',g=>{const {X,B,yb,yt}=g;
  g.P(-40,X*0.78,0.2).c(-20,X+4,60,yt,100,X*0.7,0.9).l(200,X*0.3,1).c(240,yb+10,300,yb,330,X*0.22,0).draw();
  g.P(-10,X*0.2,0).c(20,yb,90,yb,120,X*0.3,0.3).l(240,X*0.72,0).c(260,yt,320,X+4,330,X*0.82,0).draw();},{l:0.6,r:0.6});
idef('z',g=>{const {X,A,B}=g; g.P(30,X*0.82,0.1).c(70,X+4,150,X-B*2,330,X-B/2,0).draw(); g.P(330-A*0.4,X-B,0.9).l(30,B,0.9).draw();
  g.P(30,B/2,0).c(150,B*3,250,-B,340,B*2,0.1).draw();},{l:0.7,r:0.7});

/* =====================================================================
   SWEEP: centre-lines + nib -> polygons
   ===================================================================== */
function nibFor(p,o,pr){
  const b=o.b!=null?o.b:p.B, a=o.a!=null?o.a:(b+(p.A-b)*clamp(pr,0,1));
  const ang=o.role==='rule'?0:p.ang+(o.turn||0);
  return nib(a,b,ang,o.ne||3.2);
}
function circle(x,y,r){const v=[];for(let i=0;i<40;i++){const t=i/40*TAU;v.push([x+r*Math.cos(t),y+r*Math.sin(t)]);}return v;}
function teardrop(g,x,y,r){ // find the stroke end this terminal belongs to; grow a drop out of it
  let best=null,bd=r*3.2;
  for(const s of g.strokes){const P=s.pts;for(const end of [0,P.length-1]){const q=P[end],d=Math.hypot(q[0]-x,q[1]-y);if(d<bd){bd=d;best={P,end};}}}
  if(!best) return {pts:circle(x,y,r),round:true};
  const {P,end}=best, dir=end===0?1:-1; let acc=0,i=end,tip=P[end];
  while(i+dir>=0&&i+dir<P.length&&acc<r*2.1){const a=P[i],b=P[i+dir];acc+=Math.hypot(b[0]-a[0],b[1]-a[1]);i+=dir;tip=P[i];}
  const ux=x-tip[0],uy=y-tip[1],ul=Math.hypot(ux,uy)||1, cx=x+ux/ul*r*0.12, cy=y+uy/ul*r*0.12;
  const pts=circle(cx,cy,r).concat([[tip[0],tip[1]],[tip[0]+(cx-tip[0])*0.35,tip[1]+(cy-tip[1])*0.35]]);
  return {pts:hull(pts),round:false};
}
function compose(def_,p,extra,mods){
  mods=mods||{}; let wdx=mods.wdx||1;
  if(def_.cap&&!mods.sc){p=Object.assign({},p,{A:p.A*0.92});wdx*=0.955;}
  if(mods.p) p=Object.assign({},p,mods.p);
  const g=builder(p); const ret=def_.fn(g,extra);
  const dy=mods.dy||0, wd=p.wd*wdx, sl=def_.slant!=null?def_.slant:(def_.upright?0:p.slant), yc=def_.yc!=null?def_.yc:p.xh*0.45, T=(x,y)=>[x*wd+(y+dy-yc)*sl,y+dy];
  const polys=[], strokes=[]; let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  const bb=(ux,uy)=>{if(ux<x0)x0=ux;if(ux>x1)x1=ux;if(uy<y0)y0=uy;if(uy>y1)y1=uy;};
  for(const s of g.strokes){
    let prev=null; const out=[];
    for(let i=0;i<s.pts.length;i++){const [x,y,pr]=s.pts[i];
      const nb=nibFor(p,s.o,pr), q=T(x,y);
      for(const v of nb) bb(x*wd+v[0],y+dy+v[1]);
      const cur=nb.map(v=>[q[0]+v[0],q[1]+v[1]]);
      if(prev) polys.push(hull(prev.concat(cur))); else if(s.pts.length===1) polys.push(cur);
      prev=cur; out.push([q[0],q[1],pr,nb]);
    }
    strokes.push({pts:out,nodes:s.nodes.map(n=>T(n[0],n[1])),role:s.o.role||'stroke'});
  }
  const balls=[];
  for(const [x,y,r] of g.balls){const q=T(x,y);polys.push(circle(q[0],q[1],r));balls.push([q[0],q[1],r]);bb(x*wd-r,y+dy-r);bb(x*wd+r,y+dy+r);}
  for(const [x,y,r] of g.drops){const t=teardrop(g,x,y,r);g.fills.push({pts:t.pts,role:t.round?'ball':'drop'});}
  const fills=[];
  for(const f of g.fills){const pts=ccw(f.pts.map(([x,y])=>{bb(x*wd,y+dy);return T(x,y);}));polys.push(pts);fills.push({pts,role:f.role});}
  if(x0>x1){x0=0;x1=0;y0=0;y1=0;}
  let adv,dx;
  if(def_.adv!=null&&!mods.prop){adv=def_.adv*wd;dx=def_.empty?0:(adv-(x1-x0))/2-x0;}
  else{const L=p.sb*(def_.l==null?1:def_.l)+(mods.extra||0), Rr=p.sb*(def_.r==null?1:def_.r)+(mods.extra||0);adv=x1-x0+L+Rr;dx=L-x0;}
  let path=null;
  if(typeof Path2D!=='undefined'){path=new Path2D();for(const poly of polys){path.moveTo(poly[0][0],poly[0][1]);for(let i=1;i<poly.length;i++)path.lineTo(poly[i][0],poly[i][1]);path.closePath();}}
  return {path,polys,strokes,balls,fills,adv,dx,xmin:x0,xmax:x1,ymin:y0,ymax:y1,ret,nPolys:polys.length};
}
const cache=new Map();
const OSF={'0':'x','1':'x','2':'x','3':'d','4':'d','5':'d','7':'d','9':'d','6':'a','8':'a'};
function glyph(ch,p){
  const key=ch+'|'+p.key+'|'+(p.ital?1:0);
  let gd=cache.get(key); if(gd) return gd;
  let base=ch, mods={};
  if(ch.length>3&&ch.endsWith('.os')){ // old-style figure: the lining drawing on a shorter or shifted frame
    base=ch[0]; const k=OSF[base], X=p.xh; mods={p:{cap:k==='x'?X*1.02:X*1.42},dy:k==='d'?-X*0.42:0,prop:true,wdx:0.97};}
  else if(ch.startsWith('sc:')){ // small cap: the capital drawn at x-height, narrower, with heavier hairlines
    base=ch.slice(3); mods={sc:true,p:{cap:p.xh*1.1,A:p.A*0.94,B:p.B*1.3,S:p.S*1.2,sl:p.sl*0.8},wdx:0.83,extra:p.sb*0.15};}
  const d=(p.ital&&GI[base])||G[base]; if(!d) return null;
  gd=compose(d,p,undefined,mods); gd.ch=ch; gd.cursive=!!(p.ital&&GI[base]);
  if(/[\u03b1-\u03c9]/.test(base)){gd.adv+=p.sb*0.5;gd.dx+=p.sb*0.25;}
  if(cache.size>2500) cache.clear();
  cache.set(key,gd); return gd;
}
function paint(ctx,gd,x,y,s){if(!gd||!gd.path)return;ctx.save();ctx.translate(x+gd.dx*s,y);ctx.scale(s,-s);ctx.fill(gd.path);ctx.restore();}
/* kerning: pairs in font units at 1000/em (roman; italic uses 70 %) */
const KERN={};
(function(){const add=(L,R,v)=>{for(const a of L)for(const b of R)KERN[a+b]=v;};
  add('T','aceosru',-62); add('T','yvw',-45); add('T','AΔ',-55); add('T','.,',-70); add('T','J',-40);
  add('A','TVWY',-58); add('A','vwy',-34); add('A','\'’',-60); add('AΔ','CGOQ',-18);
  add('VW','aeo',-46); add('VW','.,',-70); add('VW','A',-55); add('Y','aeo',-64); add('Y','.,',-80); add('Y','A',-60);
  add('L','TVWY',-70); add('L','\'’',-80); add('L','y',-30); add('P','.,',-80); add('P','A',-40); add('F','.,',-60); add('F','a',-20);
  add('r','.,',-50); add('vwy','.,',-40); add('f','\'’)?!]',30); add('\'’','s',-25); add('\'’','A',-55);
  add('k','eo',-12); add('o','vwxy',-10); add('vwy','o',-10); add('c','k',0); add('R','TVWY',-24);})();
function shape(text,o){ // -> glyph names: ligatures, old-style figures, small caps
  let t=text;
  if(o.liga!==false) t=t.replace(/ff/g,'ﬀ').replace(/fi/g,'ﬁ').replace(/fl/g,'ﬂ');
  const out=[];
  for(const ch of t){
    if(o.smcp&&/[a-z]/.test(ch)) out.push('sc:'+ch.toUpperCase());
    else if(o.c2sc&&/[A-Z]/.test(ch)) out.push('sc:'+ch);
    else if(o.onum!==false&&/[0-9]/.test(ch)) out.push(ch+'.os');
    else out.push(ch);}
  return out;
}
function drawText(ctx,text,x,y,size,p,o){ // returns width; o: measure, track (units), liga, onum, smcp, c2sc, kern
  o=o||{}; const s=size/1000; let pen=x, prev='';
  for(const name of shape(text,o)){
    const k=o.kern===false?0:(KERN[prev.slice(-1)+name[0]]||0)*(p.ital?0.7:1); pen+=k*s;
    const gd=glyph(name,p); prev=name.startsWith('sc:')?'':name.replace('.os','');
    if(!gd){pen+=300*s;continue;} if(!o.measure) paint(ctx,gd,pen,y,s); pen+=(gd.adv+(o.track||0))*s;}
  return pen-x;
}
function measure(text,size,p,o){return drawText(null,text,0,0,size,p,Object.assign({},o||{},{measure:true}));}

/* =====================================================================
   MATHS SETTER: a tiny TeX subset, enough to show the glyphs in maths.
   \frac \sqrt \sum \int ^ _ ' \left( \right) \mathrm \, \; \quad, Greek by name.
   Scripts are set at 70 % with a slightly smaller optical size: a little sturdier, a little opener.
   ===================================================================== */
const GREEK={rho:'ρ',alpha:'α',beta:'β',gamma:'γ',delta:'δ',epsilon:'ε',varepsilon:'ε',theta:'θ',lambda:'λ',mu:'μ',pi:'π',sigma:'σ',phi:'φ',varphi:'φ',psi:'ψ',omega:'ω',Gamma:'Γ',Delta:'Δ',Sigma:'Σ',Omega:'Ω'};
const SYM={infty:['∞','ord'],partial:['∂','ord',1],nabla:['∇','ord'],cdot:['·','bin'],times:['×','bin'],sum:['∑','op'],int:['∫','op'],prime:['′','ord'],lt:['<','rel'],gt:['>','rel']};
function tokenize(s){const t=[];let i=0;while(i<s.length){const c=s[i];
  if(c==='\\'){let j=i+1;if(/[a-zA-Z]/.test(s[j]||'')){while(j<s.length&&/[a-zA-Z]/.test(s[j]))j++;}else j++;t.push(s.slice(i,j));i=j;}
  else if(/\s/.test(c))i++; else {t.push(c);i++;}}return t;}
const B0=()=>({w:0,h:0,d:0,items:[]});
function hpack(list){let x=0,h=0,d=0;const items=[];for(const b of list){for(const it of b.items)items.push(Object.assign({},it,{x:it.x+x}));x+=b.w;h=Math.max(h,b.h);d=Math.max(d,b.d);}return {w:x,h,d,items};}
function shiftB(b,dx,dy){return {w:b.w,h:b.h+dy,d:b.d-dy,items:b.items.map(it=>Object.assign({},it,{x:it.x+dx,y:it.y+dy}))};}
function overlay(list,w){let h=0,d=0;const items=[];for(const b of list){items.push(...b.items);h=Math.max(h,b.h);d=Math.max(d,b.d);}return {w:w,h,d,items};}
function spaceB(w){return {w,h:0,d:0,items:[]};}
function mctx(base,size,level,display){
  const opsz=Math.max(6,base.opsz*[1,0.8,0.66][level]);
  const o=Object.assign({},base,{opsz});
  return {base,size,level,display,p:params(Object.assign({},o,{ital:false})),pi:params(Object.assign({},o,{ital:true}))};
}
const sub_=c=>mctx(c.base,c.size*(c.level===0?0.7:0.78),Math.min(2,c.level+1),false);
function gbox(ch,c,ital){const p=ital?c.pi:c.p, gd=glyph(ch,p), s=c.size/1000;
  if(!gd) return spaceB(0.3*c.size);
  return {w:gd.adv*s,h:Math.max(gd.ymax,0)*s,d:Math.max(-gd.ymin,0)*s,items:[{t:'g',gd,x:0,y:0,s}],ital:ital&&!gd.cursive?0:0};}
function customBox(fn,c,extra){const p=c.p, s=c.size/1000; const gd=compose({fn,l:0.3,r:0.3},p,extra);
  return {gd,box:{w:gd.adv*s,h:Math.max(gd.ymax,0)*s,d:Math.max(-gd.ymin,0)*s,items:[{t:'g',gd,x:0,y:0,s}]}};}
function ruleU(p){return Math.max(p.B*1.35,p.A*0.44);}
function frac(num,den,c){const S=c.size, s=S/1000, Rp=ruleU(c.p)*s, ax=AX*s, gap=S*0.11;
  const w=Math.max(num.w,den.w)+S*0.16;
  const n=shiftB(num,(w-num.w)/2,ax+Rp/2+gap+num.d), dn=shiftB(den,(w-den.w)/2,ax-Rp/2-gap-den.h);
  const b=overlay([n,dn],w); b.items.push({t:'r',x:S*0.04,y:ax-Rp/2,w:w-S*0.08,h:Rp});
  return hpack([spaceB(S*0.08),b,spaceB(S*0.08)]);}
function sqrtB(inner,c){const S=c.size, s=S/1000, p=c.p;
  const top=Math.max((inner.h+S*0.14)/s+ruleU(p),760), bot=Math.min(-(inner.d+S*0.1)/s,-215);
  const bar=inner.w/s+50; let xt=0;
  const {gd,box}=customBox((g)=>{xt=radical(g,top,bot,bar);return xt;},c);
  const ix=(xt*p.wd+gd.dx+25)*s;
  return overlay([box,shiftB(inner,ix,0)],Math.max(box.w,ix+inner.w+S*0.05));}
function delimB(ch,inner,c){const S=c.size, s=S/1000;
  const ext=Math.max((inner.h+S*0.12)/s-AX,AX-(-(inner.d+S*0.12)/s),520), top=AX+ext, bot=AX-ext, w=150*Math.sqrt((top-bot)/1020);
  const fn=ch==='('?g=>paren(g,0,w,top,bot,1):ch===')'?g=>paren(g,w,w,top,bot,-1):ch==='['?g=>brack(g,0,top,bot,1):g=>brack(g,130,top,bot,-1);
  return customBox(fn,c).box;}
function bigop(ch,c){const S=c.size, b=gbox(ch,c,false); b.op=ch; return b;}
function scripts(a,sup,sub,c){const S=c.size, b=a.box;
  if(a.cls==='op'&&a.op==='∑'&&c.display){const g=S*0.12, w=Math.max(b.w,sup?sup.w:0,sub?sub.w:0), parts=[shiftB(b,(w-b.w)/2,0)];
    if(sup) parts.push(shiftB(sup,(w-sup.w)/2,b.h+g+sup.d)); if(sub) parts.push(shiftB(sub,(w-sub.w)/2,-(b.d+g+sub.h)));
    return overlay(parts,w);}
  let u=0,v=0,ox=0,sx=0;
  if(a.op==='∫'){u=sup?b.h-sup.h*0.5:0; v=sub?b.d-sub.h*0.5:0; ox=S*0.12; sx=-S*0.12;}
  else{u=sup?Math.max(S*0.4,b.h-S*0.28):0; v=sub?Math.max(S*0.16,b.d-S*0.2):0;
    if(sup&&sub){const gap=(u-sup.d)-(sub.h-v); if(gap<S*0.18) v+=S*0.18-gap;}}
  const parts=[]; let w=0;
  if(sup){parts.push(shiftB(sup,ox,u));w=Math.max(w,ox+sup.w);} if(sub){parts.push(shiftB(sub,Math.max(0,ox+sx),-v));w=Math.max(w,Math.max(0,ox+sx)+sub.w);}
  return hpack([b,spaceB(S*0.02),overlay(parts,w),spaceB(a.op==='∫'?S*0.08:0)]);}
const SP={ord:{op:1,bin:2,rel:3,inner:1},op:{ord:1,op:1,rel:3,inner:1},bin:{ord:2,op:2,open:2,inner:2},rel:{ord:3,op:3,open:3,inner:3},
  close:{op:1,bin:2,rel:3,inner:1},punct:{ord:1,op:1,rel:1,open:1,close:1,punct:1,inner:1},inner:{ord:1,op:1,bin:2,rel:3,open:1,punct:1,inner:1},open:{}};
function buildList(atoms,c){const out=[];let prev=null;
  for(const a of atoms){
    if(a.cls==='bin'&&(!prev||['bin','op','rel','open','punct'].includes(prev.cls))) a.cls='ord';
    if(prev&&a.cls!=='space'&&prev.cls!=='space'){const k=(SP[prev.cls]||{})[a.cls]||0; if(k&&(c.level===0||k===1)) out.push(spaceB(c.size*[0,3,4,5][k]/18*(k===1&&a.cls==='op'?1:1)));}
    out.push(a.box); if(a.cls!=='space') prev=a;}
  return hpack(out);}
function parseList(tk,pos,c,stop){const atoms=[];while(pos.i<tk.length){const t=tk[pos.i];if(t==='}'||t===stop)break;const a=parseAtom(tk,pos,c);if(a)atoms.push(a);}return atoms;}
function group(tk,pos,c){if(tk[pos.i]==='{'){pos.i++;const l=parseList(tk,pos,c);pos.i++;return buildList(l,c);}const a=parseAtom(tk,pos,c,true);return a?a.box:B0();}
function parseAtom(tk,pos,c,bare){
  const t=tk[pos.i++]; let a=null;
  if(t==='{'){const l=parseList(tk,pos,c);pos.i++;a={cls:'ord',box:buildList(l,c)};}
  else if(t==='\\frac'){const sc=c.level===0&&c.display?c:sub_(c);const n=group(tk,pos,sc),d=group(tk,pos,sc);a={cls:'inner',box:frac(n,d,c)};}
  else if(t==='\\sqrt'){a={cls:'ord',box:sqrtB(group(tk,pos,c),c)};}
  else if(t==='\\left'){const dl=tk[pos.i++];const l=parseList(tk,pos,c,'\\right');pos.i++;const dr=tk[pos.i++];const inner=buildList(l,c);
    a={cls:'inner',box:hpack([delimB(dl,inner,c),inner,delimB(dr,inner,c)])};}
  else if(t==='\\,'||t==='\;'||t==='\\quad'){a={cls:'space',box:spaceB(c.size*(t==='\\,'?3/18:t==='\;'?5/18:1))};}
  else if(t==='\\mathrm'){const rc=Object.assign({},c,{rm:true});a={cls:'ord',box:group(tk,pos,rc)};}
  else if(t[0]==='\\'){const n=t.slice(1);
    if(GREEK[n]){const ch=GREEK[n];a={cls:'ord',box:gbox(ch,c,!c.rm&&ch===ch.toLowerCase())};}
    else if(SYM[n]){const [ch,cls,it]=SYM[n];a=cls==='op'?{cls,box:bigop(ch,c),op:ch}:{cls,box:gbox(ch,c,!!it)};}
    else a={cls:'ord',box:spaceB(0)};}
  else if(/[a-zA-Z]/.test(t)) a={cls:'ord',box:gbox(t,c,!c.rm)};
  else if(/[0-9.]/.test(t)) a={cls:'ord',box:gbox(t,c,false)};
  else if(t==='+') a={cls:'bin',box:gbox('+',c,false)};
  else if(t==='-') a={cls:'bin',box:gbox('−',c,false)};
  else if(t==='='||t==='<'||t==='>') a={cls:'rel',box:gbox(t,c,false)};
  else if(t==='('||t==='[') a={cls:'open',box:gbox(t,c,false)};
  else if(t===')'||t===']') a={cls:'close',box:gbox(t,c,false)};
  else if(t===',') a={cls:'punct',box:gbox(',',c,false)};
  else if(t==='/') a={cls:'ord',box:gbox('/',c,false)};
  else if(t==="'") a={cls:'ord',box:gbox('′',c,false)};
  else return null;
  let sup=null,sub=null;
  while(!bare&&pos.i<tk.length){const n=tk[pos.i];
    if(n==="'"){pos.i++;a.box=hpack([a.box,gbox('′',c,false)]);}
    else if(n==='^'&&!sup){pos.i++;sup=group(tk,pos,sub_(c));}
    else if(n==='_'&&!sub){pos.i++;sub=group(tk,pos,sub_(c));}
    else break;}
  if(sup||sub){a.box=scripts(a,sup,sub,c); if(a.cls==='op')a.cls='op';}
  return a;
}
function math(tex,o){o=o||{};const base=Object.assign({},DEFAULTS,o.params||{});
  const c=mctx(base,o.size||32,0,o.display!==false); const pos={i:0}; const tk=tokenize(tex);
  return buildList(parseList(tk,pos,c),c);}
function drawBox(ctx,box,x,y){for(const it of box.items){
  if(it.t==='g') paint(ctx,it.gd,x+it.x,y-it.y,it.s); else if(it.t==='r') ctx.fillRect(x+it.x,y-it.y-it.h,it.w,it.h);}}

/* ---------- public ---------- */
const ROMAN='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?\'’-–—/()[]&';
const EXTRA='ﬁﬂﬀ'; const OSFSET='0123456789';
const GREEKSET='αβγδεθλμπρσφψωΓΔΣΩ';
const MATHSET='+−×=<>()[]∑∫√∞∂′∇·';
const api={G,GI,DEFAULTS,KERN,shape,params,glyph,paint,drawText,measure,math,drawBox,compose,nib,ROMAN,GREEKSET,MATHSET,EXTRA,OSFSET,VERSION:'0.2',CURSIVE:Object.keys(GI).join('')};
if(typeof module!=='undefined') module.exports=api; else root.Warp=api;
})(this);
