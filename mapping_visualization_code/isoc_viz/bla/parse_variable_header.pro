;
; $Id: parse_variable_header.pro 2922 2008-09-26 01:47:01Z nathanISOC $
;
; pro parse_variable_header
; pro get_variable_header_size
;
; This procedure parses a header for a file of variable length
; where the file columns refer to variable titles, etc.
; The header is multiline, looking something like this:
;
;	# 15:0x25...
;	#  ...
;	#  title0='plot label for variable 0'
;	#  title1='plot label for variable 1'
;	#  ...
;	#  title24='plot label for variable 24 since there are 25'
;	#  desc='some title for the plot, perhaps'
;	#  ...
;
; E.g. 15 is the number of #-lines in the header, followed by rows with
; 25 columns.  The ... refers to other things on the line that IDL doesn't
; yet know or care about but which may eventually be placed within its ken.
;
; The (input) string array of header lines is flattened so that we don't
; have to worry about which line is which.  You should check that your
; data isn't transposed, however, as that can be especially painful.
;
; Cf get_me_bin_header_size()
;
pro get_variable_header_size,    $
	file,                    $ ; IN: data file
	lines,                   $ ; OUT: number of lines in header
	vars                       ; OUT: number of variables

	compile_opt HIDDEN, STRICTARR

	first='========================================================='
	openr,unit,file,/get_lun
	readu,unit,first
	close,unit
	lines=stregex(first,'[0-9]+',/extract)
	parts=strsplit(first,':',/extract)
	dims=strsplit(parts[1],'x',/extract)
	; dims[0] might be 0, but we don't care
	vars=dims[1]
end

;
; Cf parse_me_bin_header()
;
pro parse_variable_header,       $
	file_header,             $ ; IN: header lines
	lines,                   $ ; OUT: number of header lines
	vars,                    $ ; OUT: number of variables
	answer,                  $ ; OUT: array of titleN values
	desc,                    $ ; OUT: description header item
	title=title                ; IN: name of numbered header variables

	compile_opt HIDDEN, STRICTARR

	if (not keyword_set(title)) then title='title'

	; file_header is originally multi-line
	all_hdr = strjoin(file_header, ' ')
	answer = strarr(vars)

	; grab the N items
	for n=0,vars-1 do begin
            if (n lt 10) then fermat='(I1)' $
            else if (n lt 100) then fermat='(I2)' $
            else fermat='(I3)'
	    peerage = title + string(n,/print,format=fermat)
	    answer[n] = eval_var_eq_value_pair(all_hdr,peerage)
	endfor

	; grab the description
	desc      = eval_var_eq_value_pair(all_hdr,'desc')
end

;
; This parses into a dblarr julday data
;
function parse_dbl_columns,      $
        nrows,                   $ ; IN: the number of rows of data
	cols,                    $ ; IN: columns with the dblarr
	datafile                   ; IN: data file
	                           ; RETURNS: data array

        ndbl_vars = n_elements(cols)
        dcol = dblarr(ndbl_vars,nrows)
	get_variable_header_size,datafile,ds,nvars

    ; skip header
        a = 'a'
        openr,unit,datafile,/get_lun
        for i=0,ds-1 do begin
            readf,unit,a
         ;   print,a
        end
        
    ; read dbl data
        arr = dblarr(nvars)
        for i=0l,nrows-1 do begin
            readf,unit,arr
            dcol[*,i]=arr[cols[*]]
        end

        close, unit 
        
        return, dcol
end

;
; Cf. make_me_bin_plot -- this is the first part that reads the file
;
pro parse_variable_file,         $
	ips,                     $  ; IN : common isoc plotting structure
	datafile,                $  ; IN : data file
        titles,                  $  ; OUT: variable plot titles
	df,                      $  ; OUT: data array
        dcols=dcols,             $  ; IN : columns for which data is dbl format
        vdbl=vdbl,               $  ; OUT: double data columns 
        missing_value=missing_value ; IN : keyword equal to a value used for
                                    ;      missing values
 
	if (not keyword_set(title)) then title='title'

	get_variable_header_size,datafile,ds,nvars
	data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds, $
                       missing_value=missing_value)
	df=read_ascii_data_array(datafile,' ',ds,data)
	; so df is now an Nx(nvars) data array
	parse_variable_header,hdr,ds,nvars,titles,desc,title=title

	ips.mapdesc = desc
        
        if keyword_set(dcols) then begin
            nrows = n_elements(df[0,*])
            vdbl = parse_dbl_columns(nrows,(dcols[*]-1),datafile)
        end
end


;
; eof
;
