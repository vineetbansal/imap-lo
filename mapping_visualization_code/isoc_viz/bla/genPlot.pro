;
; $Id: genPlot.pro 1376 2008-03-24 20:32:37Z gbc $
;
; general plotting procedures for data files.  K. Goodrich
;
; .run genPlot.pro
; plotter, 2,'~gbc/IBEX/work/work-flat-e2e/flat_e2e.raw', 7, 'Title'
;

function reader, filename, ndim1
close, 1
out = fltarr(ndim1, 10000)
arr = fltarr(ndim1)
openr, 1, filename
i = 0
while not eof(1) do begin
    readf, 1, arr
    out[*,i] = arr
    i = i +1
end 
out = reform(out[*,0:i-1])
return, out
end


pro plotter, grphnum, file, colnum, Title
;============================================================================
;inputs: 
;       number of graphs you would like to produce,
;       name of file you would like to graph
;       number of columns in the data file 
;       Title of the graph file
;
;outputs:
;       2 dimensional graph in .eps form that displays as much data as
;       you'd like
;============================================================================

Xtitle = '' & Ytitle=''
Sub = ''

var = reader(file, colnum)

;file = '' & Sub= ''
;read, Title, prompt = 'Title?  '
;read, file, prompt ='Enter file to be plotted:  '
;read, colnum, prompt = 'Enter how many columns in data file:  '


read, Sub, prompt = 'Title of Data: '


read, x1, prompt = 'Which column is the x-axis?  '
read, Xtitle, prompt ='X title?  '

read, y1, prompt = 'Which column is the y-axis?  '
read, Ytitle, prompt = 'Y title?  '

x1 -= 1 & y1 -= 1

max_x = max(var[x1,*]) & min_x = min(var[x1,*])
max_y = max(var[y1,*]) & min_y = min(var[y1,*])

print, max_x
print, min_x
print, max_y
print, min_y

set_plot, 'ps'
device, file = Title + '.eps', /encaps, /color
loadct, 39

PLOT, var[x1, *], var[y1, *], /NOERASE, TIT = Title, XTIT = Xtitle, YTIT = Ytitle,XRA = [min_x, max_x], YRA = [min_y - 30, max_y + 30], background = 255, color = 0, xstyle = 1, ystyle = 1
oplot, var[x1,*], var[y1,*], color = 0, psym = 7


xyouts, min_x+5, min_y - 20, Sub, color = 0 


if grphnum gt 1 then begin
    for i = 0, grphnum -2 do begin
        read, file, prompt ='Enter file to be plotted:       '

; put in here in case someone wants to graph two forms of data from
; different data files

        read, colnum, prompt = 'Enter how many columns in data file:  '
        read, Sub, prompt ='Label of Graph: '
                 

        var = reader(file, colnum)
                 
        read, x1, prompt = 'Which column is the x-axis?  '
        read, y1, prompt = 'Which column is the y-axis?  '
        read, col, prompt = 'color (1 - 255)?  '
        
        x1 -= 1 & y1 -= 1

        max_x = max(var[x1,*]) & min_x = min(var[x1,*])
        max_y = max(var[y1,*]) & min_y = min(var[y1,*])

        oplot, var[x1,*], var[y1,*], color = col
        oplot, var[x1,*], var[y1,*], color = col, psym = 7
        
        xyouts, min_x + (10*(i+2)), min_y - 20, Sub, color = col
        
    endfor
endif  
device, /close
end
