;
; $Id: 
;
; pro plot_hist
; 
; Some simple routines for plotting histogram plots
; Feed it a datafile and get a plot!
; 
pro plot_hist,                 $
          ips,                 $ ; IN: common isoc plotting structure
          datafile,            $ ; IN: name of the data file
          position=position,   $ ; IN: plotting window (!{xy}.window)
          xvar=xvar,           $ ; IN: x-var to be plotted .. the left x of hists, right x is x-var+1
          vars=vars,           $ ; IN: array of y-vars to be plotted
          xtitle=xtitle,       $
          ytitle=ytitle,       $
          title=title,         $
          lines=lines,         $ ; IN: linestyles to be used
          colors=colors,       $ ; IN: colors for linestyles
          fills=fills,         $ ; IN: array of vars to be filled                   
          stripes=stripes,     $ ; IN: set to 1 if you want striping in the fill
          mono=mono,           $ ; IN: flag to indicate monotonically increasing data
          missing_value=missing_value ; IN: missing value 

if not keyword_set(xvar) then xvar = 0

common plot_hist_com, ymin,ymax

parse_variable_file, ips, datafile, titles, df 
xl = df[xvar,*]
xr = df[xvar+1,*]
x = 0.5*xl+0.5*xr
x[0] = xl[0]
nx = n_elements(x)
x[nx-1] = xr[nx-1]

if keyword_set(mono) then ips.xrange=[x[0],x[nx-1]]

nvars = n_elements(titles)
nyvar = nvars-2

if not keyword_set(vars) then vars = 2+ indgen(nyvar)

nplot = n_elements(vars)
if (ips.yrange[0] eq ips.yrange[1])  then begin
    ymin = min(df[vars[0],*],/NAN)
    ymax = max(df[vars[0],*],/NAN)
    if (nplot gt 1) then begin
        for i=1,nplot-1 do begin
            ymin = min([ymin,min(df[vars[i],*],/NAN)],/NAN)
            ymax = max([ymax,max(df[vars[i],*],/NAN)],/NAN)
        end
    end

    range = ymax-ymin

   ips.yrange=[ymin-range/5.0,ymax+range/2.0]
;   print, ips.yrange
end

nplot = n_elements(vars)
if not keyword_set(colors) then begin
    colors = 10.0 + 230.0*findgen(nplot)/(nplot-1.0+0.1)
    colors[0] = ips.fg[0]
end

if not keyword_set(fills) then  fills = colors

if not keyword_set(stripes) then begin
    stripes = colors
    stripes[*] = 0
end

if not keyword_set(lines) then begin 
    lines = intarr(nyvar)
    lines[*] = 0
end

if not keyword_set(xtitle) then xtitle=titles[xvar]
if not keyword_set(ytitle) then ytitle=titles[vars[0]]
if not keyword_set(title) then title=ips.mapdesc

plot, x, df[vars[0],*], $
  xlog=ips.xlog,ylog=ips.ylog,xrange=ips.xrange,yrange=ips.yrange, $
  xstyle=ips.xstyle, ystyle=ips.ystyle, $
  xtitle=xtitle, ytitle=ytitle, $
  title=title, xthick=ips.xthick, $
  ythick=ips.ythick, position=position,/nodata

if (ips.ylog eq 0) then begin
    ymin = !y.crange[0]
    ymax = !y.crange[1]
end else begin
    ymin = 10.0^!y.crange[0]
    ymax = 10.0^!y.crange[1]
end

for i=0,nplot-1 do begin
    for j=0,nx-1 do begin
        
        if df[vars[i],j] gt ymin then begin
            if fills[i] then begin
                if not stripes[i] then $
                  polyfill,[xl[j],xl[j],xr[j],xr[j]],$
                  [ymin,df[vars[i],j],df[vars[i],j],ymin], $
                  color=colors[i]
                if  stripes[i] then begin
                    polyfill,[xl[j],xl[j],xr[j],xr[j]],$
                      [ymin,df[vars[i],j],df[vars[i],j],ymin], $
                      color=colors[i],orient=40,spacing=0.25,thick=3*ips.thick
                end
            end
            plots,[xl[j],xl[j],xr[j],xr[j]], $
              [ymin,df[vars[i],j],df[vars[i],j],ymin], $
              color=colors[i],linestyle=lines[i],thick=ips.thick
        end
    end        ; for loop over j variables .. the data point for a var
end                  ; for loop over i variables .. the different vars

if nplot gt 1 then begin
    if (not ips.nolegend) then begin
        items = strarr(nyvar)
        items = titles[vars[0:nplot-1]]
        
        legend,items, $
          linestyle=lines[0:nplot-1],colors=colors[0:nplot-1], $
          thick=ips.thick
        
    end                       ; if not ips.nologend (ie., draw legend)
end                             ; if nvars > 1

return
end

;
; oplot_hist
;

pro oplot_hist,                $
          ips,                 $ ; IN: common isoc plotting structure
          datafile,            $ ; IN: name of the data file
          xvar=xvar,           $ ; IN: x-var to be plotted
          vars=vars,           $ ; IN: array of y-vars to be plotted
          lines=lines,         $ ; IN: linestyles to be used
          colors=colors,       $ ; IN: colors for linestyles
          fills=fills,         $ ; IN: array of vars to be filled                   
          stripes=stripes,     $ ; IN: set to 1 if you want striping in the fill
          labels=labels,       $ ; IN: label names                      
          missing_value=missing_value ; IN: missing value 

common plot_hist_com, ymin,ymax

if not keyword_set(xvar) then xvar = 0

parse_variable_file, ips, datafile, titles, df 
xl = df[xvar,*]
xr = df[xvar+1,*]
x = 0.5*xl+0.5*xr
x[0] = xl[0]
nx = n_elements(x)
x[nx-1] = xr[nx-1]

nvars = n_elements(titles)
nyvar = nvars-1

if not keyword_set(vars) then vars = 1+ indgen(nyvar)

nplot = n_elements(vars)
if not keyword_set(colors) then begin
    colors = 10.0 + 230.0*findgen(nplot)/(nplot-1.0+0.1)
    colors[0] = ips.fg[0]
end

if not keyword_set(lines) then begin 
    lines = intarr(nyvar)
    lines[*] = 0
end

if not keyword_set(stripes) then begin
    stripes = colors
    stripes[*] = 0
end


for i=0,nplot-1 do begin
    for j=0,nx-1 do begin
        if df[vars[i],j] gt ymin then begin
            if fills[i] then begin
                if not stripes[i] then begin
                    polyfill,[xl[j],xl[j],xr[j],xr[j]],$
                      [ymin,df[vars[i],j],df[vars[i],j],ymin], $
                      color=colors[i]
                end
                if  stripes[i] then begin
                    polyfill,[xl[j],xl[j],xr[j],xr[j]],$
                      [ymin,df[vars[i],j],df[vars[i],j],ymin], $
                      color=colors[i],orient=40,spacing=0.25,thick=3*ips.thick
                end
            end
            plots,[xl[j],xl[j],xr[j],xr[j]], $
              [ymin,df[vars[i],j],df[vars[i],j],ymin], $
              color=colors[i],linestyle=lines[i],thick=ips.thick
        end
    end        ; for loop over j variables .. the data point for a var
end                  ; for loop over i variables .. the different vars


if (not ips.nolegend) then begin
    items = strarr(nyvar)
    if not keyword_set(labels) then $
      items = titles[vars[0:nplot-1]] $
    else $
      items = labels
    
    legend,items, $
      linestyle=lines[0:nplot-1],colors=colors[0:nplot-1], $
      thick=ips.thick
    
end                           ; if not ips.nologend (ie., draw legend)

return
end
