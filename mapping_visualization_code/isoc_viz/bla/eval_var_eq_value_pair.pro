;
; $Id: eval_var_eq_value_pair.pro 5186 2009-08-05 19:40:13Z gbc $
;
; function eval_var_eq_value_pair_nquote
; function eval_var_eq_value_pair_double
; function eval_var_eq_value_pair_single
; function eval_var_eq_value_pair
;
; These procedures parse a string, essentially looking for 
; something=somevalue or something=?somevalue? where ? is
; a ' or a " or ...
; assuming #'s or spaces and tabs separate several such items.
;
; If nothing is found, a '' string is returned.
;
; There is probably a smarter way to do this.
;

;
; This version assumes no quotes.
;
function eval_var_eq_value_pair_nquote,vareq,match
	local='[ #	]' + match + '=[^= #	]+'
	; match preceded by space,tab,#
	; followed by anything but =,space,#,tab
	sss=stregex(vareq, local, /extract)
	if (sss eq '') then return,''
	iii=strpos(sss,'=')+1
	return,strmid(sss,iii)
end

;
; This version looks for "
;
function eval_var_eq_value_pair_double,vareq,match
	local='[ #	]' + match + '="[^="]+"'
	; match preceded by space,tab,#
	; followed by anything but =,#,"
	pos=stregex(vareq, local, length=len)
	if (pos lt 0) then return,''
	mln=strlen(match)
	return,strmid(vareq,pos+mln+3,len-mln-4)
end

;
; This version looks for '
;
function eval_var_eq_value_pair_single,vareq,match
	local='[ #	]' + match + "='[^=']+'"
	; match preceded by space,tab,#
	; followed by anything but =,#,'
	pos=stregex(vareq, local, length=len)
	if (pos lt 0) then return,''
	mln=strlen(match)
	return,strmid(vareq,pos+mln+3,len-mln-4)
end

;
; This procedure parses a string, essentially looking for 
; something=somevalue assuming #'s or spaces and tabs separate
; several such items.  If nothing is found, a '' string is returned.
;
; We precede the var=value by a space to make the regex easier.
;
; This would be a simple eval in a shell.
;
function eval_var_eq_value_pair,vareq,match
	try=eval_var_eq_value_pair_double(' ' + vareq,match)
	if ( try ne '' ) then return,try

	try=eval_var_eq_value_pair_single(' ' + vareq,match)
	if ( try ne '' ) then return,try

	try=eval_var_eq_value_pair_nquote(' ' + vareq,match)
	return,try
end

;
; eof
;
