;
; $Id: make_colorbar2.pro 2128 2008-23-12 16:13:34Z bobD $
;
; pro make_colorbar_xy_ver2
;
; These procedures generate colorbars in either x or y.
; One of xtitle or ytitle is required so we know which one.
;
; This routine makes use of the field SCALEOPT in the ips structure. 
; This field accepts keyword=value pairs - the following keywords are
; used by this routine 
;        cb_scaleformat  - value should be set to fortran format 
;                          string for tick labels, fair defaults 
;                          are provided
;        cb_nticks  - number of tickintervals for colorbar
;               note that this is not used for log scales
;
;  NOTES
;   12/08 (DeMajistre) - Modification of original code provided to 
;   me by GBC to provide more 'standard behavior' of colorbar
;   annotation. Right now, IDL makes most of the decisions 
;   (unless overriden), which should provide pretty good results by default.
;   The general procedure follows the original code, i.e., one call to 
;   PLOT or AXIS to set up the plotting box, a call to 
;   MAKE_ME_BIN_PLOT_OVERLAY_XX to fill the box with colors and then 
;   another call to OPLOT or AXIS to put on the scales. The original code
;   had a call to a seperate procedure to determine tick intervals, 
;   but I eliminated this because 1) IDL does a better job of 
;   determining tick positions than I do, and 2) encapsulating IDLs 
;   method of tick position determination caused more problems
;   (including code readability) than it solved.
;
;   If the scaling is 'log', then IDL is used pretty directly. The
;   only complication is for 'Y oriented' colorbars, since PLOT always 
;   puts the scale on the left side, which is non-standard for
;   colorbars. Because of this, we use AXIS instead. For X
;   orientation, PLOT_IO gives very good results.
;
;   For all other scalings ('linear','sqrt'), we start with IDL's
;   default linear ticks and then put them in the right place on the 
;   colorbar. For all but linear scalings, this will obviously result 
;   in non-uniform tick interval, which I regard as a good thing.
;   The tick labels will be roundish numbers, and the scale will be obviously
;   non-linear, which will hopefully reduce errors in interpretation.
;
;   At the request of GBC, for X oriented color bars, the Label
;   appears above the bar, i.e., on the side opposite of the scale. 
;   For Y oriented bars, the scale and title are on the same side. 
;   These defaults can be overridden with the TITLE_SWITCH keyword.
;
;   NOTE THAT KEYWORDS ARE IMPORTANT. This routine will not
;   function correctly without the XTITLE or YTITLE keywords set. 
;   If both or none are set, the results will be undefined. I regard 
;   this as the interface of the original code and haven't changed this.
;   Since I'm not sure of the ISOCs error handling system, I'm not 
;   trapping errors in keyword logic. I think this needs to be fixed.
;
;   I added the keywords the following keywords (and corresponding 
;   scaleopt keywords)
;      NTICKS - the number of labled tickintervals for the plot. 
;               This should be useful for smaller colorbars where IDL 
;               uses too many ticks.
;      SCALEFORMAT - is the FORTRAN format for the tick labels. I tried to
;                provide a suitable default, but YMMV
;      TITLE_SWITCH - Put the title on the opposite (non-default)
;                     side of the bar
;      SCALE_SWITCH - Put the scale on the oppossite (non-default) 
;                     side of the bar 
;
;   By request, you can also specify options through the SCALEOPT
;   field of the common plotting
;   structure. See the seperately provided routine KWPROC for 
;   implementation details.
;
;   The above keywords can be specified by the corresponding 
;   CB_NTICKS and CB_SCALEFORMAT keywords in scaleopt.
;;;
; 1/13/09 RD, simplified scaleformat default - instead of 
;             doing it the hard way, use '(g0)' which seems
;             to do a good job in most cases (more cases than
;             the fancier way of picking something specific
; 3/5/09 RD   replace reference to ips.zmm so that 
;             negative square roots and logs are treated correctly
;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
pro make_colorbar_xy_ver2,            $
    ips,                     $ ; IN: common isoc plotting structure
    position=position,       $ ; IN: location, cf. plot position
    xtitle=xtitle,           $
    ytitle=ytitle,            $
    nticks=nticks,            $
    scaleformat=scaleformat,  $
    title_switch=title_switch,  $
    scale_switch=scale_switch     

    compile_opt HIDDEN, STRICTARR

    if (not keyword_set(xtitle) and not keyword_set(ytitle)) then begin
       print, 'One of xtitle or ytitle must be set'
       return
    endif

; calculate corrected range
    range=ips.smm
    case ips.scaling of
      'log': range=10^range
      'sqrt': range=range^2
      else: range=range
    endcase
;scaleopt processing
    kwproc,ips.scaleopt,kw

    max10=alog10(max(abs(range)))  ;figure out a good default
    min10=alog10(min(abs(range)))
    scaleformat='(g0)'

    ii=where(kw.keyword eq 'cb_scaleformat')
        if ii[0] ne -1 then scaleformat0='('+kw.value[ii[0]]+')'
    if not keyword_set(scaleformat) then scaleformat=scaleformat0

    nticks0=0  ;let IDL figure it out
    ii=where(kw.keyword eq 'cb_nticks')
        if ii[0] ne -1 then nticks0=fix(kv.value[ii[0]])
    if not keyword_set(scaleformat) then nticks=nticks0

    title_switch0=0
    ii=where(kw.keyword eq 'cb_title_switch')
       if ii[0] ne -1 then title_switch0=fix(kw.value[ii[0]])
    if not keyword_set(title_switch) then title_switch=title_switch0

    scale_switch0=0
    ii=where(kw.keyword eq 'cb_scale_switch')
       if ii[0] ne -1 then scale_switch0=fix(kw.value[ii[0]])
    if not keyword_set(scale_switch) then scale_switch=scale_switch0

    if keyword_set(scale_switch eq 0) then xx=[0,1] else xx=[1,0]  
    yy=shift(xx,1)
;;;;;;;;;;;;;;;;;;;;;;;;;;
    nb=100
    del=range[1]-range[0]
    if strlowcase(ips.scaling) ne 'log' then begin
       b0=color_scaling(ips,range[0]+findgen(nb)*del/(nb-1.))
       b1=range[0]+findgen(nb)*del/(nb-1.)
       ; use this plot to get IDLs default ticks for linear scale
       plot,indgen(nb),b1,xstyle=4,ystyle=5,ytick_get=v,/nodata, $
              /noerase,yticks=nticks,position=position
       ticks=n_elements(v)-1
       ;get scaled values
       values=interpol((b0-min(b0))/(max(b0)-min(b0)),b1,v) >0 <1 


       names=v
        ; make an empty plot to set up the plot
        ;
        plot,[0,1],[0,1],/nodata,/noerase,xstyle=5,ystyle=5,position=position
        ;
        ; make and show the color bar
        ;
        a = (1 + findgen(ips.ctop + 1)) # replicate(1.0,2)
        if (keyword_set(ytitle)) then a=transpose(a)
	ips_smm = [ 1, ips.ctop + 1 ]
        case !d.name of
         'PS':  make_me_bin_plot_overlay_ps,a,ips.ctop,ips_smm
         'X':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips_smm
         'Z':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips_smm
;         'WIN':   make_me_bin_plot_overlay_xz,a,ips.ctop
           else:  print,'no support in make_colorbar_xy for ' + !d.name
        endcase
        if (keyword_set(xtitle)) then begin
         xtop=xtitle
         xbot=''
         if title_switch ne scale_switch then begin
           xtop=''
           xbot=xtitle
         endif
         axis,xax=xx[0],xticklen=1.0,xminor=-1,   $
           xtickname=string(float(names),form=scaleformat),       $
           xticks=ticks,xtickv=values,xtitle=xbot
         axis,xax=xx[1],xticklen=1.0,xminor=-1,xtitle=xtop,   $
           xtickname=replicate(' ',9),          $
           xticks=2,xtickv=[0,1]                ; ends
        endif else begin
         rtit=ytitle
         ltit=''
         if title_switch ne scale_switch  then begin
           rtit=''
           ltit=ytitle
         endif
         axis,yax=yy[0],yticklen=1.0,yminor=-1,   $
            ytickname=string(float(names),form=scaleformat),ytitle=rtit, $
            yticks=ticks,ytickv=values
         axis,yax=yy[1],yticklen=1.0,yminor=-1,   $
            ytickname=replicate(' ',9),ytitle=ltit,          $
            yticks=2,ytickv=[0,1]                ; ends
        endelse
    endif else begin
       b0=range[0]+findgen(nb)*del/(nb-1.)
       a = (1 + findgen(ips.ctop + 1)) # replicate(1.0,2)
       if (keyword_set(ytitle)) then begin
         plot_io,fltarr(nb),b0,ysty=5,xticks=1,/noerase,xstyle=4, $
                    position=position
         a=transpose(a)
        endif else plot_oi,b0,fltarr(nb),xsty=5,yticks=1,/noerase, $
                    xticklen=1.0,xminor=-1,ystyle=4,position=position, $
                    xticks=nticks
	ips_smm = [ 1, ips.ctop + 1 ]
        case !d.name of
         'PS':  make_me_bin_plot_overlay_ps,a,ips.ctop,ips_smm
         'X':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips_smm
         'Z':   make_me_bin_plot_overlay_xz,a,ips.ctop,ips_smm
;         'WIN':   make_me_bin_plot_overlay_xz,a,ips.ctop
           else:  print,'no support in make_colorbar_xy for ' + !d.name
        endcase
          if keyword_set(ytitle) then begin 
            rtit=ytitle
            ltit=''
            if title_switch ne scale_switch then begin
              rtit=''
              ltit=ytitle
            endif
            axis,yaxis=yy[0], $
               yrange=10^!y.crange, $
               yst=1,yticks=nticks,yticklen=1.0,yminor=-1,ytitle=rtit
            oplot,[0,0],10^[!y.crange[0],!y.crange[1]]
            axis,xsty=4,ytit=ltit,yaxis=yy[1],ytickname=strarr(10)+' ',yst=1
          endif else begin
            xtit=''
            tit=xtitle
            if title_switch ne 0 then begin
              xtit=xtitle
              tit=''
            endif
            if scale_switch eq 0 then begin
              plot_oi,b0,fltarr(nb),xsty=1,yticks=1,xticklen=1.0, $
               xminor=-1,ystyle=4,/noerase,position=position,xticks=nticks, $
               title=tit,xtitle=xtit
            endif else begin
              plot_oi,b0,fltarr(nb),xsty=5,xtickname=strarr(10)+' ', $
                ystyle=4,/noerase,position=position, $
                xticks=2
              axis,xaxis=1,xticklen=1.,xminor=-1,xticks=nticks,xsty=1
              plot_oi,b0,fltarr(nb),/nodata,/noerase,xsty=8,ysty=4, $
                title=tit,xtitle=xtit,position=position*[1.,1.,1.,1.07], $
                xtickname=strarr(10)+' ',xminor=-1
            endelse
          endelse
    endelse
end
;
; eof
;
