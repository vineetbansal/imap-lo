;
; $Id: make_jpeg_from_x.pro 5735 2009-10-20 22:07:20Z gbc $
;
; pro make_jpeg_from_x
; pro make_png_from_x
; pro make_gif_from_xz
; pro make_png_from_xz
; pro make_bmp_from_xz
; pro give_credit_where_due
;
; This procedure assumes we have an X display open, and saves it
; as a jpeg file; this only works from x
;
pro make_jpeg_from_x,   $
	outfile          ; output filename

	if (strpos(outfile,'jpg') < 0 and  $
	    strpos(outfile,'jpeg') < 0 and $
	    strpos(outfile,'JPG') < 0 and  $
	    strpos(outfile,'JPEG') < 0) then outfile=outfile + '.jpg'

	give_credit_where_due
	image = tvrd(0,0,!d.x_size,!d.y_size,true=3)
	write_jpeg,outfile,image,quality=100,true=3
end

;
; ...save it as a png file, this only works from x
;
pro make_png_from_x,    $
	outfile          ; output filename

	if (strpos(outfile,'png') < 0 and  $
	    strpos(outfile,'PNG') < 0) then outfile=outfile + '.png'

	give_credit_where_due
	image = tvrd(0,0,!d.x_size,!d.y_size,true=1)
	write_png,outfile,image
end

;
; ...save it as a gif file from either x or z
;
pro make_gif_from_xz,   $
	outfile          ; output filename

	if (strpos(outfile,'gif') < 0 and  $
	    strpos(outfile,'GIF') < 0) then outfile=outfile + '.gif'

	give_credit_where_due
	tvlct,rc,gc,bc,/get
	image = tvrd()
	write_gif,outfile,image,rc,gc,bc
end

;
;
; ...save it as a png file from either x or z
;
pro make_png_from_xz,   $
	outfile          ; output filename

	if (strpos(outfile,'png') < 0 and  $
	    strpos(outfile,'PNG') < 0) then outfile=outfile + '.png'

	give_credit_where_due
	tvlct,rc,gc,bc,/get
	image = tvrd()
	write_png,outfile,image,rc,gc,bc
end

;
; ...save it as a bmp fil from either x or z
;
pro make_bmp_from_xz,   $
	outfile          ; output filename

	if (strpos(outfile,'bmp') < 0 and  $
	    strpos(outfile,'BMP') < 0) then outfile=outfile + '.bmp'

	give_credit_where_due
	tvlct,rc,gc,bc,/get
	image = tvrd()
	write_bmp,outfile,image,rc,gc,bc
end

;
; This is driven by an environment variable because:
;  don't want to break regression tests
;  the existing scripts don't pass arguments to the make_* pros
;
; IBEX_PLOT_LABEL=,top-left,top-mid,top-right,bot-left,bot-mid,bot-right
;
; This version doesn't mess with fonts, since we cannot restore previous.
;
pro give_credit_where_due
    ; do nothing if not set
    hfe = getenv("IBEX_PLOT_LABEL")
    if (hfe eq '') then return

    hf = ['','','','','','']
    ; top left, mid, right;   bottom left, mid, right
    x  = [0.010,0.500,0.990, 0.010,0.500,0.990]
    y  = [0.965,0.965,0.965, 0.015,0.015,0.015]
    a  = [0.000,0.500,1.000, 0.000,0.500,1.000]

    if (hfe eq 'DEFAULT') then begin
	hf[0] = 'IBEX SOC'
	hf[1] = ''
	hf[2] = ''
	hf[3] = ''
	hf[4] = ''
	hf[5] = strmid(systime(0),4)    ; e.g. 'Oct 20 09:32:36 2009'
    endif else begin
	sep = strmid(hfe,0,1)
	hf = strsplit(strmid(hfe,1,strlen(hfe)),sep,/extract)
    endelse
    
    for i=0,5 do begin
	xyouts,x[i],y[i],hf[i],align=a[i],/normal
    endfor
end

;
; eof
;
