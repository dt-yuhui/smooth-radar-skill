#!/usr/bin/env python3
"""smooth radar smooth radar renderer for scientific figures."""
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import font_manager

# Publication typography: Arial is first choice; use a clean sans-serif fallback
# on systems where Arial is not installed.
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Liberation Sans", "DejaVu Sans"]

def validate(cfg):
    models, axes = cfg["models"], cfg["axes"]
    values = np.asarray(cfg["values"], dtype=float)
    if values.shape != (len(models), len(axes)):
        raise ValueError(f"values shape must be ({len(models)}, {len(axes)}), got {values.shape}")
    if not np.isfinite(values).all():
        raise ValueError("values contain NaN/Inf; missing values are not imputed.")
    if len(set(models)) != len(models) or len(set(axes)) != len(axes):
        raise ValueError("model names and axis labels must be unique.")
    if cfg.get("direction", "higher") not in ("higher", "lower"):
        raise ValueError("direction must be higher or lower.")
    if len(cfg.get("colors", [])) != len(models):
        raise ValueError("Provide exactly one color per model.")
    if len(cfg.get("axis_groups", [""]*len(axes))) != len(axes):
        raise ValueError("axis_groups must have one entry per axis.")
    if cfg.get("scale", {}).get("mode") != "dual_anchor_custom":
        raise ValueError("This smooth-radar-only skill supports scale.mode='dual_anchor_custom' only.")
    if cfg.get("curve", {}).get("mode", "centripetal_catmull_rom") != "centripetal_catmull_rom":
        raise ValueError("This smooth-radar-only skill supports centripetal_catmull_rom only.")
    return values

def map_values(values, cfg):
    scale = cfg["scale"]
    n_axes = values.shape[1]
    inner = np.asarray(scale["inner_anchor"], float)
    outer = np.asarray(scale["outer_anchor"], float)
    if inner.shape != (n_axes,) or outer.shape != (n_axes,):
        raise ValueError("inner_anchor and outer_anchor must each have one value per axis.")
    if np.any(inner < 0) or np.any(outer > 1) or np.any(outer <= inner):
        raise ValueError("Anchors must satisfy 0 <= inner_anchor < outer_anchor <= 1.")
    oriented = values if cfg.get("direction", "higher") == "higher" else -values
    radii = np.empty_like(values)
    audit_axes = []
    for j in range(n_axes):
        col = oriented[:, j]
        mn, mx = float(col.min()), float(col.max())
        zero_span = abs(mx-mn) <= 1e-15
        radii[:, j] = (inner[j]+outer[j])/2 if zero_span else inner[j] + (col-mn)/(mx-mn)*(outer[j]-inner[j])
        audit_axes.append({
            "axis_index": j, "axis_label": cfg["axes"][j],
            "raw_min": float(values[:,j].min()), "raw_max": float(values[:,j].max()),
            "inner_anchor": float(inner[j]), "outer_anchor": float(outer[j]),
            "zero_span": bool(zero_span)
        })
    audit = {
        "scale_mode": "dual_anchor_custom",
        "direction": cfg.get("direction","higher"),
        "raw_values": values.tolist(),
        "mapped_radii": radii.tolist(),
        "axes": audit_axes,
        "cross_axis_radial_comparability": False,
        "warning": "Within-axis ordering is preserved; radial distances across axes are not directly comparable."
    }
    return radii, audit

def catmull_rom_closed(points, samples=40, alpha=0.5):
    p = np.asarray(points, dtype=float)
    n = len(p)
    out = []
    eps = 1e-10
    for i in range(n):
        p0,p1,p2,p3 = p[(i-1)%n],p[i],p[(i+1)%n],p[(i+2)%n]
        step = lambda a,b: max(float(np.linalg.norm(b-a)),eps)**alpha
        t0=0.0; t1=t0+step(p0,p1); t2=t1+step(p1,p2); t3=t2+step(p2,p3)
        for t in np.linspace(t1,t2,samples,endpoint=False):
            A1=(t1-t)/(t1-t0)*p0+(t-t0)/(t1-t0)*p1
            A2=(t2-t)/(t2-t1)*p1+(t-t1)/(t2-t1)*p2
            A3=(t3-t)/(t3-t2)*p2+(t-t2)/(t3-t2)*p3
            B1=(t2-t)/(t2-t0)*A1+(t-t0)/(t2-t0)*A2
            B2=(t3-t)/(t3-t1)*A2+(t-t1)/(t3-t1)*A3
            out.append((t2-t)/(t2-t1)*B1+(t-t1)/(t2-t1)*B2)
    out=np.asarray(out)
    return np.vstack([out,out[0]])

def curve_with_label_gaps(curve, model_index, values, samples, gap_samples, tie_tolerance=0.0):
    """Mask local spline samples around this model's own raw min/max vertices."""
    if gap_samples <= 0:
        return curve
    n_axes=values.shape[1]
    preserve=np.ones(len(curve),dtype=bool)
    for j in range(n_axes):
        col=values[:,j]
        x=values[model_index,j]
        is_extreme=(x == col.min()) or (x == col.max())
        if tie_tolerance > 0:
            is_extreme = abs(x-col.min()) <= tie_tolerance or abs(x-col.max()) <= tie_tolerance
        if is_extreme:
            center=j*samples
            for d in range(-gap_samples,gap_samples+1):
                preserve[(center+d) % (n_axes*samples)] = False
    out=curve.copy()
    out[~preserve,:]=np.nan
    return out

def _extrema(cfg, values):
    ann=cfg.get("annotations",{})
    precision=int(ann.get("precision",3))
    tol=float(ann.get("tie_tolerance",0.0))
    neutral=ann.get("neutral_tie_color","#AEB8BE")
    extrema=[]
    for j,axis in enumerate(cfg["axes"]):
        col=values[:,j]
        for kind,val,offset in [
            ("min",float(np.min(col)),float(ann.get("min_label_offset",-.018))),
            ("max",float(np.max(col)),float(ann.get("max_label_offset",.018)))
        ]:
            if kind=="max" and abs(float(np.max(col))-float(np.min(col))) <= tol:
                continue
            ids=np.where(np.abs(col-val)<=tol)[0] if tol>0 else np.where(col==val)[0]
            color=cfg["colors"][ids[0]] if len(ids)==1 else neutral
            extrema.append({"axis_index":j,"axis":axis,"kind":kind,"raw_value":val,
                            "models":[cfg["models"][i] for i in ids],
                            "color":color,"radial_text_offset":offset,
                            "text":f"{val:.{precision}f}"})
    return extrema

def render(cfg, outdir):
    values=validate(cfg)
    radii,audit=map_values(values,cfg)
    n_models,n_axes=values.shape
    curve_cfg=cfg.get("curve",{})
    samples=int(curve_cfg.get("samples_per_segment",40))
    alpha=float(curve_cfg.get("alpha",.5))
    style=cfg.get("style",{})
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        style.get("font_family", "Arial"),
        *style.get("font_fallback", ["Liberation Sans", "DejaVu Sans"])
    ]
    colors=cfg["colors"]
    groups=cfg.get("axis_groups",[""]*n_axes)
    group_colors=cfg.get("group_colors",{})
    theta=np.pi/2-np.arange(n_axes)*2*np.pi/n_axes
    fig,ax=plt.subplots(figsize=style.get("figsize",[8.5,8.5]))
    ax.set_aspect("equal"); ax.axis("off")
    grid_color = style.get("grid_color", "#E3E8EB")
    for rr in [.2,.4,.6,.8,1.0]:
        ax.add_patch(plt.Circle((0,0),rr,fill=False,ec=style.get("ring_color",grid_color),
                                lw=style.get("ring_width_pt",.45),zorder=0))
    for t in theta:
        ax.plot([0,np.cos(t)],[0,np.sin(t)],color=style.get("spoke_color","#D7E0E5"),
                lw=style.get("spoke_width_pt",.4),ls=(0,(2,3)),zorder=0)
    label_radius=float(style.get("label_radius",1.17))
    for t,label,group in zip(theta,cfg["axes"],groups):
        ax.text(label_radius*np.cos(t),label_radius*np.sin(t),label,
                ha="center",va="center",fontsize=style.get("label_fontsize",8),
                color=style.get("label_color","#26343D"),
                bbox=dict(boxstyle=f"round,pad={style.get('label_pad',.22)}",
                          fc=style.get("label_facecolor","white"),
                          ec=group_colors.get(group,"#AAB8C2"),
                          lw=style.get("label_border_width_pt",.7)))
    highlight=style.get("highlight_model",cfg["models"][-1])
    order=[i for i,m in enumerate(cfg["models"]) if m!=highlight]+[i for i,m in enumerate(cfg["models"]) if m==highlight]
    gap_samples=int(style.get("line_gap_samples",3))
    tie_tol=float(cfg.get("annotations",{}).get("tie_tolerance",0.0))
    line_records=[]
    for i in order:
        xy=np.c_[radii[i]*np.cos(theta),radii[i]*np.sin(theta)]
        curve=catmull_rom_closed(xy,samples=samples,alpha=alpha)
        curve=curve_with_label_gaps(curve,i,values,samples,gap_samples,tie_tol)
        is_highlight=cfg["models"][i]==highlight
        lw=float(style.get("highlight_width_pt",style.get("highlight_width",1.8)) if is_highlight
                 else style.get("line_width_pt",style.get("line_width",1.0)))
        ax.plot(curve[:,0],curve[:,1],color=colors[i],lw=lw,
                alpha=1.0 if is_highlight else float(style.get("other_alpha",.88)),
                zorder=3+i,solid_capstyle="round")
        ax.scatter(xy[:,0],xy[:,1],s=float(style.get("marker_size_pt",2.0))**2,
                   color=colors[i],edgecolors="white",linewidths=.3,zorder=10+i)
        line_records.append({"model":cfg["models"][i],"line_width_pt":lw,"line_gap_samples":gap_samples})
    extrema=_extrema(cfg,values)
    for e in extrema:
        j=e["axis_index"]; ids=[cfg["models"].index(m) for m in e["models"]]
        # Label follows the actual extremum point's mapped radius; ties use neutral color.
        idx=ids[0]
        r=radii[idx,j]+e["radial_text_offset"]
        t=theta[j]
        ax.text(r*np.cos(t),r*np.sin(t),e["text"],ha="center",va="center",
                fontsize=style.get("score_fontsize",7),color=e["color"],
                fontweight="bold" if e["kind"]=="max" else "normal",clip_on=False,zorder=30)
    # Optional Overall summary column, independent of radar geometry.
    summary=cfg.get("summary")
    if summary:
        sx=float(style.get("summary_x",1.02))
        sy=float(style.get("summary_y",.5))
        ax.text(sx,sy+0.10,"Overall",transform=ax.transAxes,ha="left",va="center",
                fontsize=style.get("summary_header_fontsize",7.5),fontweight="bold")
        for i,item in enumerate(summary):
            y=sy - i*float(style.get("summary_row_step",.055))
            ax.text(sx,y,f"{item['value']:.{int(item.get('precision',4))}f}",
                    transform=ax.transAxes,ha="left",va="center",
                    fontsize=style.get("summary_fontsize",7.2),
                    color=item.get("color",colors[i] if i<len(colors) else "#333333"),
                    fontweight=item.get("weight","normal"))
    handles=[Line2D([0],[0],color=colors[i],
                    lw=float(style.get("highlight_width_pt",style.get("highlight_width",1.8)) if cfg["models"][i]==highlight
                            else style.get("line_width_pt",style.get("line_width",1.0))),
                    marker="o",markersize=3,label=cfg["models"][i]) for i in range(n_models)]
    ax.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,-.09),
              ncol=min(int(style.get("legend_ncol",3)),n_models),frameon=False,
              fontsize=style.get("legend_fontsize",8))
    ax.set_xlim(-1.38,1.48 if summary else 1.38); ax.set_ylim(-1.36,1.36)
    title_text = cfg.get("title","smooth radar smooth radar")
    if cfg.get("subtitle"):
        title_text += "\n" + cfg["subtitle"]
    ax.set_title(title_text,fontsize=style.get("title_fontsize",13),
                 fontweight="bold",pad=18)
    caption=("Axis-specific display ranges were used to visualize task-wise profiles. "
             "Within-axis model ordering is preserved; radial distances across axes are not directly comparable. "
             "Curves between categorical axes are visual interpolation only.")
    fig.text(.5,.018,caption,ha="center",fontsize=6.5,color="#6B7780",wrap=True)
    fig.subplots_adjust(left=.06,right=.94,top=.90,bottom=.17)
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    name=cfg.get("name","smooth_radar")
    for ext in ("png","svg","pdf"):
        fig.savefig(outdir/f"{name}.{ext}",dpi=int(style.get("dpi",400)),
                    bbox_inches="tight",facecolor="white")
    plt.close(fig)
    audit.update({
        "models":cfg["models"],"axes_labels":cfg["axes"],"extrema":extrema,
        "curve":{"mode":"centripetal_catmull_rom","alpha":alpha,"samples_per_segment":samples},
        "line_rendering":line_records,
        "summary":summary,
        "caption_note":caption
    })
    (outdir/"scale_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")

def main():
    p=argparse.ArgumentParser(description="Render a smooth radar smooth radar chart.")
    p.add_argument("--config")
    p.add_argument("--preset",choices=["example"])
    p.add_argument("--preset-file",default=str(Path(__file__).resolve().parents[1]/"assets"/"example_presets.json"))
    p.add_argument("--outdir",required=True)
    args=p.parse_args()
    if args.preset:
        data=json.loads(Path(args.preset_file).read_text(encoding="utf-8"))
        cfg=data[args.preset]
    elif args.config:
        cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    else:
        p.error("Provide --config or --preset.")
    render(cfg,args.outdir)

if __name__=="__main__":
    main()
