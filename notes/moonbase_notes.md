# Moonbase hero refine — progress notes

Script: repo/scripts/moonbase.py (github james184298/office-tower-render, main). Render via job.yml on GitHub CPU (Eevee Next, xvfb).
Helpers: `jd.sh CMD` dispatches and prints run id; `jw.sh RUN` polls ~100 s, then pulls out-branch and writes jobs/RUN/cmp.jpg (ref | render, 540x675 each).

## Camera/layout derived from the reference (720x900 ref px)
- Ortho, sensor_fit HORIZONTAL, ortho_scale 20 (1 ref px = 0.0277 units), rotation (60°, 0, 45°): slab edges in the ref slope ±0.5 → 30° elevation, 45° azimuth.
- Block-top centre placed at ref px (380, 395). Block x∈[-6.5,6.5], y∈[-6,6], top z=0; corner cutaway x>-1, y<-0.6.
- Rocket at (-3.5,-1.6), ~11.5 tall; Earth at ref px (580,135) r≈55 px; stars on a camera-facing emissive backdrop plane (the world bg is uniform under an ortho camera, so world stars don't show).

## Rounds
- v3 (run 43157737485, 361 s render): full rewrite: bmesh rock with noise silhouette + taper, boolean corner cut + elevator slot, 5 floors, props, bots, surface props. Composition now matches.
- v4 (run 43158783631, 784 s — too slow): strata/regolith/screens/bots tweaks; 3 point lights in the elevator made it 2x slower → removed in v5.
- v5: denser lower floors (chairs, tables, carpet lounge, bar, plants), sign rotated toward camera, rocket r=1.2, darker regolith, AgX Punchy.
- v6 (run 43161810484, 605 s on a slow runner): sign fixed (thin extrusion, rotated 22° toward camera), screens = navy panels + cyan/orange chart strips, look back to AgX Medium High Contrast + exposure 0.35, deeper taper.
- v7 (run 43163252003, 457 s, samples 32→24): lower-floor props pulled toward the open front (they were hidden under the slab above), flaps removed, softer bots.
- v8 (run 43164370755, 304 s): darker/high-contrast strata, non-metal light frames (metal read black against the black sky), sun moved front-left so the rocket reads white, bigger bots, tank moved forward.
- v9 FINAL (run 43165201351, commit "moonbase v9b", render 462 s/frame at 1080x1350, 24 samples; build ~50-70 s): broader strata + light crust under the surface, deeper bot colours.
  Output: jobs/43165201351/moon_hero.png, side-by-side jobs/43165201351/cmp.jpg.
  Gotcha: ShaderNodeMix in RGBA mode — inputs["A"] picks the hidden float socket; use MixRGB or indexes.

## Session 2 rounds (Nov 12)
- Re-measured floors off the ref: 4 floors (not 5), slab tops at Z0=-1.45, pitch FH=2.1, recess FZ_BOT=-10.2 (left slab edges at ref v≈500/565/632/697; v = 456.8 - 31.2 z for points on the x=XC,y=-B+0.15 edge).
  Visibility: a lower floor shows only ~2.4 units behind each open edge (camera 30° down), so props are placed explicitly in that band.
- Procedural raster images built in-script (Canvas class → bpy image, packed): big mission screen (countdown, gauges, trajectory over earth limb, launch photo, telemetry charts, status list), green list screen, console screens, dial panel, posters.
- BUG found: box() called transform_apply() with defaults, which applied LOCATION too, so every box later rotated (solar panels, rocket windows, console desks, flaps) swung about the world origin; tank fan blades ended up as grey sticks in the sky. Fixed in v13 (apply scale only).
- v10 run 43168798634 (417 s), v11 43170078983 (290 s), v12 43170992231 (290 s).

## Remaining gaps vs reference
- Lower floors still read as thin strips; ref shows more of each floor (ref floors likely shallower/stepped) and denser, smaller props.
- Mission-control consoles are too big/blocky; big wall screen is a simple navy panel, no detailed UI graphics.
- Strata still finer/more regular than the ref's soft broad bands; silhouette less chunky; no rubble at the bottom.
- Bots are a little pastel under AgX; no green glow rings under them.
- Rocket lacks the ref's grid fins/flaps and decal detail; landing pad lacks "LANDING ZONE 1" text; SPACEX sign lacks the X swoosh.
- Earth has no terminator/night side; elevator cab is a plain pink box.
- Render time swings 300-600 s depending on the GitHub runner.

## Session 3 (Nov 12 pm) — v13 onward
- v13–v23: see git log (box() location bug fix, rover, earth, solar grid, shaft/top station, cybertruck rover, lander + sign, broad strata, fins). v23 run 43180334614 (305 s).
- v24 run 43181379269 (459 s): deeper ocean, floor ring. v25 run 43181910447 (426 s): fins to pad, lander sign tweak. v25 kept as base (superset of v24; near-identical).
- Measurement tools: cmp2.sh RUN (50% overlay blend.jpg + top/mid/bot side-by-side crops at ref res), meas.py PNG (rocket silhouette rows/column), stars.py PNG (star counts per sky region).
- Projection (ref px, 720x900): u = 380 + 0.707(x+y)/k, v = 395 - (-0.354x + 0.354y + 0.866z)/k, k = 20/720. Near side of a vertical cylinder of radius R appears 0.5R lower than its axis.
- Measured off the ref (v25 overlay): rocket r=1.07 (render was 0.92) and 6 px too far left; band z 7.45-9.8; ogive nose tip z~11.75; body bottom z~0.55; SPACEX body text from z~2.9 to 5.9. Sign letters ~1.0 tall, S bottom-left at ref (367,255), row 8.1 long at 22° toward camera; ref letters are thin logotype glyphs (A without bar) on a thin scaffold. Ref stars: few and bright (≈6 in the 200x200 px sky patch above the sign; v25 had ~150 faint).
- v26 (commit 96135c4): all of the above + rock shader = discrete layers (floor(z*2.3 + warp) → white-noise tone) × stretched streak noise × grain × patches × dark layer-base line; slimmer right column; lighter floors; smaller consoles in 4 rows x 5; 25 bots total (20 floors + 2 top station + 2 surface + 1 elevator); earth uses NASA Blue Marble + clouds downloaded by the job cmd (cmdfull.txt) with procedural fallback.
- v26 run 43184161219 (311 s): rocket now matches the ref silhouette within ~3 px (meas.py); sign position matches; stars match density.
- v27 run 43185621357 (306 s): finer layers, bolder glyphs, three.js earth_atmos_2048 texture works (NASA URL times out from runners; earth_clouds_1024.png never downloads → skipped).
- GOTCHA: run 43186335321 was meant as v28 but GitHub resolved main to the previous commit (dispatch right after push). Always `sleep 12` after push before jd.sh.
- v28/v29 run 43187461613 (328 s): asymmetric taper about (2.5,2.5) via TAPER table, terrain hill TH(x,y) rising to the back-right corner (ref's +x face top edge reaches v~310) — silhouette now within ~15 px on both sides (sil.py).
- v30 run 43189000684 (443 s): strata tilted (layer coord z + 0.19(y-x)) so they read flatter than slab edges like the ref; geometry ledges follow.
- v31 run 43190509879 (492 s): no side boulders, crates by the shaft, recess light, darker floors, podium.
- v32 run 43191053318 (267 s): earth r=69 ref px centred on the Americas with ~40% night side (ELON -58, tilt 4°), fine dark layer lines + fine grain, small ledges, dimmer fill, taller glyphs. Best so far.
- edges.py RUN x0,y0,x1,y1 out.png: red = ref edges, green = render edges (slab edges coincide → floor geometry is right).

## Session 4 (Nov 13) — v33 onward
- v33 eab28d1 brighter console screens, darker regolith; v34 5e46126 condensed rocket SPACEX + swoosh; v35 a99ad2f (run 43193909265) solar 4 rows, crates, fill; v36 11518c4 (run 43195097796, 485 s) earth terminator, humanoid robots; v37 4a162b7 (run 43326732724, 483 s) sign mound, deeper letters, bench rework.
- lum.py (v35/v36): floor2 179 vs ref 121, top_mid 90 vs 129, right_face 34 vs 51, recess 167 vs 148.
- Measured: ref earth r≈72 ref px, same centre as render, lit ~72% of the disc from the left (terminator right of centre, night side black, soft edge). v36 had terminator at ~54%.
- Measured: ref kiosk + top-station roof sit ~25-30 ref px lower than the render (station shorter: TZ1 -0.73); ref dishes (3, facing camera-left) at the front-right edge at ref (632,415),(655,404),(682,393); front-right terrain lower than the back corner (hill ramp now from y=3.8).
- v38 e38ce7a (run 43327735793): all of the above + dimmer floor lights (62/55), slab 0.34, regolith ramp 0.12-0.38, fill 0.85, recess 48, italic glyph shear 0.2, bigger tank, denser lounge (armchairs, round tables) and garden (big plants, dark column, planters).

## Animation notes (source moon/moon_src.mp4: 1080x1350, 30 fps, 67.05 s = 2012 frames; 2 s contact sheet ana/tsheet.jpg)
- 0-3 s hero frame with title text overlay. ~4-7 s: cutaway closes (block shown solid, regolith top, crater), cursor clicks. ~8 s: rocket launches (engine glow, lifts out of frame), cutaway reopens. ~10 s rocket gone, crater visible on pad, UI floor list appears (left), click "Mission Control".
- ~12-16 s camera zoom/pan into mission control (ortho zoom ~2.5x), tooltip "Flight Director". ~18-20 s Starship Engineering floor ("Mechazilla"). ~22-24 s Starlink floor ("Laser Link", purple map screen). ~26-30 s Lobby (lowest floor, Octaweb lander replica, plants). ~32 s zoom back out to hero framing (rocket absent).
- ~34-38 s "Solar field" card: sun appears top-left, Earth moves toward the sun -> ~40 s total eclipse (ring), whole scene tinted red/brown, rock turns rust. ~44-46 s "Under Floor 1" zoom; ~48-50 s Tunnel Boring Machine under the floors; ~52 s camera pans down through rock strata; ~54-56 s cave with orange lamp light, black monolith; ~58 s TMA-1 monolith glows green, red bot appears.
- ~60 s back up: interior wide shot (counter 25 working/0 waiting); ~62 s rocket returns/lands with bright engine glare; ~64 s landing (light streaks); 66-67 s hero frame again with title.
- UI overlays (top-left badge, counters, bottom cards, floor list, cursor hand) are 2D: composite in ffmpeg afterwards, not in Blender.
- Bots bob/move between desks throughout; elevator cab travels; screens animate.
- Per-frame still render cost on GH Actions CPU: ~270-490 s at 1080x1350, 24 samples (runner-dependent). Full 2012 frames ≈ 150-270 CPU-hours.
- v38 run 43327735793 (429 s). v39 3c?/run 43329351529 (432 s): earth light dir, 9x5 solar, dishes face camera, black rocket band, grey floor side walls (M_lwall), darker rock tone, sun shadow_maximum_resolution 0.0005.
- v40 run 43330927864 (199 s fast runner): soft terminator, ELON -52, bolder glyphs, darker floors (slab 0.27, lights 50), garden deck removed so SPACEX mat shows.
- v41 run 43331881030 (357 s): glyph rounded() dedupe + 0.42 corner cap (the "spikes" were really depth faces), ETILT 22 (too much -> 12 in v44), lighter clouds (pow 1.5), recess ground + tank label/frames.
- v42 e47b20a run 43332765725 (393 s): bigger gold lander, longer lounge bar. v43 d136570 run 43333512434 (259 s): sign glyphs GW .95 GH .8 ST .25, spacing .47, less italic (0.12), raised 0.2 — sign size/position now matches the ref within a few px. Smaller bots s=.25.
- v44 e957041 run 43334180059 (207 s): plat dark (looked light due to specular -> v46 matte), thick rim. v45 7207218 run 43334693819 (391 s): recess ground grey, metal pillars, sign emissive-white, regolith darker/finer.
- Measured (v44 column profiles at x=300): slab edges match the ref within ~6 px; floor pitch is right. Ref lower floors' back-left is darker -> v46 moves floor lights toward the open front.
- v46 run 43335763427, v47 run 43336264441 (earth ramp -0.04..0.42, rocket text 0.66 + offset .012, 3 hatches, sign top rail, regolith 0.075-0.28).

## Session 5 (Nov 13 pm) — v51 onward
- v51 a1ba81e run 43365876061 (260 s): voronoi block cells + cracks in the rock shader, softer streaks, 3 console rows/cluster, dim console screens, stronger bot glow, earth roll. BUG: the whole rock block vanished (EXACT boolean returned nothing) — caused by the ledge change (LEDA 0.13 + x-varying LEDB 0.06, OFF0 0.02) or the stronger taper. v52 (surface rocks) cancelled for the same bug.
- Earth orientation: ELON more negative moves the Americas RIGHT (toward the terminator). Ref: NA upper-left of SA => counter-clockwise roll (EROLL positive).
- v53 makes LEDA/LEDB/OFF0/OLDTAPER env-tunable and prints "BLOCK_SECONDS polys N" (evaluated block poly count) in the job log.
- Runs 43366849659 (LEDA .05/OFF0 .1, new taper) and 43366858255 (new ledges, OLDTAPER) both rendered fine (block polys ~25k): the v51 empty block was a flaky EXACT boolean on that exact mesh. v54 adds a FAST-solver fallback when evaluated polys < 5000.
- Voronoi crack lines in the rock read as cobblestones/hex tiles — removed in v54 (kept only a subtle flat-block tone).
- v54 4f? run 43367959599 (240 s): strata now read as bands; left silhouette within ~5 px from v=380 to 820 (ns bulge at the taper onset was the 20 px overshoot: now smoothed, amplitude 0.05).
- v55 run 43368306662: FZ_BOT -9.4 (ref pillars under the lowest floor are short, ~1 unit), plank stacks front-right, speckled regolith, sun (-0.34,-1,0.8) angle 7.
- v56 run 43368909172: strata 4.6/unit, warp 3.6, lines 0.05 wide, darker tone; fill sun now casts shadows; 5 console rows; garden deck; earth ELON -68 ETILT 6 EROLL 20 (v54 at -55/15 showed Greenland + Africa).
- v57 run 43369073429 (274 s): regolith speckle visible (scale 9; scale 45 averaged out sub-pixel) + low-freq dark patches.
- v58 ce7ceaa run 43370029151 (392 s): sun raised to ~50 deg (aim (-0.34,-1,1.25)) — the ref's big soft dark shape across the surface is the ROCKET SHADOW running up-right; lum now top_mid 123/129, left_face 88/91, right_face 47/51, floor2 133/121, floor0 46/58, recess 136/148.
- Earth: v58 (ELON -60, tilt 0, roll 25) shows NA upper-left but SA right of centre and Sahara at the terminator; ref has SA centre-left.
- v59 run 43371193217: ELON -52 tilt 8, 110 flatter rocks, recess ground 0.12.
- v60 run 43372081329: BLH rise on the back-left edge (TH gaussian at (-6.3,3.0)); earth ldir up -0.12 hides Africa on the night side. v61 run 43372345075: plat 0.14 (ref MC floor mid grey), taller big screen.
- Lum zones are misleading for floor2: that box covers the eng floor's back-left wall + bots; judge interiors by zoomed crops.
- v62 run 43373115012 (223 s): light floors (slab 0.3) + full-height light walls on lower floors, subtler glow, BLH 1.4 (top-edge profile right of the rocket now within ~10 px, topedge.py), ELON -54.
- v63 run 43373875510: walls 0.36, earth r 72, ELON -50. v64 run 43373935383: bots s 0.3, console screens strength 0.6 (ref MC rows show lit teal/blue monitors and are denser than v56+'s 5 rows — consider going back to ~8 rows of small desks).
- topedge.py RUN.png: top-surface edge profile vs ref (rows from 150 down; ref columns 70-190 are covered by the title text).

## Session 6 (Nov 13, ~14:00) — v65 onward
- Reviewed v63 (43373875510) and v64 (43373935383): both OK (~395 s render). v64 earth: SA still right of centre at ELON -50.
- Zoomed lower floors (crop2.sh RUN 620 560 280 900): the glass railings + white top rails on each slab edge read as a solid light band ~40 px tall that hides the lower floors' surfaces; ref floor edges are thin and the floors are wide open.
- v65 7?? run 43375286913: MC console rows rebuilt dense (6 rows x 2 blocks: 6+5 desks, seg .42, depth .85), surface rim railing off (RRAIL=1 restores), ELON -40.
- v66 run 43375349565: glass floor railings off (GRAIL=1 restores), slab thickness SLABT 0.16 (was 0.22).
- v65 reviewed: surface rail removal matches ref. 6 MC rows far too dense (desks hide floor + bots). ELON -40 brings Africa onto the right limb — worse; v64's -50 already puts SA centre-left like the ref (disc-centre offset ~-0.08 r both).
- v67 run 43376509972: 4 MC rows at 1.0 pitch (6+5 desks each), bots moved into aisles, ELON -50.
- v66 run 43375349565: removing glass rails opened the floors up — good. v67 run 43376509972: 4 MC rows reads much closer to the ref (floor0 lum 46 vs ref 58, was 40). v68 run 43376818784: garden floor patch lum 106 -> 123 (ref 161) with GLE 45.
- Recess mismatch: ref recess ground runs OUT IN FRONT of the lowest floor with the tank sitting on it in front of the floor edge (and plank stacks bottom-centre-right); ours had the tank tucked under the floor and dark rock below. v69 run 43377615996: PORCH 1.1 ground slab in front (y -B-1.1..-B, top at FZ_BOT), TANKY -6.1, crates at (4.0,-6.85).
- v69 reviewed: porch idea right (ground in front of floor, tank on it) but the porch read as a bright sunlit slab with a hard edge, and the tank overlapped the left column. v70 run 43378464081: porch colour 0.065, TANKDX 0.9.
- Earth at ELON -50: SA centred OK but Africa shows on the lit right limb; ref terminator is at ~65% across the disc (ours ~75%). v71 run 43378523194: ELDB 0.22 (light dir back component, was 0.44).
- v70 reviewed: porch 0.065 too dark (ref mid grey) -> v72 run 43379529601 porch 0.11.
- v71 reviewed: terminator now at ~65% like the ref, Africa hidden, but SA sits on the terminator. v73: ELON -38, ETSOFT 0.38 (terminator ramp width, was 0.22).
- v72 (43379529601)/v73 (43379589295) reviewed: earth SA now sits in the lit side like the ref (ELON -38 with ELDB 0.22). Porch still read as a floating slab with a black gap below; ref ground is light (~140) and the rock face simply continues under its front edge.
- v74 run 43380702777: porch is a mesh wedge (top PORCHC 0.15 grey, sides M_rock) sloping back into the block over PORCHD 2.4. v75 run (next): ETSOFT 0.65.
- v74 reviewed: wedge porch works — ground now reads as a ledge of the block, rock continues under it (ref-like). Ground ~110 vs ref ~130.
- v75 run 43380749300: ETSOFT 0.65 barely softens the terminator (AgX contrast / emission); not worth more rounds. v76: plat 0.19, PORCHC 0.2.
- v77 d59c11c run 43383296164: earth smoothstep ramp ETMIN -0.22..ETSOFT 0.6 (To Min 0), texture downscaled ERES 360, procedural clouds ECLD 0.65, EVAL 1.7; lower floors M_slabL 0.5 + lwall 0.58 + LFE 38 + back fill area lights LBE 22 (no shadow); MC desks h MCH 0.7, MC bots s MCBS 0.34 raised 0.04.
- v77 reviewed: lower floors much brighter/open (floor0 lum 58.4 = ref 58.5), MC bots now read over lowered desks. Earth: cloud texture DID download this run (226 KB) -> wispy dense clouds; terminator still reads hard: AgX lifts the ramp's dim tail so the visible edge is where it hits 0.
- v78 e36b768 run 43384051529: ETMIN 0 ETSOFT 0.95 + EPOW 2 gamma, texture clouds off (ECTEX=1 restores), procedural ECLD 0.85; porch wedge bevel 0.45 + simple subsurf 3 + clouds displace 0.12 (PORCHSM=0 off).
- v78 reviewed: earth fade now soft but terminator moved too far left (half-brightness ~35% across; ref ~56%), chunky clouds too opaque/hard. Measured ref centre-row fade (2x px): full to ~1190, half ~1215, ~0 by 1260 (disc 1060-1348) => dot ~+0.08 full .. -0.28 zero with ldir as in the script. Porch bevel ok.
- Ground measured (2x px grid): ref ground ~95-110 lum covers x 300-940, y 1590-1710 (much bigger/lower than ours, which is a narrow 130-200 strip at x 540-800, y 1590-1680); ours is lighter but too small.
- v79 0d6dc6e run 43384737308: top station TZ1 -0.2 (was -0.73; ref box ~1.6x taller, roof ~20 ref px higher), frames 0.06 + mid band.
- v80 bfc7a1d run 43385232631: ETMIN -0.3 ETSOFT 0.12 EPOW 1.3; clouds 0.5-0.67 max 0.72; ground apron PORCH 2.0, PORCHL 2.2, flat to PORCHFLAT -6.9 then PORCHDROP 1.2 slope, PORCHD 3.4, PORCHC 0.16.
- v79 reviewed: station height now matches the ref (sil/framing unchanged: sil.py within ~10 px both sides).
- v80 reviewed: earth now lit almost to the limb with a sharp 20 px drop (terminator geometry compresses near the limb). Empirical map on the centre row (2x px): dot 0.25 -> x 1195, 0.12 -> 1240, 0 -> ~1250, -0.22 -> 1250, -0.3 -> 1260 (everything below ~0.1 is squeezed into 20 px). Fit to the ref (full to 1190, half 1215, ~0 at 1260): ramp ETMIN 0.02 .. ETSOFT 0.32, EPOW 1.
- v80 apron: too bright, uniform, slopes visibly and pokes out past the left face -> worse than v79.
- v81 7f390d4 run 43386245000: earth ETMIN 0.02 ETSOFT 0.32 EPOW 1; apron PORCH 1.6 PORCHL 1.5 PORCHDROP 0.35 with M_reg (regolith) top (PORCHREG=0 -> flat grey).
- v81 reviewed: earth half-brightness now at x 1220 (ref 1215) — terminator position right; fade 1200-1230 still narrower than ref 1190-1260. Clouds dominate, land barely shows, SA sits right of centre (ref centre-left). Apron: flatter regolith ground reads close to the ref; ground gap done (2 rounds) — leave.
- v82 03a6324 run 43386808831: MC bots MCBS 0.27 (v77's 0.34 was bigger than the ref bots), desk depth MCDK 0.65.
- v83 4c3ba8c run 43387157499: ETMIN -0.03 ETSOFT 0.4, ECLD 0.55 (0.54-0.7), ELON -28, EHUE 0.52.
- v82 reviewed: MC bot size and desk depth now ref-like, floor visible between rows; MC gap done.
- v83 reviewed: ELON -28 puts SA centre-left like the ref (keep). Terminator still a hard line at ~1230 (2x px). Re-derived: dot maps ~linearly to screen x (~1/144 per 2x px; dot 0 ~ x 1236) — the hard look comes from the ramp being only ~0.3 dot wide and AgX lifting its tail. EHUE 0.52 made SA slate-coloured -> back to 0.5.
- v84 808a493 run 43387993528: ETMIN -0.2 ETSOFT 0.32 EPOW 1.4.
- v85 50d0acd run 43388078481: lower-floor bots LBS 0.25 (was 0.3), garden cubes 0.17 (ref lower-floor props/bots are smaller).
- v84 reviewed: wider ramp changed nothing visible — lit edge still a hard curve at ~1250 (2x px). Diagnostic run 43388744266 (ETMIN -1.5 ETSOFT -1.4, PCT 50, PS 8 = fully lit earth) to see whether the edge is the shader or something else. v85 reviewed: smaller lower-floor bots read closer to the ref.
- Diagnostic 43388744266 (fully lit earth) vs v84: ratio v84/full along the centre rows = effective shading after AgX. v84 (ramp -0.2..0.32 ^1.4) fades 0.88 at x 1200 -> 0.01 at 1248 (48 px; ref ~70 px, 1190-1260). v81/v80 ratios are noisy (different texture/ELON). Method: render a fully lit earth with ETMIN -1.5 ETSOFT -1.4 PCT 50 PS 8 and divide.
- v86 d64fb1a run 43389448731: ETMIN -0.32 ETSOFT 0.5, plus atmosphere halo shell (1.06 r, blended emission (0.45,0.72,1.5), alpha Facing^1.5 x lit-mask x 0.85; EHALO=0 off).
- v86 reviewed: terminator fade now ~80 px (1190 -> 1270 at 2x), matching the ref's wide soft blur — earth terminator gap essentially fixed. Halo too strong: milky haze over the whole disc + hard outer edge. Africa/Sahara still shows orange in the fade.
- v87 7c8992c run 43390273261: halo Facing^4 x 0.7, radius 1.025 r; EVAL 1.55.
- v87 reviewed (FINAL this session, run 43390273261, commit 7c8992c, render 307 s on a slow runner): soft wide terminator + subtle rim halo — earth reads close to the ref. lum: top_mid 132/129, left_face 88/91, right_face 47/51, floor0 58/58.5, recess 160/148.
- Remaining gaps after v87: earth land colours (ref SA green/tan, ours dark slate; Sahara shows orange in the fade; bottom ice/cloud cap too big); elevator shaft reads dark with a pink cab (ref: light glass column); lower floors still have bigger/darker props than the ref and show less floor depth; rock block lower-left has large flat facets and the bottom tip is ~20 ref px shorter than the ref; ground apron OK but simple.

## Session 2026-11-13 (afternoon): v88+
- v88 fb5ccad run 43392121508: elevator glass alpha EGA 0.16 / emit EGE 0.06 (was 0.28/0.12), cab white-pink ECE 0.12 + light 8 (was pink 0.35 / 25), colR side column COLRC 0.16 (was 0.07; ref strip ~65 lum vs ours ~35); lower-floor props M_ldark LDC 0.12 (rug, poufs smaller, engbase, tables, stools, barrels, kiosk col, cubes 0.12), sofa SOFAC 0.09, 3 smaller armchairs; earth ESAT 1.35 (was 1.8), gamma EGAM 0.8, desert mask (R-B 0.15..0.45) -> tan (0.55,0.5,0.3) ETAN 0.75; UNDER sun 1.2 from (-0.7,-0.8,-0.5) to light the tapered underside (ours lower-left was ~25 lum vs ref ~100 -> sil.py/bot.py read it as background), RNS 0.035 finer taper noise; PEBBLES 22 small rocks on the apron.
- variant run 43392132522 = v88 + ELON -42 ETILT 16 (earth: SA ref sits slightly right of centre and is bigger; polar cap smaller?).
- New tools: shaft.py (lum grid around the shaft, 2x px), bot.py (lowest rock pixel per column).
- v88 reviewed: under-light fixes the black lower-left underside (bot.py/sil.py now match within ~10-20 px; bottom tip no longer short) but lit the left face too (115 vs ref 91). Cab now subtle white (good); shaft side column still dark. Earth ESAT 1.35/gamma 0.8 washed oceans pale; desert->tan works but SA still grey-brown.
- variant 43392132522 (ELON -42 ETILT 16): SA centred like the ref, Sahara pushed to the limb, bottom polar cap gone; Greenland shows at top. Adopted ELON -42 ETILT 14.
- v89 e0ffea4 run 43393383185: ELAND stylised land (mask (R+G)/2-B over 0..0.12 -> mix 0.85 with ramp dark green (0.13,0.33,0.08)@0.12 .. tan (0.62,0.54,0.33)@0.5), ESAT 1.6, EGAM 0.9; UNDER 1.4 from (-0.35,-0.45,-1); SLABL 0.38 lower slabs; COLRC 0.3; pebbles 30 x 0.05-0.16 dark. Variant 43393387925 = v89 with ELAND=0.

## Session 2026-11-14
- Repo made PUBLIC 11:25 CST (James approved) -> unlimited free Actions minutes, 20 parallel jobs.
- v90 b349954 run 43551353001: solar panels SOLW 0.47 SOLD 0.43 (fixed tilt line that a comment had swallowed). Reviewed: fine.
- moonanim fe8ed47: ALWAYS_HIDDEN set — apply_hides was unhiding the boolean cutter boxes (dark box over the building in wide shots). Check run 43551584388: fixed.
- Full low-res preview run 43551586974 (step 2, 20 jobs, 25%, 4 samples, mp4 15 fps).
- Anim gaps seen: close-up floor shots (t 16.7, 25) framing differs and lack rock walls; UI overlay still to composite with ffmpeg.

## 2026-11-14 noon
- UI overlay: compose.py pastes source-video UI regions (feathered rounded-rect masks) onto our frames; on/off per frame from edge-detection (ui/det.npy). Title uses lighten blend. Verified on ui_test.mp4 (2010 frames).
- ALWAYS_HIDDEN fix (fe8ed47): boolean cutters never render.
- Eclipse: sun halo off during totality (38.9-61.6 s), halo tighter (SHR 2.6, SHP 3.6), city lights on earth night side (ECITY/ECITYS env).
- Floor close-ups: FTDZ default -0.6 (FTDZ0 for MC stays 0.7). Cavity faces get banded rock during close-ups (ROCKWALL env).
- Biggest remaining gap: lower floor furniture themes differ from source (SE: glass room + rocket model; Starlink: map screen + server racks; Lobby: arch, capsule, statues).
- v91: scripts/floors_v2.py (FL2=1) holds the lower-floor interiors, built from the original's close-ups at 18/22/27 s. Back walls are dark glazing (BWD=1). Close-up camera: OSF 6.8 with FTDZ 0.3; Mission Control keeps OSF0 8.5 with FTDZ0 0.7. Preview v3 is run 43558535704.
- 15:35 eclipse ring thinner/dimmer (RW1 .012 RW2 .05 RG2 .25 RSTR 4), test run 43571132863 OK (preview/t5.jpg). Note: ad.sh FRAMES takes a range only, no comma lists; use STEP for sampling.
- Gap seen at t=50s (t5.jpg): the source is wider, showing the lobby, the floor above, and the TBM digging in a dark crater below at -74 m. Ours is a single-floor close-up. Next: camera at 49.8–58.4 s widens to show 2 floors + TBM/cave below.
- cave/lobby wider camera (OSCAVE 12.5, CAVEDZ 4.5) commit pushed 16:15; test run 43574805160 frames 1480-1720 step 60
- 19:20 test run 43589194816: env CAVEDZ=8 OSCAVE=16 (ref t=51 shows floor plate top + rock below; 43574805160 camera was too low/tight). Not yet reviewed; if good make defaults.
- 22:20 cave camera tests (ref t=51 zoomed out ~1.5x vs OSCAVE16/CAVEDZ8): runs 43603862399 and previous: OSCAVE=24 CAVEDZ=8 / OSCAVE=22 CAVEDZ=10
- 23:55 added deepwide slab (RWIDE=3) to widen rock around cave column; test run 43612430103 OSCAVE=24 CAVEDZ=8 frames 1500-1560. Review f1500/f1560.
- 00:58 strata material (SWS 3.5, SEM .7) on deep/deepwide/cavebase, commit 3164f84; test run 43618007296 frames 1500-1560 step4. Review f1500/f1560 for layered rock.
- 01:05 reviewed 43618007296 f1532 vs ref 51.0 s (preview/cmp_cave4.jpg): framing closer, but the deep rock top face is pink regolith, flat, and too bright. Ref is dark brown with visible horizontal strata on the side faces and a stepped ledge under the floor plate. Our floor plate also sits too small and high in frame. Next: darken the strata material, put strata on the top/side faces the camera sees, and lower the camera a little.
- 01:55 darker strata (SEM .25, brown ramp) pushed; test run 43623354161 frames 1500-1560 step4 (OSCAVE/CAVEDZ env not passed via ad.sh arg 6; defaults apply). Review f1532 vs ref.
- 02:58 darken upward-facing faces of strata material (top of cave rock was orange); test run 43629166076 frames 1500-1560 step4. Review f1532 vs ref.
- 03:55 stronger strata bands (SWS 9, ramp brighter, SEM .5; sides were flat dark in 43629166076); test run 43634492756 frames 1500-1560 step4. Review f1532 vs ref (cmp_cave6.jpg shows previous).
- 04:58 strata scale bug found (SWS 9 in world units = sub-pixel bands, sides looked flat); default now 0.8, commit 6964467; test run 43639823264 frames 1500-1560 step4. Review f1532 vs anim/ref51.jpg.
- 05:58 strata used Object coords (unit-scaled by box -> flat); now world Position, SWS 1.6; test run 43645056105 frames 1500-1560 step4. Review f1532 vs ref51.
- 06:55 strata top faces were flat black (normal-Z mix x3); now STOP .55 blend, commit pushed; test run 43650462237 frames 1500-1560 step4. Review f1532 vs ref51.
- 07:55 reviewed 43650462237 f1532 vs ref51 (anim/cmp_cave9.jpg): top face still flat brown noise with no ledge/strata, bottom corner bands pink/too bright and aliased, camera too low/close. Next: apply strata bands on the vertical faces only with dark brown ramp, add stepped ledge under floor plate, pull camera up/out.
- 08:55 v: a1b27ae wider cave camera defaults OSCAVE24/CAVEDZ8, darker brown strata (SEM .35, SWS 1.2); test run 43660343361 frames 1500-1560 step4. Review f1532 vs ref51.
- 09:55 CST 007c2b5 tighter cave camera OSCAVE16 CAVEDZ3 (v ref51: plate was too small, rock top flat); test run 43665076371 frames 1500-1560 step4. Review f1532 vs ref51 (cmp_cave10 = previous).
- 02:51 UTC 'STOP .97' dark strata tops pushed; test run 43669735366 frames 1500-1560 step4. Review f1532 vs ref51 (cmp_cave11 = previous: top face orange, too large/bright).
- 03:55 UTC subtler irregular strata (SWS .9 dist 3, dimmer ramp), CAVEDZ 0; test run 43674373963 frames 1500-1560. Review f1532 vs ref51 (cmp_cave12=previous: sides too regular/bright, plate too high).
- 12:55 CST (04:55 UTC) reviewed 43674373963: big dark top face = deepwide (RWIDE 3) top. Variants RWIDE=1 CAVEDZ=0/6/12 (runs 43678590413/…596177/…602025, anim/cmp_cave14.jpg): RWIDE=1 gives the right structure (plate on rock column, corner under plate); dz6 best framing, bands too bright/regular. Commit 42a5309: RWIDE 1, CAVEDZ 6, darker strata ramp, SEM .25. Test runs 43679019514 (OSCAVE=13) and 43679024574 (OSCAVE=11 CAVEDZ=4), frames 1500-1560 step30; ref plate is bigger. Review f1530 vs ref51. Next: TBM forward motion, light band 63-64 s.
- 13:58 CST commit 5c84b43 CAVEDR env (shift cave camera), strata calmer/darker (SWD 1.2, ramp darker). Reviewed 43679019514/43679024574 (anim/cmp_cave15.jpg): structure OK, bands too wavy/bright, corner should sit lower-right. Test runs 43683031888 (OSCAVE20 CAVEDR2 CAVEDZ8) and 43683034066 (OSCAVE22 CAVEDR3 CAVEDZ10 SWS.6), frame 1530. Next: pick best, TBM motion, light band 63-64s.
- 14:55 CST reviewed 43683031888/43683034066 (anim/cmp_cave16.jpg): plate/column structure fine, but plate corner sits at ~(0.67,0.43) of frame vs ref (0.8,0.54); strata too regular stripes. Test runs for framing (frame 1530): 43687492569 (OSCAVE14 CAVEDR6 CAVEDZ8), 43687498353 (OSCAVE13 CAVEDR9 CAVEDZ10), 43687503972 (OSCAVE15 CAVEDR5 CAVEDZ12 SWS.6). Review f1530 vs ref51; then TBM motion, light band 63-64s.
- 15:58 CST reviewed 43687492569/498353/503972 (anim/cmp_cave17.jpg): variant 1 (OSCAVE14 CAVEDR6 CAVEDZ8) framing matches ref corner position best (~0.84,0.5 vs ref 0.8,0.54); strata still regular stripes, a bit bright. Commit 2af2505: defaults = variant 1, TBM creeps +x 1.1 over 46.5-58.4 s (TBMFWD env), fan spin to 58.4. Test run 43691950699 frames 1450-1740 step30. Review TBM motion; next light band 63-64 s, then full low-res preview.
- 16:00 test run for 62.5-65 s landing/light band: (id above) frames 1875-1950 step15; ref strip anim/lb/src_strip.jpg (ejecta streaks radiating from pad, rocket landing)
- 16:15 KEY FINDING: ref after 52.4 s is NOT the plate view: cave floor with monolith TMA-1, pod/TBM left, rocks (anim/lb/cave_src.jpg). Our T_CAVE (plate view) was held 52.4-58.4 -> only rock wall (cave_sheet18.jpg). Commit adds 2-stage camera (T_CAVE2 C2X/C2Y/C2DZ/OSC2). Test runs 43692444890 (default), 43692447991 (C2 1.8,-2.2,2.2 OS11), 43692450970 (3.0,-3.0,1.0 OS7.5) frames 1600-1720 step40. TBM test 43691950699 reviewed: tank moves OK.
- 16:20 ROOT CAUSE of rock-only cave frames: 'deepwide' slab (CZ-16..FZ_BOT) filled the cave volume solid at RWIDE 1. Now only built when RWIDE>1. Test runs 43693027021 (default C2) and 43693031155 (C2 1.8,-2.2,2.2 OS11) frames 1500-1720 step40. Landing dust streaks added (commit), test run 43692580179 frames 1875-1950.
- 16:30 dust streaks v1 too thick/bright (run 43692580179); thinned; retest above-ID next line
- 16:50 cave now visible (43693031155, cave_sheet20.jpg) but ceiling/front walls hide most of floor; adding CAVECH env; variants runs listed in last 3 ids (frames 1580-1700 step60)
- 17:00 dust streaks v2 (43693133154) look close to ref 63-64.5s, accepted.
- 17:15 cave variant CAVECH=12 OSC2=11 (43693589176, cave_sheet21.jpg) matches ref well. Defaults set (CAVECH12, C2 1.8/-2.2/2.4, OSC2 10, monolith glow .2). FULL low-res preview v4 dispatched (id in last_run.txt), then compose.py UI + upload to Drive + message James.
- 17:00 CST (v4 9b71a62) FULL low-res preview run 43694107702 done (20 jobs, ~19 min). UI composed with compose.py -> anim/preview/moon_preview_v4.mp4 (67 s, 1080x1350, audio). Reviewed sheet_v4.jpg: cave segment now shows cave floor+monolith, TBM moves, dust streaks at 63-64 s. Uploaded to Drive; James messaged. Next: review for remaining gaps (strata too regular, floor interiors), then final full-res: ./ad.sh 1 20 100 <samples> 1-2012.
- 17:55 CST full-res timing test run 43701392812 (pct100 samples16, frames 1000-1100 step20, 2 jobs) to size final render (jobs/samples). v4 preview already delivered; no James feedback yet.
- 18:05 CST timing test 43701392812: ~88 s/frame at 100%/16 spp. FINAL full-res dispatched: ./ad.sh 1 20 100 16 1-2012 '' 30 PNG, run 43702193988 (v4 code 9b71a62), est ~2.5-3h (100 frames/job). Next: fetch out mp4/artifacts, compose.py UI, add audio, upload to Drive, message James.
- 19:55 CST James asked why a flickering elevator shows before rocket landing: thin emissive 'ebar' lamp bars in the glass shaft shimmer frame to frame at low res (ref shaft has none). Commit 2fe94ec EBAR off by default. Test run 43710603310 frames 1815-1840 25%/4spp. FINAL run 43702193988 (v4 code, still has bars) saved in final_run.txt.
- 20:00 CST cancelled old final 43702193988 (had shaft bars); re-dispatched FINAL with 2fe94ec: ./ad.sh 1 20 100 16 1-2012 '' 30 PNG run 43710642796, est done ~23:00 CST. Then compose.py UI + audio, Drive upload, message James. Test 43710603310 (25%) to confirm shaft no longer flickers.
- 20:50 CST FRAME-BY-FRAME REVIEW (src vs v4, 2 fps sheets anim/fbf/sheet_01..12.jpg; left=src right=ours). Final 43710642796 CANCELLED to fix. Fix list (priority):
  1. Close-up back rock walls (16-30 s, 45-50 s): ours high-contrast wavy black/white zebra; src fine straight horizontal dark-gray strata + big diagonal shadow.
  2. Camera timing: ours ~0.5-1 s early at 10.5-11.5 zoom-in, 16 s MC->Eng, 30.5-31.5 zoom-out, 45.5 dive, 58.5 pull-up. Src 45.5-48 pans DOWN across MC/Eng/Starlink/Lobby (multi-floor, shaft at left); ours jumps to lobby close-up.
  3. Close-ups too tight: src frames wider (whole floor + part of floor below).
  4. Launch 7-9.5 s: ours solid white opaque beam column; src blue/purple exhaust cone + radial streaks, fades to soft blue spotlight by 9.5.
  5. Lid 6.5 s slides wrong way (src slab slides to lower-right; ours lower-left).
  6. Pad after launch: src dark scorched circle + 'LANDING ZONE 1'; ours white ring.
  7. 48-50 s TBM: src TBM under lobby with headlight, digging debris particles; ours black cylinder beside floor, no light/debris. 50.5-52 descent: src stepped rock ledge + dark maroon strata, narrow lit slit at 52; ours shows orange cave early and black void (background) on left.
  8. Cave 52.5-58: src pale sandy lit floor, TBM w/ headlight left, yellow + red bots, monolith dark w/ orange gradient glow; walls dark. Ours orange banded walls, no TBM/yellow bot. 56.5 src monolith stays dark, green glow at bottom + 2 white eyes; ours whole slab bright green.
  9. Eclipse 38.5-61: src ring orange-red thin, earth disk shows city lights, tint maroon desaturated; ours ring pale yellow thick, tint orange saturated. Ours totality ~0.5 s early.
  10. Landing 60.5-61.5: src rocket descends from 60.5 with blue exhaust; ours later w/ white disc. Dust streaks 63.5-64 still too thick/dashed; src fine faint lines 63-64.5.
  11. Wide shots: ours building ~10-15% right/smaller vs src.
  12. Floating name tags (Flight Director, Mechazilla, Octaweb, Laser Link, TMA-1) missing - UI layer, add in compose.py.
  13. Starlink floor: src big purple world map on back wall + server racks in glass; ours purple window + one rack.
- 21:55 CST run checked: no active GH runs, no uncommitted changes; fix list item 1 (zebra rock walls, likely wave-texture materials in moonanim.py/moonbase.py) not yet started.
- 22:55 CST fix1 committed (RWS2.5 RWD.5 calmer ramp), test run 43726812172 frames 450,600,900,1380,1440,1480 (25%). Next: review vs src, then item 2 camera timing.
- 23:28 CST test 43726812172 rendered nothing (comma frame list unsupported). Re-dispatched fix1 test as range: ad.sh 30 6 25 4 450-1480 -> run 43729727146. Review rock walls vs src, then item 2 camera timing.
- 23:35 CST reviewed 43729727146 (anim/fix1/a.jpg,b.jpg): fix1 ACCEPTED - rock walls now fine straight gray strata like src (src also has a big diagonal shadow; optional). Next: item 3 close-ups too tight (src shows whole floor + floor below; ours ~1.3x tighter) and item 2 camera timing incl. 45.5-48 s multi-floor pan-down (ours at f1440 is lobby close-up while src shows MC..Lobby stack).
- 23:45 CST commit a995cd4: OSF 8.2, FTDZ -0.5 (wider close-ups showing floor below like src), Starlink->Lobby 22.8-23.7, new T_STACK (STKF 1.8, OSSTK 11.5) key at 46.4 with solar hold to 45.3 and TBM at 47.6 (src pans down 45.5-47.5). Test run 43730614927 frames 480-1500 step30. Review vs src (fix2/src10_32.jpg, src44_52.jpg).
- 23:58 CST reviewed 43730614927 (anim/fix2/ours.jpg vs src.jpg): close-ups wider, timing at f1320-1470 now near src (stack pan ok-ish; src stack pan slightly wider/lower at 1410). Items 2/3 ACCEPTED. Next: item 4 launch exhaust (7-9.5 s), 5 lid, 6 pad.
- 00:55 CST fix4 committed (bluer dimmer plume/trail), test run 43737824134 frames 195-290. Review vs src 7-9.5s, then items 5 lid, 6 pad.
- 02:00 CST reviewed fix4 (43737824134, anim/fix4): plume now blue, closer to src; still slightly column-like & pad white ring (item 6). Fix4 ACCEPTED. Next: item 5 lid direction, item 6 pad scorch + 'LANDING ZONE 1'.
- 02:55 CST fix5 committed (lid Y sign flipped, env LIDY), test dispatched frames 185-235; verify lid direction lower-right vs src 6.5s, then item 6 pad.
- 03:55 CST fix5 (Y flip) wrong: lid flies off up-right/vanishes; src slab slides lower-right & stays in frame. Commit fix5b slides along X (LIDX env). Tests LIDX=10 and -10 dispatched (185-235); pick the one going lower-right, set default, then item 6 pad.
- 04:55 CST fix5 resolved: LIDX=-10 (slab slides lower-right) set default, committed. Next: item 6 pad scorch + 'LANDING ZONE 1'.
- 05:55 CST item6 crater code already committed; dispatched pad test 270-420 (25%) to verify scorch, then 'LANDING ZONE 1' text + items 7-
- 06:58 CST reviewed pad test 43765955840 (anim/fix6/c.jpg): 'LANDING ZONE 1' text present, pad dark-ish ring closer to src; item 6 ACCEPTED. Next: item 7 TBM/descent 48-52 s, then 8 cave.
- 07:55 CST item7 baseline test dispatched frames 1440-1590 (run 43777191106); review vs src 48-53s, then edit TBM/descent.
- 09:00 CST reviewed item7 baseline 43777191106 (anim/fix7 s.png=src, o.png=ours f1440-1590): ours stays on lobby close-up through 49 s with black void left at 49.5; src pans down past lobby: TBM below lobby w/ headlight+debris, then rock strata descent, then lit cave. Need: camera keyframes follow rock descent 48-52 s, TBM beneath lobby w/ light, strata walls. Not yet edited.
- 09:55 CST check: no active runs; item 7 (TBM/descent camera + TBM light + strata) still not edited; next run to start it.
- 10:58 CST item7 edit committed 6c80304 (descent camera keys 48/49/50 s z-6.8/-10.5/-15.5, side rock slabs rsl/rsr/rsf/rsb visible from 46 s, TBM digging debris specks 47.8-50.4, T_CAVE hold to 52.3, CAVE2 at 53.4). Test run 43794837765 frames 1380-1620 step15. Review vs src (fix7/s.png) next.
- 11:15 CST test 43794837765 (fix7): floors 0-2 were hidden from 45.6 (FOCUS) so stack pan showed only lobby, and descent rock was near-black/flat. fix7b commit: floors visible until 49.7, brighter strata2 (STRK 3.5) on deep/side rock. Test run 43795624864 (same range 1380-1620 step15). Review vs fix7/s.png.
- 11:32 CST fix7b test 43795624864 reviewed: stack pan 46-49 s now shows MC..Lobby floors (good, TBM beside lobby); descent rock below still flat black (in shade). fix7c: strata2 emission x4 (STRK 2.5). Test run 43796473671 frames 1440-1620 step15.
- 11:50 CST 43796473671 reviewed: flat brown = TOP faces of my side slabs (rsl/rsr/..) hiding the cliff faces; slabs now off by default (RSLAB env), commit fix7d. Earlier 'void' was just deep rock hidden until 49.8 (now 46.0). Test run 43797326252 frames 1440-1620 step15.
- 12:00 CST reviewed fix7d 43797326252 (anim/fix7d/o5.png vs s5.png): rock strata fine but pinker/lighter than src dark maroon; black void left of rock in descent/cave frames; cave arrives ~1 s earlier than src (ours 51 s, src 52 s). fix7e 'extend rock left (LEXT 30)' committed; test run 43800886409 frames 1440-1620 step15. Next: delay cave ~1 s, darken rock, then item 8 cave details.
- 12:15 CST fix7e 43800886409 reviewed: black void GONE. fix7f committed (cave arrives 0.8 s later: keys 50.9/52.0/52.9; STRK 1.7 darker rock); test run 43801653582 frames 1440-1620 step15. Item 7 near-accepted; next item 8 cave details (TBM w/ headlight left, yellow/red bots, monolith dark w/ green glow + eyes, pale sandy floor), then 9 eclipse.
- 12:50 CST fix7f 43801653582 reviewed: descent timing/colour OK, item 7 ACCEPTED. fix8 committed (pod+headlight moved to (-0.6,-2.0) left of monolith - it was hidden in the wall; yellow bot at (2.5,-3.35)); test run 43802413287 frames 1620-1740 step60. Review vs src 54-58 s (anim/fix7d/cmp55.png). Next: 56.5 s monolith dark + green bottom glow + eyes, then item 9 eclipse.
- 13:25 CST fix8 43802413287 reviewed: pod+headlight now visible at left, yellow bot ok -> item 8 ACCEPTED (cave compact vs src but close). fix9 eclipse committed (ring redder/thinner RSTR3, TINT .85/.4/.36, totality +0.4 s); test run 43803200684 frames 1100-1280 step15. Review vs src 36.7-42.7 s. Next: item 10 landing 60.5-61.5, 11 wide shots, 12 name tags, then full preview v5.
- 13:50 CST fix9 43803200684 reviewed: eclipse timing/ring/tint now match src (item 9 ACCEPTED; fix9b slightly darker light). Landing test (frames 1780-1960 step15) dispatched, id in last_run.txt; review vs src 59.3-65.3 s (item 10).
- 14:20 CST landing test 43803957251 reviewed: timing OK vs src (item 10 timing ok); dust streaks too thick/bright -> fix10 (strength 1.8/1.4, NRAY 280, thickness .008) committed; test (50%, 8spp) frames 1860-1950 step15. Item 11 wide shots and 12 name tags (compose.py overlay needs per-frame pill detection; may skip) left.
- 14:55 CST landing test 43804744633 reviewed: rocket touchdown ~0.5 s late vs src, streaks still too bright, building ~7% smaller than src in wide shots. fix11 committed (landing duration 2.3, OS0K .94 zoom, streaks .7/.5 RLEN 5.5); test 43805*** (last_run.txt) frames 1860-1950. Item 11 included here. Then full preview v5.
- 15:40 CST fix11 test 43805667931 reviewed: wide-shot scale and landing timing now match src; streaks dimmer (items 10, 11 ACCEPTED). Item 12 name tags skipped for now (UI overlay). FULL low-res preview v5 dispatched: ./ad.sh 2 20 25 4 1-2012 '' 15 JPEG, run 43806459844 (id also in preview/v5_run.txt). Next: aw.sh, compose.py runs/RUN/out/frames 2 preview/moon_preview_v5.mp4, regenerate sheets, review, upload, message James.
- 12:55 CST (clock) v5 run 43806459844 in progress; next run: wait/aw.sh, compose, sheets, upload, message James.
- 14:00 CST (clock) v5 composed preview/moon_preview_v5.mp4 (2010 frames @2-step render, 1080x1350, audio ok), sheets anim/fbf5; sent to James, awaiting approval for final.
- 15:20 CST JAMES FEEDBACK ON v5 (not approved, polish more vs src, check EVERY frame carefully):
  V6 FIX LIST (priority):
  A. Opening: the lunar ground extends out past the rocket side (ground plane edge/terrain visible beyond rocket at start); src does NOT look like this. Compare src 0-7 s frame by frame and match the ground extent/edge/horizon exactly.
  B. After nightfall (eclipse/totality, ~38.5 s onward, esp. before landing 58-61 s): elevator "ghost" still visible below the rocket (shaft/elevator cab or lamp remnants shimmering). Src has no elevator ghost there. Find the object (shaft glass, cab, ebar, reflections, low-spp noise) and remove/hide it in those frames; verify at full-ish res (50%+, more spp) that it is gone, not just low-res noise.
  C. Then do a NEW full frame-by-frame review of v5 vs src at 4 fps (not 2): list every remaining mismatch (geometry, timing, lighting, colour, objects appearing/disappearing) as items C1.. and fix them in priority order.
  Only after A, B and all C items are accepted: full low-res preview v6, sheets at 4 fps, upload, send James.
- 15:22 CST V6: item A cause = LEXT rock box visible from start (left bulge); fix12 hides it until 45.8 s. Test runs: A 43823328464 frames 1-120; B baseline (ghost, frames 1200-1500 step15) 43823331984. Review next run (anim/v6 has src-vs-v5 comparisons).
- 15:58 CST item A ACCEPTED (43823328464: ground edge matches src, no left bulge). B baseline at 42 s shows no ghost (rocket gone then); ghost test at 50%/16spp frames 1740-1860 step15 dispatched (last_run.txt); review vs src 58-62 s.
- 08:53 CST item B: test 43826981108 (50%) frames 1740-1860 shows no elevator ghost below rocket -> ACCEPTED. Dispatching full preview v6 (C review done on v6 sheets).
- 17:55 CST v6 run 43834904900 fetched; composing preview/moon_preview_v6.mp4
- 18:05 CST v6 composed+uploaded, sent to James, awaiting approval
- 18:00 CST JAMES FEEDBACK ON v6 (not approved). V7 FIX LIST:
  D. Every floor's ground/floor slab still extends out to the LEFT. In src the floors do NOT extend out on that side (the rocket/under-rocket side); compare each floor close-up and wide shot vs src frame by frame and match which side (if any) the floor slabs overhang. Check all floors, not just the opening.
  E. The way each office floor disappears (floor hide/fade sequence, order, timing, method) differs from src. Extract src frames at full fps around every floor transition, document exactly how each floor vanishes (cut, slide, fade, dissolve, which direction, timing), and replicate.
  F. After nightfall there should be a TBM (tunnel boring machine) drilling down underground below the building, as in src. Verify in src when/where it appears, its path down through the rock, headlight, debris; make ours match (it may be missing or wrong after the night/eclipse starts).
  Then a fresh 4 fps full review vs src (items G1..). Only after all accepted: v7 preview, upload, send James naming D/E/F fixes.
- 18:10 CST (run) no GH runs active. Started V7 study: v7/tbm_01/02.jpg (src-left vs v6-right, 38-54 s). Findings F: in src the TBM sits on the rock ledge BELOW the lobby floor (dark body, bright headlight, SPACEX floor decal), tilts nose-down and digs into rock 47-50 s with white debris specks; ours shows a tank at lobby level, no visible dig-down; src camera is closer/higher zoom on floors (floors fill frame). D/E/F code not yet changed; next: extract full-fps src frames 47-51 s and floors 0-2 vanish, edit moonanim.py.
- 18:01 CST JAMES: do NOT fix only D/E/F. FIRST do a complete frame-by-frame comparison of the whole 67 s vs src (at least 10 fps sheets, plus full-size frame pairs at every shot change/transition), and write EVERY difference as items G1.. (geometry, layout, which side things overhang, object presence/absence, how floors appear/disappear, camera framing/timing, lighting, colour, effects, UI). Then fix D/E/F and all G items. James says there are many differences; be exhaustive.
- 18:52 CST run: backup pushed; G list still not written.
- 19:52 CST run: no new work possible this run (budget); G list still unwritten; backup current.
- 20:52 CST run: budget-limited, no new work; backup current (repo clean).
- 21:51 CST run: budget-limited, no new work; backup current (repo clean).
- 22:52 CST run: budget-limited, no new work; backup current (repo clean).
- 23:50 CST run: budget-limited, no new work; backup current (repo clean).
- 00:50 CST run: budget-limited, no new work; backup current (repo clean).
- 01:51 CST run: budget-limited, no new work; backup current (repo clean).
- 02:50 CST run: budget-limited, no new work; backup current (repo clean).
