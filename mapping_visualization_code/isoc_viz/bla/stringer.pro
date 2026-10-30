;===============================
;Cool program for finding strings

function stringer, $ 
           number, $; IN number (int, long, double)
           digit    ; the number of digits in the string
                    ; returns the appropriate string (truncated!)

;Number=Ulong(Number)
N=fltarr(15)
NumStr=strarr(15)
for i=0.0,digit-1 do begin
    numplace=number/10.0^(digit-1-i)
    num=numplace mod 10
    N[i]=fix(num)
end
for i=0,digit-1 do begin
    if N[i] eq 0 then NumStr[i] = '0'
    if N[i] eq 1 then NumStr[i] = '1'
    if N[i] eq 2 then NumStr[i] = '2'
    if N[i] eq 3 then NumStr[i] = '3'
    if N[i] eq 4 then NumStr[i] = '4'
    if N[i] eq 5 then NumStr[i] = '5'
    if N[i] eq 6 then NumStr[i] = '6'
    if N[i] eq 7 then NumStr[i] = '7'
    if N[i] eq 8 then NumStr[i] = '8'
    if N[i] eq 9 then NumStr[i] = '9'
    if N[i] lt 0 then numstr[i] = '*'
    if N[i] ge 10 then NumStr[i] = '!'
end
Nstring=NumStr[0]+NumStr[1]+NumStr[2]+NumStr[3]+NumStr[4]+NumStr[5]+NumStr[6]+NumStr[7]+NumStr[8]+NumStr[9]+NumStr[10]+NumStr[11]+NumStr[12]+NumStr[13]+NumStr[14]
return,Nstring
end

