;
; $Id$
;
; pro extra_xaxis
; pro extra_yaxis
;
; Generate a line of extra axis labels, presuming that a plot has
; been set up so that the existing state is sane.
;
; E.g. after a plot with [xy]style 5 (no axes) use xtick_get=xv
; in an axis call to capture the label locations for the major ticks.
; captures the x label positions (in physical coords).
; and optionally a pair of bookends (e.g. what & units)
;
; E.g.
; make_me_bin_plot,ips,'x.txt',position=[.1,.15,.775,.9],ystyle=9,xstyle=5
; axis,xaxis=0,xstyle=1,xticklayout=0,xtickname=replicate(' ',10),xtick_get=xv
; xx=sqrt(xv)
; lab=string(xx,format='(F6.2)')
; extra_xaxis,0,xv,lab,.025,xbnor=[.05,.8],xblab=['Sqrt','(none)']
; extra_xaxis,0,xv,lab,.050,xbnor=[.05,.8],xblab=['Sqrt','(none)']
; extra_xaxis,0,xv,lab,.075,xbnor=[.05,.8],xblab=['Sqrt','(none)']
; axis,xaxis=1,xstyle=1,xticklayout=0,xtickname=replicate(' ',10)
; extra_xaxis,1,xv,lab,.000,xbnor=[.05,.8],xblab=['Sqrt','(none)']  
; extra_xaxis,1,xv,lab,.025,xbnor=[.05,.8],xblab=['Sqrt','(none)']
; extra_xaxis,1,xv,lab,.050,xbnor=[.05,.8],xblab=['Sqrt','(none)'] 
;
; and similarly for the y version.
;
; The orientation is the sense in which the labels flow, but on X
; displays that's probably not what you wanted.  This is a detail
; to fix internally at some point....
;

pro extra_xaxis,            $
    xaxis,                  $ ; IN: 0 (bottom) 1 (top)
    xtkv,                   $ ; IN: array of x axis values
    lab,                    $ ; IN: corresponding labels
    ynoff,                  $ ; IN: offset (outward) in normal units
    xbnor=xbnor,            $ ; IN: min/max normal cooord x for bookends
    xblab=xblab,            $ ; IN: a pair of labels (use '' to skip)
    xorient=xorient           ; IN: optional orientation angle

    if (not keyword_set(xorient)) then xorient=0.0

    nnn = n_elements(xtkv)
    yis = replicate(!y.crange[xaxis],nnn)
    nor = convert_coord(xtkv,yis,/to_normal)
    xxx = nor(0,*)
    yyy = nor(1,*) + 2*(xaxis-0.5)*ynoff
    xyouts,xxx,yyy,lab,alignment=0.5,orientation=xorient,/normal

    if (keyword_set(xbnor) and keyword_set(xblab) and $
	n_elements(xbnor) eq 2 and n_elements(xblab) eq 2) then begin
	    xyouts,xbnor[0],yyy[0],xblab[0],alignment=1.0, $
		orientation=xorient,/normal
	    xyouts,xbnor[1],yyy[1],xblab[1],alignment=0.0, $
		orientation=xorient,/normal
    endif

end

pro extra_yaxis,            $
    yaxis,                  $ ; IN: 0 (left) 1 (right)
    ytkv,                   $ ; IN: array of y axis values
    lab,                    $ ; IN: corresponding labels
    ynoff,                  $ ; IN: offset (outward) in normal units
    ybnor=ybnor,            $ ; IN: min/max normal cooord y for bookends
    yblab=yblab,            $ ; IN: a pair of labels (use '' to skip)
    yorient=yorient           ; IN: optional orientation angle

    if (not keyword_set(yorient)) then yorient=0.0

    nnn = n_elements(ytkv)
    xis = replicate(!x.crange[yaxis],nnn)
    nor = convert_coord(xis,ytkv,/to_normal)
    xxx = nor(0,*) + 2*(yaxis-0.5)*ynoff
    yyy = nor(1,*)
    xyouts,xxx,yyy,lab,alignment=0.5,orientation=yorient,/normal

    if (keyword_set(ybnor) and keyword_set(yblab) and $
	n_elements(ybnor) eq 2 and n_elements(yblab) eq 2) then begin
	    xyouts,xxx[0],ybnor[0],yblab[0],alignment=1.0, $
		orientation=yorient,/normal
	    xyouts,xxx[1],ybnor[1],yblab[1],alignment=0.0, $
		orientation=yorient,/normal
    endif

end

;
; eof
;
