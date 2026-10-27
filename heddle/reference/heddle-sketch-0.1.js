/* machine-made Shuttle — sketch 0.1 glyph engine.
   Font units, y up. Metrics: x-height 520, cap 700, ascender 730, descender -210, em 1000.
   Every glyph is built from four primitives: rect, ring (superellipse), parallelogram, V.
   Openings are cut with horizontal clips scoped to one ring, which gives Swiss horizontal terminals. */
(function(root){
"use strict";
const XH=520, CAP=700, ASC=730, DESC=-210, OS=10, N=2.6;

function superellipse(x0,y0,x1,y1,n){
  const cx=(x0+x1)/2, cy=(y0+y1)/2, rx=(x1-x0)/2, ry=(y1-y0)/2, pts=[];
  for(let i=0;i<96;i++){const t=i/96*Math.PI*2,c=Math.cos(t),s=Math.sin(t);
    pts.push([cx+rx*Math.sign(c)*Math.pow(Math.abs(c),2/n), cy+ry*Math.sign(s)*Math.pow(Math.abs(s),2/n)]);}
  return pts;
}
function tools(ctx,p){
  const S=p.S, H=p.H;
  const fin=(rule)=>{ctx.fill(rule||'nonzero');if(p.hair){ctx.lineWidth=p.hair;ctx.strokeStyle=ctx.fillStyle;ctx.lineJoin='miter';ctx.stroke();}};
  const cons=(drawPath)=>{if(!p.cons)return;ctx.save();ctx.strokeStyle=p.cons;ctx.lineWidth=(p.hair||1)*1.1;ctx.beginPath();drawPath();ctx.stroke();ctx.restore();};
  const trace=pts=>{ctx.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)ctx.lineTo(pts[i][0],pts[i][1]);ctx.closePath();};
  const T={
    S,H,
    rect(x0,y0,x1,y1){const r=()=>ctx.rect(Math.min(x0,x1),Math.min(y0,y1),Math.abs(x1-x0),Math.abs(y1-y0));ctx.beginPath();r();fin();cons(r);},
    // a superellipse ring; cuts are rectangles removed from THIS ring only (horizontal terminals)
    ring(x0,y0,x1,y1,cuts=[],ts=S,th=H){ctx.save();
      for(const c of cuts){ctx.beginPath();ctx.rect(-1e4,-1e4,2e4,2e4);
        ctx.rect(Math.min(c[0],c[2]),Math.min(c[1],c[3]),Math.abs(c[2]-c[0]),Math.abs(c[3]-c[1]));ctx.clip('evenodd');}
      const both=()=>{trace(superellipse(x0,y0,x1,y1,N));if(x1-x0>2*ts && y1-y0>2*th) trace(superellipse(x0+ts,y0+th,x1-ts,y1-th,N));};
      ctx.beginPath();both();fin('evenodd');ctx.restore();cons(both);},
    poly(pts){ctx.beginPath();trace(pts);fin();cons(()=>trace(pts));},
    // horizontal thickness that keeps a diagonal optically as heavy as a stem
    dt(dx,dy){return S*0.9*Math.hypot(dx,dy)/Math.abs(dy);},
    par(xa,ya,xb,yb,t){T.poly([[xa-t/2,ya],[xa+t/2,ya],[xb+t/2,yb],[xb-t/2,yb]]);},
    vee(x0,x1,yT,yB,t){
      const xm=(x0+x1)/2, oL=[x0,yT], oR=[x1,yT], bL=[xm-t/2,yB], bR=[xm+t/2,yB], iL=[x0+t,yT], iR=[x1-t,yT];
      const d1=[bL[0]-oL[0],yB-yT], d2=[bR[0]-oR[0],yB-yT];
      const det=-d1[0]*d2[1]+d2[0]*d1[1], rx=iR[0]-iL[0], ry=iR[1]-iL[1];
      const a=(rx*(-d2[1])-(-d2[0])*ry)/det, I=[iL[0]+a*d1[0], iL[1]+a*d1[1]];
      if(I[1]>yB) T.poly([oL,iL,I,iR,oR,bR,bL]); else T.poly([oL,iL,iR,oR,bR,bL]);
    },
    flipX(W,fn){ctx.save();ctx.translate(W,0);ctx.scale(-1,1);fn();ctx.restore();},
    rot(W,yc,fn){ctx.save();ctx.translate(W/2,yc);ctx.rotate(Math.PI);ctx.translate(-W/2,-yc);fn();ctx.restore();}
  };
  return T;
}

/* ---- shared constructions ---- */
function arch(g,x0,x1,top,stemTo){ // n-shoulder: upper half of a ring, then the right stem
  const ry=Math.min((x1-x0)*0.52, top*0.62), y0=top+OS-2*ry, cy=(y0+top+OS)/2;
  g.ring(x0,y0,x1,top+OS,[[x0-20,y0-20,x1+20,cy]]); g.rect(x1-g.S,stemTo,x1,cy+1);
}
function bowlD(g,x0,y0,x1,y1){ // square on the left, round on the right
  g.ring(x0,y0,x1,y1); g.rect(x0,y0,x0+(x1-x0)/2,y0+g.H); g.rect(x0,y1-g.H,x0+(x1-x0)/2,y1); g.rect(x0,y0,x0+g.S,y1);
}
function twoRingS(g,W,top){ // S and s: two stacked rings that share the spine
  const mid=top*0.48, yL1=mid+g.H, cU=(mid+top+OS)/2, cL=(-OS+yL1)/2;
  g.ring(W*0.04,mid,W*0.97,top+OS,[[W*0.5,-60,W+20,cU+(top-cU)*0.26]]);
  g.ring(0,-OS,W,yL1,[[-20,cL*0.72,W*0.5,yL1+20]]);
}
function six(g,W){ g.ring(0,-OS,W,CAP*0.64); g.ring(0,-OS,W*1.02,CAP+OS,[[W*0.5,-60,W*1.1,CAP*0.74]]); }

/* ---- glyph table: base width at width 100, and a draw function (g, W) ---- */
const G={};
function def(ch,base,fn,opt){G[ch]=Object.assign({base,fn},opt||{});}

// lowercase
def('o',560,(g,W)=>g.ring(0,-OS,W,XH+OS));
def('c',520,(g,W)=>g.ring(0,-OS,W,XH+OS,[[W*0.52,XH*0.30,W+20,XH*0.71]]));
def('e',540,(g,W)=>{const yb=XH*0.44;g.ring(0,-OS,W,XH+OS,[[W*0.5,XH*0.25,W+20,yb]]);g.rect(g.S*0.5,yb,W,yb+g.H);});
def('n',540,(g,W)=>{g.rect(0,0,g.S,XH);arch(g,0,W,XH,0);});
def('h',540,(g,W)=>{g.rect(0,0,g.S,ASC);arch(g,0,W,XH,0);});
def('m',820,(g,W)=>{const m=(W+g.S)/2;g.rect(0,0,g.S,XH);arch(g,0,m,XH,0);arch(g,m-g.S,W,XH,0);});
def('u',540,(g,W)=>g.rot(W,XH/2,()=>{g.rect(0,0,g.S,XH);arch(g,0,W,XH,0);}));
const bee=(g,W)=>{g.rect(0,0,g.S,ASC);g.ring(0,-OS,W,XH+OS);};
def('b',560,bee);
def('d',560,(g,W)=>g.flipX(W,()=>bee(g,W)));
def('p',560,(g,W)=>g.rot(W,XH/2,()=>g.flipX(W,()=>bee(g,W))));
def('q',560,(g,W)=>g.rot(W,XH/2,()=>bee(g,W)));
def('g',560,(g,W)=>{g.ring(0,-OS+20,W,XH+OS);const rh=170,y0=DESC-OS,cy=y0+rh;
  g.ring(0,y0,W,y0+2*rh,[[-20,cy,W+20,cy+2*rh+40]]);g.rect(W-g.S,cy-1,W,XH);});
def('a',520,(g,W)=>{const r=XH*0.36,y1=XH+OS,y0=y1-2*r,cy=y0+r;
  g.ring(0,y0,W,y1,[[-20,y0-20,W*0.5,cy+r*0.28],[W*0.5,y0-20,W-g.S,cy]]);g.rect(W-g.S,0,W,cy+1);
  const b1=XH*0.55;g.ring(0,-OS,W-g.S*0.4,b1);g.rect(W-g.S,0,W,b1);});
def('s',500,(g,W)=>twoRingS(g,W,XH));
def('i',0,(g,W)=>{g.rect(0,0,g.S,XH);const gap=Math.max(60,g.S*0.55);g.rect(0,XH+gap,g.S,XH+gap+g.S*1.04);},{fixed:true});
def('j',0,(g,W)=>{const x=W-g.S,y0=DESC-OS,cy=DESC+80;g.ring(0,y0,W,DESC+170,[[-20,cy,W+20,DESC+240]]);g.rect(x,cy-1,W,XH);
  const gap=Math.max(60,g.S*0.55);g.rect(x,XH+gap,W,XH+gap+g.S*1.04);},{fixed:true,extra:120});
def('l',0,(g,W)=>g.rect(0,0,g.S,ASC),{fixed:true});
def('f',330,(g,W)=>{const x=W*0.18,r=Math.min(150,(W-x)/2+10);g.rect(x,0,x+g.S,ASC-r+1);
  g.ring(x,ASC+OS-2*r,x+2*r+40,ASC+OS,[[x-20,ASC-2*r-20,x+2*r+60,ASC+OS-r]]);g.rect(0,XH-g.H,W,XH);});
def('t',330,(g,W)=>{const x=W*0.18,r=Math.min(130,(W-x)/2);g.rect(x,r-OS-1,x+g.S,XH+150);
  g.ring(x,-OS,x+2*r+30,2*r-OS,[[x-20,r-OS,x+2*r+60,2*r+20]]);g.rect(0,XH-g.H,W,XH);});
def('r',330,(g,W)=>{const ry=XH*0.42;g.ring(0,XH+OS-2*ry,W*1.9,XH+OS,[[-20,-20,W*2,XH+OS-ry],[W,0,W*2,XH+40]]);g.rect(0,0,g.S,XH);});
def('k',520,(g,W)=>{g.rect(0,0,g.S,ASC);const t=g.dt(W*0.7,XH);g.par(g.S*0.6,XH*0.30,W-t/2,XH,t);g.par(W*0.34,XH*0.52,W-t/2,0,t);});
def('v',520,(g,W)=>g.vee(0,W,XH,0,g.dt(W/2,XH)));
def('w',780,(g,W)=>{const t=g.dt(W/4,XH);g.vee(0,W*0.56,XH,0,t);g.vee(W*0.44,W,XH,0,t);});
def('x',520,(g,W)=>{const t=g.dt(W,XH);g.par(t/2,XH,W-t/2,0,t);g.par(W-t/2,XH,t/2,0,t);});
def('y',520,(g,W)=>{const t=g.dt(W/2,XH);g.vee(0,W,XH,0,t);const k=(W/2)/XH*(-DESC)*0.85;g.par(W/2,0,W/2-k,DESC+g.H*0.2,t);g.rect(W/2-k-t/2-60,DESC,W/2-k+t/2,DESC+g.H);});
def('z',480,(g,W)=>{const t=g.dt(W,XH);g.rect(0,XH-g.H,W,XH);g.rect(0,0,W,g.H);g.par(W-t/2,XH-g.H,t/2,g.H,t);});

// uppercase
def('A',660,(g,W)=>{const t=g.dt(W/2,CAP);g.rot(W,CAP/2,()=>g.vee(0,W,CAP,0,t));g.rect(W*0.18,CAP*0.22,W*0.82,CAP*0.22+g.H);});
def('B',620,(g,W)=>{bowlD(g,0,CAP*0.48,W*0.9,CAP);bowlD(g,0,0,W,CAP*0.48+g.H);});
def('C',680,(g,W)=>g.ring(0,-OS,W,CAP+OS,[[W*0.56,CAP*0.31,W+20,CAP*0.69]]));
def('D',660,(g,W)=>bowlD(g,0,0,W,CAP));
def('E',560,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(0,CAP-g.H,W,CAP);g.rect(0,0,W,g.H);g.rect(0,CAP*0.47,W*0.9,CAP*0.47+g.H);});
def('F',530,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(0,CAP-g.H,W,CAP);g.rect(0,CAP*0.45,W*0.9,CAP*0.45+g.H);});
def('G',700,(g,W)=>{g.ring(0,-OS,W,CAP+OS,[[W*0.55,CAP*0.47,W+20,CAP*0.69]]);g.rect(W*0.5,CAP*0.47-g.H,W,CAP*0.47);g.rect(W-g.S,0,W,CAP*0.47);});
def('H',640,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(W-g.S,0,W,CAP);g.rect(0,CAP*0.47,W,CAP*0.47+g.H);});
def('I',0,(g,W)=>g.rect(0,0,g.S,CAP),{fixed:true});
def('J',520,(g,W)=>{const r=W*0.5,cy=r-OS;g.ring(0,-OS,W,2*r-OS,[[-20,cy,W+20,2*r+20]]);g.rect(W-g.S,cy-1,W,CAP);});
def('K',640,(g,W)=>{g.rect(0,0,g.S,CAP);const t=g.dt(W,CAP*0.6);g.par(g.S*0.5,CAP*0.28,W-t/2,CAP,t);g.par(W*0.32,CAP*0.5,W-t/2,0,t);});
def('L',520,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(0,0,W,g.H);});
def('M',800,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(W-g.S,0,W,CAP);g.vee(0,W,CAP,0,g.dt(W/2,CAP)*0.92);});
def('N',650,(g,W)=>{g.rect(0,0,g.S,CAP);g.rect(W-g.S,0,W,CAP);const t=g.dt(W,CAP);g.poly([[0,CAP],[t,CAP],[W,0],[W-t,0]]);});
def('O',740,(g,W)=>g.ring(0,-OS,W,CAP+OS));
def('P',600,(g,W)=>{g.rect(0,0,g.S,CAP);bowlD(g,0,CAP*0.40,W,CAP);});
def('Q',740,(g,W)=>{g.ring(0,-OS,W,CAP+OS);const t=g.dt(W*0.3,CAP*0.35);g.par(W*0.62,CAP*0.24,W*0.96,-OS-30,t);});
def('R',630,(g,W)=>{g.rect(0,0,g.S,CAP);bowlD(g,0,CAP*0.42,W*0.97,CAP);const t=g.dt(W*0.5,CAP*0.42);g.par(W*0.5,CAP*0.42+g.H*0.5,W-t/2,0,t);});
def('S',620,(g,W)=>twoRingS(g,W,CAP));
def('T',580,(g,W)=>{g.rect(0,CAP-g.H,W,CAP);g.rect(W/2-g.S/2,0,W/2+g.S/2,CAP);});
def('U',640,(g,W)=>{const r=W*0.48,cy=r-OS;g.ring(0,-OS,W,2*r-OS,[[-20,cy,W+20,2*r+20]]);g.rect(0,cy-1,g.S,CAP);g.rect(W-g.S,cy-1,W,CAP);});
def('V',640,(g,W)=>g.vee(0,W,CAP,0,g.dt(W/2,CAP)));
def('W',920,(g,W)=>{const t=g.dt(W/4,CAP);g.vee(0,W*0.56,CAP,0,t);g.vee(W*0.44,W,CAP,0,t);});
def('X',640,(g,W)=>{const t=g.dt(W,CAP);g.par(t/2,CAP,W-t/2,0,t);g.par(W-t/2,CAP,t/2,0,t);});
def('Y',620,(g,W)=>{g.vee(0,W,CAP,CAP*0.40,g.dt(W/2,CAP*0.6));g.rect(W/2-g.S/2,0,W/2+g.S/2,CAP*0.44);});
def('Z',590,(g,W)=>{const t=g.dt(W,CAP);g.rect(0,CAP-g.H,W,CAP);g.rect(0,0,W,g.H);g.par(W-t/2,CAP-g.H,t/2,g.H,t);});

// figures: tabular
const FW=560;
def('0',FW,(g,W)=>g.ring(W*0.04,-OS,W*0.96,CAP+OS),{tab:true});
def('1',FW,(g,W)=>{const x=W*0.55;g.rect(x,0,x+g.S,CAP);g.poly([[x+g.S*0.3,CAP],[x-W*0.34,CAP*0.74],[x-W*0.34,CAP*0.74-g.H],[x+g.S*0.3,CAP-g.H*1.5]]);},{tab:true});
def('2',FW,(g,W)=>{const r=CAP*0.27,y0=CAP+OS-2*r,cy=y0+r;g.ring(0,y0,W,CAP+OS,[[-20,y0-20,W+20,cy],[-20,cy-1,W*0.4,cy+r*0.25]]);
  const t=g.dt(W*0.8,cy);g.poly([[W-t,cy],[W,cy],[t*0.9,g.H],[0,g.H]]);g.rect(0,0,W,g.H);g.rect(W-g.S,cy-30,W,cy+1);},{tab:true});
def('3',FW,(g,W)=>{const m=CAP*0.53,cU=(m-g.H+CAP+OS)/2,cL=(-OS+m)/2;
  g.ring(W*0.06,m-g.H,W*0.94,CAP+OS,[[-20,m-g.H-20,W*0.45,cU+(CAP-cU)*0.12]]);
  g.ring(0,-OS,W,m,[[-20,cL*0.65,W*0.45,m+20]]);g.rect(W*0.32,m-g.H,W*0.6,m);},{tab:true});
def('4',FW,(g,W)=>{const x=W*0.64;g.rect(x,0,x+g.S,CAP);const t=g.dt(x,CAP*0.7);g.poly([[x-t*0.2,CAP],[x+g.S*0.4,CAP],[t*0.7,CAP*0.3],[0,CAP*0.3]]);g.rect(0,CAP*0.24,W,CAP*0.24+g.H);},{tab:true});
def('5',FW,(g,W)=>{const top=CAP*0.62,cy=top/2;g.ring(0,-OS,W,top+OS,[[-20,cy*0.58,W*0.42,top+40],[-20,cy,W*0.46,top+40]]);
  g.rect(W*0.06,top+OS-g.H,W*0.5,top+OS);g.rect(W*0.06,top-30,W*0.06+g.S,CAP);g.rect(W*0.06,CAP-g.H,W*0.94,CAP);},{tab:true});
def('6',FW,six,{tab:true});
def('7',FW,(g,W)=>{g.rect(0,CAP-g.H,W,CAP);const t=g.dt(W*0.6,CAP);g.par(W-t/2,CAP-g.H,W*0.36,0,t);},{tab:true});
def('8',FW,(g,W)=>{g.ring(W*0.07,CAP*0.52-g.H,W*0.93,CAP+OS);g.ring(0,-OS,W,CAP*0.52);},{tab:true});
def('9',FW,(g,W)=>g.rot(W,CAP/2,()=>six(g,W)),{tab:true});

// punctuation
def('.',0,(g,W)=>g.rect(0,0,g.S*1.06,g.S*1.06),{fixed:true,extra:6});
def(',',0,(g,W)=>{const d=g.S*1.06;g.rect(0,0,d,d);g.poly([[d*0.25,0],[d,0],[d*0.55,-d*1.1],[d*0.1,-d*1.1]]);},{fixed:true,extra:6});
def(':',0,(g,W)=>{const d=g.S*1.06;g.rect(0,0,d,d);g.rect(0,XH-d,d,XH);},{fixed:true,extra:6});
def('!',0,(g,W)=>{const d=g.S*1.06;g.rect(0,0,d,d);g.rect(d*0.04,d+Math.max(60,g.S*0.5),d*0.96,CAP);},{fixed:true,extra:6});
def("'",0,(g,W)=>g.rect(0,CAP*0.66,g.S,CAP),{fixed:true});
def('-',300,(g,W)=>g.rect(0,XH*0.42,W,XH*0.42+g.H*1.05));
def('–',500,(g,W)=>g.rect(0,XH*0.42,W,XH*0.42+g.H));
def('/',360,(g,W)=>{const t=g.dt(W,CAP+120);g.par(W-t/2,CAP+20,t/2,-100,t);});
def('&',700,(g,W)=>{g.ring(W*0.08,CAP*0.5,W*0.66,CAP+OS);g.ring(0,-OS,W*0.82,CAP*0.56,[[W*0.6,CAP*0.1,W,CAP*0.6]]);
  const t=g.dt(W*0.6,CAP*0.5);g.par(W*0.22,CAP*0.6,W-t/2,0,t);g.rect(W*0.6,CAP*0.36,W,CAP*0.36+g.H);});
def(' ',260,()=>{});

/* ---- public API ---- */
function params(o){ // o: {wght 100..900, wdth 70..140, track (units), hair, cons}
  const t=(o.wght-100)/800, S=28+t*(178-28), H=S*0.84;
  return {S,H,wf:o.wdth/100,track:o.track||0,hair:o.hair||0,cons:o.cons||null};
}
function sb(p){return 22+p.S*0.22+p.track;}
function glyphBox(ch,p){
  const gl=G[ch]; if(!gl) return null;
  let W;
  if(gl.fixed) W=(ch==='j'?p.S+gl.extra:p.S*(ch==='.'||ch===','||ch===':'||ch==='!'?1.06:1));
  else if(gl.tab) W=gl.base*Math.min(1.25,Math.max(0.8,p.wf)) ;
  else W=gl.base*p.wf;
  if(!gl.fixed && !gl.tab) W=Math.max(W, p.S*2.3);
  return {W, adv:W+2*sb(p)};
}
function drawGlyph(ctx,ch,p){ // caller has set transform: origin at left sidebearing, baseline, y up
  const gl=G[ch]; if(!gl) return;
  const b=glyphBox(ch,p); const g=tools(ctx,p);
  ctx.save(); ctx.translate(sb(p),0); gl.fn(g,b.W); ctx.restore();
}
const api={G,XH,CAP,ASC,DESC,params,sb,glyphBox,drawGlyph,CHARSET:'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:!\'-–/'};
if(typeof module!=='undefined') module.exports=api; else root.Shuttle=api;
})(this);
