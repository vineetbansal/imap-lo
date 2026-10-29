;
; $Id: loadaltct.pro 6598 2010-03-18 10:46:40Z nathanISOC $
;
; pro loadaltct
; pro canonical_colortab_x
; pro recover_colortable_x
; pro make_greyscale_color
; pro make_saturated_color
; pro resample_colormap
;
; Since IDL's colortables suck, we need to make our own.
;

;
; In setup_colormap, this one line hook:
;
; if (ips.ct ge 0) then loadct,ips.ct,/silent else loadaltct,ips
;
pro loadaltct,              $
    ips                       ; IN: common isoc plotting structure

    if (ips.ctsilent eq 0) then print,"loadaltct with ",ips.ct

    c = bytarr(256,3)
    case ips.ct of
      -8:   load_maher_diff_redblue
      -7:   make_saturated_color,c,ho=120.0,silent=ips.ctsilent
      -6:   canonical_colortab_x,c,ct=33,silent=ips.ctsilent
      -5:   canonical_colortab_x,c,ct=27,silent=ips.ctsilent
      -4:   make_saturated_color,c,ho=85.0,silent=ips.ctsilent
      -3:   make_saturated_color,c,ho=70.0,silent=ips.ctsilent
      -2:   make_greyscale_color,c,silent=ips.ctsilent
      -1:   recover_colortable_x,c,ct=0,silent=ips.ctsilent
      else: recover_colortable_x,c,ct=ips.ct,silent=ips.ctsilent
    endcase
    if (ips.ctstrch[0] ge 1 and ips.ctstrch[1] le ips.ctop+1) then $
	resample_colormap,c,ips.ctstrch[0],ips.ctstrch[1],ips.ctop,ips.ctsilent
    tvlct,c,0
end

pro canonical_colortab_x,   $
    c,                      $ ; IN/OUT: bytarr(256,3) of color values
    ct=ct,                  $ ; IN: color table to load
    silent=silent

    loadct,ct,/silent
    tvlct,c,/get
    case ct of
      27: c[1,*] = c[2,*] / 2
      else:
    endcase
    ; this is customary
    c[255,*] = 255
    c[0,*] = 0
    if (silent eq 0) then print,"recover_colortable_x with ",ct
end

pro recover_colortable_x,   $
    c,                      $ ; IN/OUT: bytarr(256,3) of color values
    ct=ct,                  $ ; IN: color table to load
    silent=silent

    loadct,ct,/silent
    tvlct,c,/get
    if (silent eq 0) then print,"recover_colortable_x with ",ct
end

pro make_greyscale_color,   $
    c,			    $ ; IN/OUT: bytarr(256,3) of color values
    silent=silent

    x = indgen(256)
    c[*,0] = x
    c[*,1] = x
    c[*,2] = x
    if (silent eq 0) then print,"make_greyscale_color"
end

pro make_saturated_color,   $
    c,			    $ ; IN/OUT: bytarr(256,3) of color values
    ho=ho,                  $ ; IN: lowest hue to use
    silent=silent
 
    h = fltarr(256)
    s = fltarr(256)
    v = fltarr(256)
    r = bytarr(256)
    g = bytarr(256)
    b = bytarr(256)
    h = indgen(256)
    ; h[*] = h[*] - 255 + 359
    h[*] = ho + (360.0 - ho) * (h[*] / 256.0)
    s[*] = 1.0
    v[*] = 1.0
    color_convert, h,s,v, r,g,b, /HSV_RGB
    c[*,0] = r
    c[*,1] = b
    c[*,2] = g
    ; this is customary
    c[255,*] = 255
    c[0,*] = 0
    if (silent eq 0) then print,"make_saturated_color, lowest hue is ",ho
end

;
; resample the colors to only use a subset: 1..(ctop+1)
;
pro resample_colormap,      $
    c,                      $ ; IN/OUT: bytarr(256,3) of color values
    lcol,                   $ ; IN: Lowest color to keep (>= 1)
    hcol,                   $ ; IN: Highest color to keep (<= ctop+1)
    ctop,                   $ ; IN: top minus one
    silent                    ; whether to comment

    oldc = bytarr(256,3)
    newind = fix(1.0*lcol + (1.0*hcol-1.0*lcol)*indgen(ctop+1)/(ctop*1.0))
    c[1 + indgen(ctop+1),*] = c[newind,*]
    if (silent eq 0) then print,"resample_colormap from ",lcol,"..",hcol
end

;
pro load_maher_diff_redblue  

rvec = [ 70,73,69,65,57,53,49,41,37,33,25 $
         ,21,17,9,5,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,0,0,0,0   $
         ,0,0,0,0,0,0,0,1,2,0,0   $
         ,60,63,65,66,69,70,72,75,76,79,81 $
         ,82,85,86,88,91,92,94,97,98,101,102 $
         ,104,107,108,110,113,114,117,118,120,123,124 $
         ,126,128,130,131,134,136,139,140,141,144,146 $
         ,147,150,152,155,156,157,160,162,163,166,168 $
         ,169,172,173,176,178,179,182,184,185,188,189 $
         ,192,194,195,198,199,201,204,205,207,210,211 $
         ,214,215,217,220,221,223,226,227,230,231,233 $
         ,236,237,239,241,243,244,247,249,252,253,255 $
         ,255,255,255,255,255,255,255,255,255,255,255 $
         ,255,255,255,255,255,255,255,255,255,255,255 $
         ,255,255,255 ]

gvec = [ 180,183,182,180,177,175,174,170,169,167,164,162 $
         ,161,158,156,154,151,150,146,145,143,140,138,137 $
         ,134,132,130,127,126,124,121,119,116,114,113,110 $
         ,108,106,103,102,100,97,95,94,90,89,85,84 $
         ,82,79,77,76,73,71,69,66,65,63,60,58 $
         ,55,53,52,49,47,45,42,41,39,36,34,33 $
         ,29,28,25,23,21,18,17,15,12,10,9,5 $
         ,4,2,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,1,2,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,0,0 $
         ,0,0,0,0,0,0,0,0,0,0,3,5 $
         ,7,11,13,15,18,20,24,26,28,32,34,35 $
         ,39,41,43,47,49,52,54,56,60,62,64,68 $
         ,69,73,75,77,81,83,85,88,90,92,96,98 $
         ,102,103,105,109,111,113,117,119,122,124,126,130 $
         ,132,134,137,139,141,145,147,151,153,154,158,160 $
         ,162,166,168,170 ]

bvec = [255,255,255,255,255,255,255,255,255,255,255,255 $
        ,255,255,255,255,255,255,253,252,250,248,246,245 $
        ,242,241,240,237,236,234,231,230,227,226,225,222 $
        ,221,219,217,215,214,211,210,208,206,204,202,200 $
        ,199,196,195,193,191,189,188,185,184,183,180,179 $
        ,176,174,173,170,169,168,165,164,162,160,158,157 $
        ,154,153,150,149,147,145,143,142,139,138,136,134 $
        ,132,131,128,127,124,123,122,119,118,116,113,112 $
        ,111,108,107,105,103,101,99,97,96,93,92,90 $
        ,88,86,85,82,81,80,77,75,73,71,70,67 $
        ,66,65,62,61,0,0,0,0,1,2,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,0,0,0,0,0,0,0,0,0,0,0 $
        ,0,3,11,15,19,27,31,39,43,47,54,58 $
        ,62,70,74,78 ]

tvlct, rvec, gvec, bvec
return
end

;
; eof
;
