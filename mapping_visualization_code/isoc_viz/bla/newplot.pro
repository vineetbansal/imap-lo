;
; $Id: newplot.pro 1372 2008-03-24 14:33:40Z gbc $
;
; EDITED 6/12/07 by K. Maynard to add Z-buffer functionality
;
;==========================================================
pro new_axis,xax,yax,xtickv,xtickname,ytickv,ytickname,blk = blk, $
    xtit = xtit, ytit = ytit
;==========================================================

if not keyword_set(blk) then blk = 0

nx = n_elements(xax) & ny = n_elements(yax)
oplt,[xax[0],xax[nx-1]],[yax[0],yax[0]],color = blk
oplot,[xax[0],xax[0]],[yax[0],yax[ny-1]], color = blk
oplot,[xax[nx-1],xax[nx-1]],[yax[0],yax[ny-1]],color = blk 
oplot,[xax[0],xax[nx-1]],[yax[ny-1],yax[ny-1]],color = blk

nticx = n_elements(xtickv) & nticy = n_elements(ytickv)
dytic = (yax[ny-1]-yax[0])/70.0

for i=0,nticx-1 do begin
  oplot,[xtickv[i],xtickv[i]],[yax[0],yax[0]+dytic],/noclip,color = blk
  xyouts,xtickv[i],yax[0],'!C' + xtickname[i],/noclip,charsize = 1.5,color = blk
end
if (keyword_set(xtit)) then begin
 xyouts,(xax[0]+xax[nx-1])/2.0,yax[0],'!C!C'+xtit,charsize = 1.5,color = blk
end

dxtic = (xax[nx-1]-xax[0])/70.0
for i=0,nticy-1 do begin
  oplot,[xax[0],xax[0]+dxtic],[ytickv[i],ytickv[i]],/noclip,color = blk
  xyouts,xax[0],ytickv[i], ytickname[i]+' ',/noclip,charsize = 1.5,align=1,color = blk
end

d = convert_coord([xax[0]],[(yax[0]+yax[ny-1])/2.0],/data,/to_device)

if (keyword_set(ytit)) then begin
  xyouts,d[0,0]-3.0*!D.Y_CH_SIZE,d[1,0],ytit,charsize = 1.5,$
    orientation = 90,/device,color = blk
end

return
end



;==============================
PRO COLOR_20, ncol = ncol
;==============================
;     making a color table
;         0    1  2  3  4  5
;for do begin

;endfor
;
common rgb, red, green, blue
ncol=!d.n_colors
if (!d.n_colors gt 256) then ncol = 256
 print,'ncol = ',ncol
    Red = FLTARR(ncol)
    Green = FLTARR(ncol)
    BLUE = FLTARR(ncol)

    FOR I=0,ncol-1 DO BEGIN
      RED(I) = 0.15*(ncol-1.)
      GREEN(I) = 0.0*(ncol-1.)
      BLUE(I) = .25*(ncol-1.)
    IF( I GT .05*ncol) THEN BEGIN
      RED(I) = 0.3*(ncol-1.)
      GREEN(I) = 0.0*(ncol-1.)
      BLUE(I) = .5*(ncol-1.)
    ENDIF
    IF( I GT .1*ncol) THEN BEGIN
       RED(I) = 0.15
       GREEN(I) = 0.1*(ncol-1)   ; 0.0*255
       BLUE(I) = .75*(ncol-1)
    ENDIF
    IF( I GT .15*ncol) THEN BEGIN
       RED(I) = 0.0
       GREEN(I) = 0.2*(ncol-1)   ; 0.0*255
       BLUE(I) = 1*(ncol-1)
    ENDIF
    IF( I GT .2*ncol) THEN BEGIN
       RED(I) = 0.0*(ncol-1)
       GREEN(I) = 0.45*(ncol-1)  ; 0.9*255
       BLUE(I) = 1.0*(ncol-1)   ; 0.8*255
    ENDIF
    IF( I GT .25*ncol) THEN BEGIN
       RED(I) = 0.0*(ncol-1)
       GREEN(I) = 0.7*(ncol-1)  ; 0.9*255
       BLUE(I) = 1.0*(ncol-1)   ; 0.8*255
    ENDIF
    IF( I GT .3*ncol) THEN BEGIN
       RED(I) = 0.0*(ncol-1)   ; 0.0*255
       GREEN(I) = .85*(ncol-1)
       BLUE(I) = 0.85*(ncol-1)
    ENDIF
    IF( I GT .35*ncol) THEN BEGIN
       RED(I) = 0.0*(ncol-1)   ; 0.0*255
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 0.7*(ncol-1)
    ENDIF
    IF( I GT .4*ncol) THEN BEGIN
       RED(I) = 0.3*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 0.45*(ncol-1)
    ENDIF
    IF( I GT .45*ncol) THEN BEGIN
       RED(I) = 0.6*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 0.0*(ncol-1)
    ENDIF
    IF( I GT .5*ncol) THEN BEGIN
       RED(I) = .8*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 0.0*(ncol-1)
    ENDIF
    IF( I GT .55*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 0.0*(ncol-1)
    ENDIF
    IF( I GT .6*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 0.85*(ncol-1)   ; 1.0*255
       BLUE(I) = 0.0*(ncol-1)
    ENDIF
    IF( I GT .65*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 0.7*(ncol-1)   ; 1.0*255
       BLUE(I) = 0.0*(ncol-1)
    ENDIF
    IF( I GT .7*ncol) THEN BEGIN
       RED(I) = .9*(ncol-1)
       GREEN(I) = 0.5*(ncol-1)   ; 1.0*255
       BLUE(I) = 0.15*(ncol-1)
    ENDIF
    IF( I GT .75*ncol) THEN BEGIN
       RED(I) = .8*(ncol-1)
       GREEN(I) = 0.3*(ncol-1)   ; 1.0*255
       BLUE(I) = 0.3*(ncol-1)
    ENDIF
    IF( I GT .8*ncol) THEN BEGIN
       RED(I) = .9*(ncol-1)
       GREEN(I) = 0.15*(ncol-1)
       BLUE(I) = 0.4*(ncol-1)
    ENDIF
    IF( I GT .85*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 0.0*(ncol-1)
       BLUE(I) = 0.4*(ncol-1)
    ENDIF
    IF( I GT .9*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 1.0*(ncol-1)
;       RED(I) = 1.0*(ncol-1)
;       GREEN(I) = 0.2*(ncol-1)
;       BLUE(I) = .7*(ncol-1)
    ENDIF
    IF( I GT .95*ncol) THEN BEGIN
       RED(I) = 1.0*(ncol-1)
       GREEN(I) = 1.0*(ncol-1)
       BLUE(I) = 1.0*(ncol-1)
;       print,'hi - 2'
;       RED(I) = 1.0*(ncol-1)
;       GREEN(I) = 0.4*(ncol-1)
;       BLUE(I) = 1.0*(ncol-1)
    ENDIF
    ENDFOR
;
   RED(0) = 0.
   GREEN(0) = 0.
   BLUE(0) = 0.
;   red(ncol-1) = 255.0
;   green(ncol-1) = 255.0
;   blue(ncol-1) = 255.0
;   RED(ncol-1) = (ncol-1)
;   GREEN(ncol-1) = (ncol-1)
;   BLUE(ncol-1) = (ncol-1)
;	PRINT,RED
   TVLCT, RED, GREEN, BLUE
;
RETURN
END





;==========================================================================
PRO COLOR_PLOT, Z_IN, X, Y, $
	ZRANGE=ZR, POSITION=POS, DEVICE=DEV, CHARSIZE=CHS, XMARGIN=XMAR, $
	YMARGIN=YMAR, FILL=FILL, NOERASE=NOER, FONT=FONT, SUBTITLE=SUBT, $
	TITLE=TITLE, TICKLEN=TICL, XMINOR=XMI, YMINOR=YMI, XTICKS=XTI,   $
	YTICKS=YTI, XTICKNAME=XTN, YTICKNAME=YTN, XTICKV=XTV, YTICKV=YTV,$
	XTITLE=XTITLE, YTITLE=YTITLE, STITLE=STITLE, SMINOR=SMINOR, 	 $
	STICKS=STICKS, STICKV=STV, STICKNAME=STICKN, NOAXES=NOAX,	 $
	SMOOTH=SM, NOSCALE=NSC, LOGSC=LOGSC, WRAP=WRAP, MAX_VALUE=MAXZ,	 $
	CONTOUR=CONTOUR, C_COLOR=C_COLOR, LEVELS=LEV, C_LINESTYLE=C_LI,  $
	C_CHARSIZE=C_CHAR, C_LABELS=C_LAB, C_THICK=C_THI, YWRAP=YWRAP,	 $
	ZCOLORS=ZCOLORS, col_max=max_col, lprt=lprt

;==========================================================================

;This procedure does a TV plot of a 2 dimensional array Z with an adjacent
;color scale.

;ARGUEMENTS:
;  Z - The 2 dimensional array to be plotted. The values are converted to
;colored squares or rectangles unless smoothing is selected. The array Z is 
;expanded by a single scale factor until it fits snugly in the plotting area. 
;Using the keyword FILL causes it to expand by two factors in the x and y 
;directions so that it fills the plot area. 

;  X & Y - are optional parameters used to label the axes of the plot or to 
;determine the position of the grid rectangles. 
;  1.) Use exactly as you would in a call to CONTOUR: X & Y denote coordinates
;at the centers of the grid rectangles. Grid rectange edges are placed halfway
;between the centers.
;  2.) If it is desired only to label the axes, X & Y need only be two element
;vectors containing the max & min values. If you don't want axis labels, omit 
;both; for X axis labels only, just include X; for Y axis labels only, set X 
;to 0 (or any SINGLE value) and include Y. 
;  3.) To specify the size of the grid rectangles, set X to an n+1-dimension
;vector of vertical positions and Y to an m+1-dimension array of horizontal
;positions (increasing order), where Z is n x m. (X(i), Y(j)) will then give 
;the coordinate of the lower left corner of the grid rectangle for Z(i,j).

;KEYWORDS:
;  FILL - if set, Z is expanded by separate factors until it fills the plot
;area. Otherwise it is expanded by a single factor (square grid).

;  ZRANGE - A 2 dimensional vector (zmax, zmin). Values of Z greater than
;zmax are colored at the top scale value and values of Z less than zmin are
;colored at the bottom of the scale.

;  SMOOTH - nearest neighbor is used to expand the Z array. If SMOOTH is set, 
;bilinear interpolation is used to smooth the data.
;******NOTE******When smoothing without wrapping, the edges of the plot will
;lie over the centers of the outermost grid squares.  Thus when specifying
;the min and max values of the axes as in 2 above, you should use the x & y
;values at the center of the outermost grid squares.  When not smoothing or
;when wrapping, the edge of the plot will correspond to the edge of the
;outermost grid squares.

;  NOSCALE - If set, no color scale is plotted.

;  POSITION - Position of the region containing the plot, in normal 
;coordinates, unless DEVICE is set. In this sense it differs from the
;IDL keyword and setting !P.POSITION has no effect here.

;  CHARSIZE, DEVICE, FONT, NOERASE, SUBTITLE, TITLE, TICKLEN, 
;XMARGIN, XMINOR, XTICKNAME, XTICKS, XTICKV, XTITLE, YMARGIN, YMINOR,
;YTICKNAME, YTICKS, YTICKV, YTITLE - Standard IDL plotting keywords.
;The default values used are those of the corresponding IDL system variables
;except for the margins. When no keywords are used to set the margins, they
;are set automatically based on which axis titles or labels are present.

;  SMINOR, STICKNAME, STICKS, STICKV, STITLE  - Similar to IDL keywords, but
;applied to the scale.

;  LOGSC - Set if you want color on log scale

;  WRAP - Set if data is periodic in X and you want the smoothing to take
;	  this into account

;  YWRAP - Set if data is periodic in Y and you want the smoothing to take
;	  this into account

;  NOAXES - Suppress axis plotting

;  MAX_VALUE - Similar to keyword for contour, fills grid square where
;		Z GT MAX_VALUE with top color table value. (NOTE: GT not GE)
;		This will keep smoothing from interpolating to fill values
;		if ZRANGE is not set. Not needed if ZRANGE is set.

;  CONTOUR  - Set if you want contours overplotted. can customize these by
;using the standard contour keywords C_COLOR, LEVELS, C_LINESTYLE,  
;	C_CHARSIZE, C_LABELS, and C_THICK
;
;  ZCOLORS - use color values in Z_IN without rescaling
;
;Programmer: D. Ortland (10-14-91)  If you have any comments, additional 
;features desired or bugs to report, please let me know.

;	Updated (5-5-92) - Corrected scaling bug, added log scale, wrap
;			   keywords, and reduced SBIG in postscrip plots
;			   or when position is reduced (for smoothing)
;		(8-18-92) - Use of system vars !x.title, etc. should
;			    now work a little better. (Margins set properly)
;	       (11-24-92) - Fixed wrap & stickn
;	       (12-3-92)  - Added NOAXES
;		(3-16-93) - Added MAX_VALUE keyword
;		(3-17-93) - Added ability to use !P.MULTI
;		(4-27-94) - Color scale may not be from 0-255-use!d.n_colors
;		(5-27-94) - Added contouring capability. 
;			    Changed usage of X & Y
;	       (10-25-94) - Added ywrap, changed C_LABEL to C_LABELS,
;			    C_CHARSIZ to C_CHARSIZE and eliminated
;			    extrapolation when smoothing
;		(12-14-94)- Added ZCOLORS keyword
;==========================================================================

;ON_ERROR, 2

IF (!D.NAME NE 'X') AND (!D.NAME NE 'PS') AND (!D.NAME NE 'Z') THEN BEGIN
  PRINT,'Device must be X or PS or Z'
  RETURN
ENDIF

Z=REFORM(Z_IN)
S = SIZE(Z)                                  
IF S(0) NE 2 THEN BEGIN
  PRINT, 'Z must be a 2 dimensional array'
  RETURN
ENDIF

IF !P.MULTI(1) NE 0 OR !P.MULTI(2) NE 0 OR !P.MULTI(3) NE 0 THEN BEGIN
  IF !P.MULTI(0) LE 0  AND NOT KEYWORD_SET(NOER) THEN ERASE 
ENDIF ELSE IF NOT KEYWORD_SET(NOER) THEN ERASE

IF KEYWORD_SET(DEVICE) THEN NFAC = [1.,1.] $
  ELSE NFAC = [!D.X_SIZE, !D.Y_SIZE]

;-----------------------------------------------------------------
;Set up plot area within current device window. 
;Find corners of maximum region for TV plot (lower left & upper right).
;Space is made for labels and color scale. Z array is expanded 
;so it will fit into plot area, and then centered.
;-----------------------------------------------------------------

NOPOS=0
IF N_ELEMENTS(POS) NE 4 THEN BEGIN
  NOPOS=1
  POS = [0., 0., 1., 1.]

  IF !P.MULTI(1) NE 0 OR !P.MULTI(2) NE 0 OR !P.MULTI(3) NE 0 THEN BEGIN
    IF !P.MULTI(1) EQ 0 THEN NPX=1 ELSE NPX = !P.MULTI(1)
    IF !P.MULTI(2) EQ 0 THEN NPY=1 ELSE NPY = !P.MULTI(2)
    IF !P.MULTI(3) EQ 0 THEN NPZ=1 ELSE NPZ = !P.MULTI(3)
    NPLOT = NPX*NPY
    IPLOT = (NPLOT*NPZ - !P.MULTI(0)) MOD NPLOT
    DX=1./NPX
    DY=1./NPY
    IF !P.MULTI(4) EQ 0 THEN BEGIN
      X0=(IPLOT MOD NPX)*DX
      Y1=1.-(IPLOT/NPX)*DY
    ENDIF ELSE BEGIN
      X0=(IPLOT/NPY)*DX
      Y1=1.-(IPLOT MOD NPY)*DY
    ENDELSE
    X1=X0+DX
    Y0=Y1-DY
    POS=[X0,Y0,X1,Y1]
  ENDIF
ENDIF

IF ((POS(2) LE POS(0)) OR $
    (POS(3) LE POS(1))) THEN BEGIN
  PRINT,'Position entered wrong. Try again'
  RETURN
ENDIF

POS = POS * [NFAC, NFAC]			;Use device coordinates
W_SIZE = [POS(2)-POS(0), POS(3)-POS(1)]

IF N_ELEMENTS(CHS) NE 1 THEN BEGIN
;  IF !P.CHARSIZE GT 0 THEN CHS = !P.CHARSIZE ELSE $
;  IF !P.MULTI(1) GE 2 AND !D.NAME NE 'X' THEN CHS=.6 $
;  ELSE CHS = 1
  IF !P.CHARSIZE GT 0 THEN CHS = !P.CHARSIZE ELSE CHS=1
ENDIF
CH_SIZE = [!D.X_CH_SIZE, !D.Y_CH_SIZE]          ;Character sizes
CH_SIZE = CH_SIZE * CHS
MHS=[1.,1.] 
IF !P.MULTI(1) GT 2 THEN MHS(0) = 1.5 / (!P.MULTI(1))
IF !P.MULTI(2) GT 2 THEN MHS(1) = 1.5 / (!P.MULTI(2))
CH_SIZE = CH_SIZE * MHS

IF (N_ELEMENTS(TITLE) NE 1) AND (!P.TITLE NE '') THEN  TITLE = !P.TITLE
IF (N_ELEMENTS(SUBT) NE 1) AND (!P.SUBTITLE NE '') THEN  SUBT = !P.SUBTITLE
IF (N_ELEMENTS(XTITLE) NE 1)  AND (!X.TITLE NE '') THEN  XTITLE = !X.TITLE
IF (N_ELEMENTS(YTITLE) NE 1)  AND (!Y.TITLE NE '') THEN  YTITLE = !Y.TITLE

IF N_ELEMENTS(XMAR) NE 2 THEN BEGIN		;Set margins
  XMAR = [10,10]
  IF N_ELEMENTS(YTITLE) NE 1 THEN XMAR(0) = XMAR(0) - 4
  IF N_ELEMENTS(Y) LT 2 THEN $
    IF N_ELEMENTS(X) LT 2 THEN XMAR(0) = XMAR(0) - 6 $
    ELSE XMAR(0) = XMAR(0) - 3
  IF N_ELEMENTS(STITLE) NE 1 THEN XMAR(1) = 7
  IF KEYWORD_SET(NSC) THEN $
    IF N_ELEMENTS(X) LT 2 THEN XMAR(1) = 0 $
    ELSE XMAR(1) = 3
ENDIF

IF N_ELEMENTS(YMAR) NE 2 THEN BEGIN
  YMAR = [4,2]
  IF N_ELEMENTS(SUBT) NE 1 THEN $
    IF N_ELEMENTS(XTITLE) NE 1 THEN $
      IF N_ELEMENTS(X) LT 2 THEN YMAR(0) = 0 $
      ELSE YMAR(0) = 2 $
    ELSE YMAR(0) = 3
  IF N_ELEMENTS(TITLE) NE 1 THEN $
    IF N_ELEMENTS(Y) LT 2 THEN YMAR(1) = 0 $
    ELSE YMAR(1) = 1
ENDIF

LL_MARGIN = [XMAR(0), YMAR(0)]
UR_MARGIN = [XMAR(1), YMAR(1)]			;Margins in # characters

IF KEYWORD_SET(NSC) THEN BEGIN
  SPACE = 0 & SCALE_WID = 0
ENDIF ELSE BEGIN
  SPACE = .05 * W_SIZE(0)			;Space between plot & scale
  SCALE_WID = .05 * W_SIZE(0)			;Scale width
ENDELSE

LL_CORNER = LL_MARGIN * CH_SIZE
UR_CORNER = W_SIZE - [SPACE + SCALE_WID, 0] - UR_MARGIN * CH_SIZE

IF KEYWORD_SET(FILL) THEN $
  PFAC = (UR_CORNER - LL_CORNER) / S(1:2) $
ELSE $
  PFAC = MIN ((UR_CORNER - LL_CORNER) / S(1:2))

P_SIZE = PFAC * S(1:2)					;Size & pos of actual 
LL_POS = .5 * ((LL_CORNER + UR_CORNER) - P_SIZE)	;TV plot (dev coord)
LL_POS = LL_POS + POS(0:1)
POS = [LL_POS, LL_POS + P_SIZE]

IF (MIN(P_SIZE) LT 1) THEN BEGIN
  PRINT, 'Not enough space to plot. Try scaling characters or margins.'
  RETURN
ENDIF


IF N_ELEMENTS(FONT) NE 1 THEN  FONT = !P.FONT
IF N_ELEMENTS(TICL) NE 1 THEN  TICL = !P.TICKLEN

;IF N_ELEMENTS(ZR) EQ 2 THEN BEGIN			;Set Z range
;  IF ZR(0) GE ZR(1) THEN ZR(1) = ZR(0) + 1
;  IF NOT KEYWORD_SET(SM) THEN DATA = (Z < ZR(1)) > ZR(0) $
;	ELSE DATA = Z
;ENDIF ELSE BEGIN
  DATA = Z
  ;IF NOT KEYWORD_SET(SM) THEN BEGIN
   ; ZR = [MIN(DATA), MAX(DATA)]
    IF ZR(0) EQ ZR(1) THEN ZR(1) = ZR(0) + 1
  ;ENDIF
;ENDELSE

;IF KEYWORD_SET(LOGSC) THEN BEGIN
;  DMIN = MIN(DATA) & DMAX = MAX(DATA)
;  IF (DMIN LE 0) AND (DMAX LE 0) THEN BEGIN
;    PRINT, ' CANT DO LOG OF NEGITIVES, DUMMY'
;    RETURN
;  ENDIF ELSE IF (DMIN LE 0) THEN DATA = ALOG10(DATA+DMAX/1.E6) $
;  ELSE DATA = ALOG10(DATA)
;  IF N_ELEMENTS(ZR) EQ 2 THEN IF ZR(0) LE 0 THEN ZR(0) = ZR(1) / 1.E6
;ENDIF

;==========
;TV plot
;==========

N = N_ELEMENTS(X)-1 & M = N_ELEMENTS(Y)-1

IF (!D.NAME EQ 'PS') THEN BEGIN
  IF ((N NE S(1)) OR (M NE S(2))) AND ((N+1 NE S(1)) OR (M+1 NE S(2))) $
	AND (NOT KEYWORD_SET(SM)) THEN BEGIN

    ;IF KEYWORD_SET(LOGSC) THEN BEGIN
    ;  DMIN=MIN(ALOG10(ZR(0))) & DMAX = MAX(ALOG10(ZR(1))) 
   ;ENDIF ELSE BEGIN
  ;   DMIN = ZR(0) & DMAX = ZR(1)
  ;ENDELSE
 
    IF NOT KEYWORD_SET(ZCOLORS) THEN $
    DATA = round((!d.n_colors-1) * (DATA-DMIN) / (DMAX - DMIN))
    FDATA = (!d.n_colors-1) * (DATA-DMIN) / (DMAX - DMIN)
    TV, DATA, LL_POS(0), LL_POS(1), XSIZE=P_SIZE(0), YSIZE=P_SIZE(1)

    XB=(.5+FINDGEN(S(1))) / FLOAT(S(1))
    YB=(.5+FINDGEN(S(2))) / FLOAT(S(2))

    GOTO, SCALE
  ENDIF ELSE SBIG = $
	[640,480]*[POS(2)-POS(0),POS(3)-POS(1)]/NFAC ;Pixel size of image
ENDIF ELSE SBIG = [P_SIZE(0),P_SIZE(1)]

IF (N EQ S(1)) AND (M EQ S(2)) THEN BEGIN	;Grid edge normal coord
  XE = FLOAT(X-X(0)) / (X(N) - X(0))
  YE = FLOAT(Y-Y(0)) / (Y(M) - Y(0))
ENDIF ELSE IF (N+1 EQ S(1)) AND (M+1 EQ S(2)) THEN BEGIN
  XX=[1.5*X(0)-.5*X(1), (X(0:N-1)+X(1:N))*.5, 1.5*X(N)-.5*X(N-1)]
  YY=[1.5*Y(0)-.5*Y(1), (Y(0:M-1)+Y(1:M))*.5, 1.5*Y(M)-.5*Y(M-1)]
  XE = FLOAT(XX-XX(0)) / (XX(N+1) - XX(0))
  YE = FLOAT(YY-YY(0)) / (YY(M+1) - YY(0))
ENDIF ELSE BEGIN
  XE = FINDGEN(S(1)+1) / S(1) 
  YE = FINDGEN(S(2)+1) / S(2)
ENDELSE

XB = (FINDGEN(SBIG(0)) + .5) / FLOAT(SBIG(0))	;Centers of pixel grid
YB = (FINDGEN(SBIG(1)) + .5) / FLOAT(SBIG(1))

IF KEYWORD_SET(SM) THEN	BEGIN
  IF KEYWORD_SET(WRAP) THEN BEGIN		;Make periodic in X
    XE = [XE(0)-XE(S(1)-1)+XE(S(1)-2),XE,XE(S(1))+XE(1)-XE(0)]
    DATA = [DATA(S(1)-1,*),DATA,DATA(0,*)]
    S(1) = S(1) + 2
  ENDIF

  IF KEYWORD_SET(YWRAP) THEN BEGIN		;Make periodic in Y
    YE = [YE(0)-YE(S(2)-1)+YE(S(2)-2),YE,YE(S(2))+YE(1)-YE(0)]
    DATA = [DATA(S(1)-1,*),DATA,DATA(0,*)]
    DATA = [[DATA(*,S(2)-1)],[DATA],[DATA(*,0)]]
    S(2) = S(2) + 2
  ENDIF

;Centers of data grid
  XG = .5 * (XE(0:S(1)-1) + XE(1:S(1)))
  YG = .5 * (YE(0:S(2)-1) + YE(1:S(2)))

;Expand data grid so that 1st & last data pts lie on plot edge (ie at 0 & 1)
;if not wrapped. This will prevent edge extrapolation.
  IF NOT KEYWORD_SET(WRAP) THEN BEGIN
    XE = (XE-XG(0))/(XG(S(1)-1)-XG(0))
    XG = (XG-XG(0))/(XG(S(1)-1)-XG(0))
  ENDIF
  IF NOT KEYWORD_SET(YWRAP) THEN BEGIN
    YE = (YE-YG(0))/(YG(S(2)-1)-YG(0))
    YG = (YG-YG(0))/(YG(S(2)-1)-YG(0))
  ENDIF
ENDIF ELSE BEGIN
  XG = XE & YG = YE
ENDELSE

;Note that XG,YG are at grid edge if not smoothing, 
;at grid center if smoothing.

NX = LONARR(SBIG(0)) & MY = LONARR(SBIG(1))
NG = N_ELEMENTS(XG)-1 & MG = N_ELEMENTS(YG)-1
NB = SBIG(0)-1 & MB = SBIG(1)-1

;Lower left corner indices of (XG,YG) grid square that contains center
;of each pixel grid point.
FOR I=0, NB DO NX(I) = MAX([WHERE(XB(I) GT XG(0:NG-1)),0])
FOR I=0, MB DO MY(I) = MAX([WHERE(YB(I) GT YG(0:MG-1)),0])

;Put these indices in an array the same size as pixel grid
;and convert to scalar subscript for data array
;Note IND(I,J) = NX(I) + S(1) * MY(J) for  I=0,SBIG(0)-1, J=0,SBIG(1)-1

IND = NX # REPLICATE(1,SBIG(1)) + REPLICATE(S(1),SBIG(0)) # MY

  nmz=0
IF NOT KEYWORD_SET(SM) THEN BEGIN	    ;Single valued rectangles
  ZBIG = DATA(IND)

ENDIF ELSE BEGIN			    	;Bi-linear interpolation
  WX2 = (XB - XG(NX)) / (XG(NX+1) - XG(NX))	;Interpolation wieghts
  WY2 = (YB - YG(MY)) / (YG(MY+1) - YG(MY))
  WX1 = 1. - WX2  & WY1 = 1. - WY2

  IF N_ELEMENTS(MAXZ) NE 1 THEN MAXV=MAX(Z)+1. ELSE MAXV=MAXZ
  IF KEYWORD_SET(LOGSC) THEN MAXV=ALOG10(MAXV)

;Interpolate, but don't use grid points with Z>MAXV
  W11=WX1#WY1
  JX=WHERE(DATA(IND) GT MAXV,NJ)
  IF NJ GT 0 THEN W11(JX) = 0.

  W21=WX2#WY1
  JX=WHERE(DATA(IND+1) GT MAXV,NJ)
  IF NJ GT 0 THEN W21(JX) = 0.

  W12=WX1#WY2
  JX=WHERE(DATA(IND+S(1)) GT MAXV,NJ)
  IF NJ GT 0 THEN W12(JX) = 0.

  W22=WX2#WY2
  JX=WHERE(DATA(IND+(S(1)+1)) GT MAXV,NJ)
  IF NJ GT 0 THEN W22(JX) = 0.

  ZBIG = W11*DATA(IND) + W21*DATA(IND+1) + W12*DATA(IND+S(1)) $
       + W22*DATA(IND+(1+S(1)))
  WTOT=W11+W21+W12+W22

  JX=WHERE(WTOT NE 0,NJ)
  IF NJ NE 0 THEN ZBIG(JX)=ZBIG(JX)/WTOT(JX)

;Refill grid squares that contain no data with max value
  FOR I=0, NB DO NX(I) = MAX([WHERE(XB(I) GT XE(0:NG)),0])
  FOR I=0, MB DO MY(I) = MAX([WHERE(YB(I) GT YE(0:MG)),0])
  IND = NX # REPLICATE(1,SBIG(1)) + REPLICATE(S(1),SBIG(0)) # MY

  JX=WHERE(DATA(IND) GT MAXV,NJ)
  IF NJ NE 0 THEN ZBIG(JX)=MAXV

;Extrapolation may have moved result out of ZRANGE. 
  IF N_ELEMENTS(MAXZ) NE 1 THEN MAXV=MAX(ZBIG) ELSE $
    IF KEYWORD_SET(LOGSC) THEN MAXV=MAX(ZBIG(WHERE(ZBIG LT ALOG10(MAXZ)))) $
	ELSE MAXV=MAX(ZBIG(WHERE(ZBIG LT MAXZ)))
  IF N_ELEMENTS(ZR) NE 2 THEN BEGIN
    IF NOT KEYWORD_SET(LOGSC) THEN $
	ZR = [MIN(ZBIG), MAXV] $
    ELSE $
	ZR = [10.^(MIN(ZBIG)), 10.^(MAXV)]
  ENDIF

  if n_elements(maxz) eq 1 and n_elements(max_col) eq 1 then $
    ind=where(zbig ge maxz,nmz)

  IF NOT KEYWORD_SET(LOGSC) THEN $
	ZBIG = (ZBIG < ZR(1)) > ZR(0) $
  ELSE $
	ZBIG = (ZBIG < ALOG10(ZR(1))) > ALOG10(ZR(0))
ENDELSE

IF KEYWORD_SET(LOGSC) THEN BEGIN
  DMIN = MIN(ALOG10(ZR(0))) & DMAX = MAX(ALOG10(ZR(1)))
ENDIF ELSE BEGIN
  DMIN = ZR(0) & DMAX = ZR(1)
ENDELSE
 
IF NOT KEYWORD_SET(ZCOLORS) THEN $
  DATA = round((!d.n_colors-1) * (ZBIG-DMIN) / (DMAX - DMIN)+.01) $
ELSE DATA=ZBIG
FDATA = (!d.n_colors-1) * (ZBIG-DMIN) / (DMAX - DMIN)+.01

if n_elements(maxz) eq 1 and n_elements(max_col) eq 1 and $
  nmz gt 0 then data(ind)=max_col

TV, DATA, LL_POS(0), LL_POS(1), XSIZE=P_SIZE(0), YSIZE=P_SIZE(1)

;================
;Scale
;================

SCALE:


IF KEYWORD_SET(NSC) THEN GOTO, AXES

SLL_POS = [POS(2)+SPACE,POS(1)]
SP_SIZE = [SCALE_WID, P_SIZE(1)]
IF (!D.NAME EQ 'X' or !D.NAME EQ'Z') THEN $
  SCL = REPLICATE(1,SP_SIZE(0)) # (FINDGEN(SP_SIZE(1)))  $
ELSE SCL = TRANSPOSE(FINDGEN(256))

TVSCL, SCL, SLL_POS(0), SLL_POS(1), XSIZE=SP_SIZE(0), YSIZE=SP_SIZE(1)
SPOS = [SLL_POS, SLL_POS + SP_SIZE]

IF N_ELEMENTS(STICKS) NE 1 THEN STICKS = 0
IF N_ELEMENTS(SMINOR) NE 1 THEN SMINOR = 0

IF N_ELEMENTS(STITLE) NE 1 THEN  STITLE = ''
IF N_ELEMENTS(STICKN) NE STICKS+1 THEN  STICKN = REPLICATE('',STICKS+1)
IF N_ELEMENTS(STV) NE STICKS+1 THEN $
  IF (STICKS GT 0) THEN $
    STV = ZR(0) + FINDGEN(STICKS+1) * (ZR(1) - ZR(0)) / STICKS $
  ELSE STV = ZR

IF KEYWORD_SET(LPRT) THEN begin
    loadct,0
end

PLOT, /NODATA, /NOERAS, /DEVICE, POS=SPOS, YSTYLE=8, [0,1], [0,1], $
	TICKLEN=0, XMINOR=-1, XTICKN=[' ',' '], $
	XRA=[0,0], YRA=[0,0], XTIT='', YTIT='', TIT='', XTICKS=1, $
	YTICKN=[' ',' '],YTICKS=1,subt=''

zr(1)=zr(1)+.0001*(zr(1)-zr(0))
IF KEYWORD_SET(LOGSC) THEN YTYPE=1 ELSE YTYPE=0
AXIS, YAXIS=1, TICKLEN=1, CHARS=CHS, YTICKN=STICKN, YTICKV=STV, YRA=ZR, $
	FONT=FONT, YTITLE=STITLE, YTICKS=STICKS, YMI=SMINOR, YSTYLE=1, $
	YTYPE = YTYPE

;------------------------
;Plot axes
;------------------------

IF KEYWORD_SET(LPRT) THEN begin
    loadct,0
end

AXES:
IF N_ELEMENTS(TITLE) NE 1 THEN  TITLE = !P.TITLE
IF N_ELEMENTS(SUBT) NE 1 THEN  SUBT = !P.SUBTITLE
IF N_ELEMENTS(XTITLE) NE 1 THEN  XTITLE = !X.TITLE
IF N_ELEMENTS(YTITLE) NE 1 THEN  YTITLE = !Y.TITLE
IF N_ELEMENTS(XMI) NE 1 THEN XMI = !X.MINOR
IF N_ELEMENTS(YMI) NE 1 THEN YMI = !Y.MINOR
IF N_ELEMENTS(XTI) NE 1 THEN XTI = !X.TICKS
IF N_ELEMENTS(YTI) NE 1 THEN YTI = !Y.TICKS
IF N_ELEMENTS(XTN) EQ 0 THEN XTN = !X.TICKNAME
IF N_ELEMENTS(YTN) EQ 0 THEN YTN = !Y.TICKNAME

IF (N_ELEMENTS(X) LT 2) AND (N_ELEMENTS(Y) LT 2) THEN TICL = 0

IF N_ELEMENTS(X) LT 2 THEN BEGIN
  XMI = -1
  XTN = REPLICATE(' ',2)
  XTI = 1
  X=[0, 1]
  N=1
ENDIF

IF N_ELEMENTS(Y) LT 2 THEN BEGIN
  YMI = -1
  YTN = REPLICATE(' ',2)
  YTI = 1
  Y=[0, 1]
  M=1
ENDIF

IF N_ELEMENTS(XTV) EQ 0 THEN $
  IF (XTI GT 0) THEN $
    XTV = MIN(X) + FINDGEN(XTI+1) * (MAX(X)-MIN(X)) / XTI $
  ELSE XTV = [MIN(X), MAX(X)]
IF N_ELEMENTS(YTV) EQ 0 THEN $
  IF (YTI GT 0) THEN $
    YTV = MIN(Y) + FINDGEN(YTI+1) * (MAX(Y)-MIN(Y)) / YTI $
  ELSE YTV = [MIN(Y), MAX(Y)]

;Coordinates at plot boundary
IF (N+1 EQ S(1)) AND (M+1 EQ S(2)) THEN BEGIN
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(WRAP) THEN $
    XX=[X(0),X(N)] ELSE XX=[1.5*X(0)-.5*X(1), 1.5*X(N)-.5*X(N-1)]
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(YWRAP) THEN $
    YY=[Y(0),Y(M)] ELSE YY=[1.5*Y(0)-.5*Y(1), 1.5*Y(M)-.5*Y(M-1)]
ENDIF ELSE IF (N EQ S(1)) AND (M EQ S(2)) THEN BEGIN
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(WRAP) THEN $
    XX=[.5*X(0)+.5*X(1), .5*X(N)+.5*X(N-1)] ELSE XX=[X(0),X(N)] 
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(YWRAP) THEN $
    YY=[.5*Y(0)+.5*Y(1), .5*Y(M)+.5*Y(M-1)] ELSE YY=[Y(0),Y(M)] 
ENDIF ELSE BEGIN
  DX=(X(N)-X(0))/S(1)
  DY=(Y(M)-Y(0))/S(2)
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(WRAP) THEN $
    XX=[X(0)+.5*DX, X(N)-.5*DX] ELSE XX=[X(0),X(N)] 
  IF KEYWORD_SET(SM) AND NOT KEYWORD_SET(YWRAP) THEN $
    YY=[Y(0)+.5*DY, Y(M)-.5*DY] ELSE YY=[Y(0),Y(M)] 
ENDELSE

IF KEYWORD_SET(NOAX) THEN STY=5 ELSE STY=1
IF KEYWORD_SET(CONTOUR) THEN BEGIN

  IF N_ELEMENTS(C_COLOR) GE 1 THEN COL=C_COLOR ELSE COL=[!P.COLOR]
  IF N_ELEMENTS(LEV) LT 2 THEN  LEV=ZR(0)+FINDGEN(11)*(ZR(1)-ZR(0))/10. 
  if keyword_set(logsc) then lev=alog10(lev)
  NLEV=N_ELEMENTS(LEV)
  IF N_ELEMENTS(C_LI) NE N_ELEMENTS(LEV) THEN C_LI=REPLICATE(0,NLEV)
  IF N_ELEMENTS(C_LAB) LE 0 THEN BEGIN
    C_LAB=REPLICATE(1,NLEV)
    ILAB=INDGEN(NLEV/2)*2+1
    C_LAB(ILAB)=0
  ENDIF
  IF N_ELEMENTS(C_CHAR) LE 0 THEN C_CHAR=0.
  IF N_ELEMENTS(C_THI) LE 0 THEN C_THI=1.

  DATA = FDATA * (DMAX-DMIN) / (!d.n_colors-1)  + DMIN
  NX=N_ELEMENTS(XB) & NY=N_ELEMENTS(YB)
  DX=FLOAT(XX(1)-XX(0))/NX & DY=FLOAT(YY(1)-YY(0))/NY
  XB=XX(0)+((XB-XB(0))/(XB(1)-XB(0))+.5)*DX
  YB=YY(0)+((YB-YB(0))/(YB(1)-YB(0))+.5)*DY
  maxzz=zr(1)*.99+zr(0)*.01
  if keyword_set(logsc) then maxzz=alog10(maxzz)

  CONTOUR,DATA,XB,YB,POS=POS,/DEV,$
	/NOER,XST=STY,YST=STY,C_COL=COL,C_THI=C_THI,C_CHARSIZ=C_CHAR, $
	LEV=LEV,/FOLLOW,C_LI=C_LI, MAX=maxzz, C_LAB=C_LAB, $
	SUBTITLE=SUBT, TICKLEN=TICL, CHARS=CHS, XMI=XMI, YMI=YMI, 	$
	XTICKS=XTI, YTICKS=YTI, XTICKN=XTN, YTICKN=YTN, XTICKV=XTV, 	$
	YTICKV=YTV, FONT=FONT, TITLE=TITLE, XTITLE=XTITLE, 		$
	YTITLE=YTITLE, XRA=XX, YRA=YY

ENDIF ELSE BEGIN
  PLOT, /NODATA, /NOERAS, /DEVICE, POS=POS, XSTYLE=STY, YSTYLE=STY, XX, YY, $
	SUBTITLE=SUBT, TICKLEN=TICL, CHARS=CHS, XMI=XMI, YMI=YMI, 	$
	XTICKS=XTI, YTICKS=YTI, XTICKN=XTN, YTICKN=YTN, XTICKV=XTV, 	$
	YTICKV=YTV, FONT=FONT, TITLE=TITLE, XTITLE=XTITLE, 		$
	YTITLE=YTITLE, XRA=[0,0], YRA=[0,0]
ENDELSE

IF nopos THEN BEGIN
  IF !P.MULTI(1) NE 0 OR !P.MULTI(2) NE 0 OR !P.MULTI(3) NE 0 THEN BEGIN
    IF !P.MULTI(0) EQ 0 THEN !P.MULTI(0)=NPLOT*NPZ-1 ELSE $
	!P.MULTI(0) = !P.MULTI(0) - 1
  ENDIF
ENDIF
 
RETURN
END

